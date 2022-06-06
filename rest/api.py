"""
Dynamically assembles a Flask-RestPlus API from the pipeline specification.
"""

import json
import logging

from flask import request, Response
from flask_restplus import Api, Resource
from werkzeug.datastructures import FileStorage

from spec.proto.input_pb2 import Input
from tf_serving_flask_app.base.encoders import NumpyEncoder
from tf_serving_flask_app.core import metrics
from tf_serving_flask_app.core.prediction_flow import create_prediction_flow
from tf_serving_flask_app.core.spec_borg import SpecBorg

logger = logging.getLogger('rest')


def create_prediction_api_from_spec(route='/predict'):
    """Dynamically generates a Flask-RestPlus resource from the given specification.

    :param route: The route on which the resource has to be installed.
    :return: a flask_restplus.Api object.
    """
    spec_borg = SpecBorg()

    model_spec = spec_borg.model_spec
    model_name = model_spec.name
    model_version = model_spec.version
    api = Api(version=model_version,
              title='%s REST API' % model_name,
              description='RESTful API for predictions with the model %s' % model_name,
              doc='/')

    request_parser = api.parser()
    for (input_key, input_spec) in spec_borg.input_specs.items():
        if input_spec.type == Input.IMAGE or input_spec.type == Input.FILE:
            request_parser.add_argument(input_key,
                                        location='files',
                                        type=FileStorage,
                                        required=True)
        if input_spec.type == Input.TEXT:
            request_parser.add_argument(input_key,
                                        location='form',
                                        type=str,
                                        required=True)

    @api.route(route)
    class Prediction(Resource):
        @api.doc(description='Make a prediction with the model %s' % model_name,
                 responses={
                     200: 'Success',
                     400: 'Bad request',
                     500: 'Internal server error'
                 })
        @api.expect(request_parser)
        @metrics.counter(
            'prediction_request_total',
            'Total number of prediction requests',
            labels={
                'method': lambda: request.method,
                'status': lambda r: r.status_code,
            },
        )
        @metrics.histogram(
            'prediction_request_duration_seconds',
            'Prediction request duration in seconds',
            labels={
                'method': lambda: request.method,
                'status': lambda r: r.status_code,
                'path': lambda: request.path
            },
        )
        def post(self):
            try:
                prediction_flow_input = {}
                for (input_key, input_spec) in spec_borg.input_specs.items():
                    if input_spec.type == Input.IMAGE or input_spec.type == Input.FILE:
                        prediction_flow_input[input_key] = request.files[input_key]

                    if input_spec.type == Input.TEXT:
                        prediction_flow_input[input_key] = request.form[input_key]
            except KeyError as e:
                logger.exception(e)
                errmsg = 'Inputs not conformant with signature and type specified in the spec: %s' % e
                return Response(errmsg, status=400)

            try:
                prediction_flow = create_prediction_flow()
                results = prediction_flow(prediction_flow_input)
                results_json = json.dumps(results, cls=NumpyEncoder)
                return Response(results_json, status=200, mimetype='application/json')
            except Exception as e:
                logger.exception(e)
                errmsg = 'Failed to make a prediction with `%s`: %s' % (type(e).__name__, e)
                return Response(errmsg, status=500)

    return api


