"""Bootstraps the Flask Application."""

import argparse
import os
import logging.config

from flask import Flask

from tf_serving_flask_app import settings
from tf_serving_flask_app.base.utils import as_boolean
from tf_serving_flask_app.rest.api import create_prediction_api_from_spec
from tf_serving_flask_app.core import spec_borg
from tf_serving_flask_app.core import metrics


def create_app():
    """Creates and configures attributes and APIs on the Flask app."""
    app = Flask(__name__)
    app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP
    return app


def bootstrap_spec(pipeline_spec_path):
    """Bootstraps the specs once on initialization."""
    borg = spec_borg.SpecBorg()
    borg.initialize_from_json(pipeline_spec_path)


def register_metrics():
    """Exposes Prometheus metrics as a separate flask application on a different
    thread. This ensures that worker processes are used only for prediction requests
    and frequently scraping metrics does not result in a worker process not being available
    for serving.
    """
    metrics_host = os.getenv('METRICS_HOST', settings.DEFAULT_METRICS_HOST)
    metrics_port = int(os.getenv('METRICS_PORT', settings.DEFAULT_METRICS_PORT))
    # start_http_server allows exposing the endpoint on an independent Flask application
    # on a selected HTTP port.
    metrics.register_endpoint(metrics_port, metrics_host, endpoint='/metrics')


def bootstrap_app(pipeline_spec_path):
    """Creates the application, bootstraps the spec, and generates resources dependent on the spec."""
    app = create_app()
    bootstrap_spec(pipeline_spec_path)
    prediction_api = create_prediction_api_from_spec()
    prediction_api.init_app(app)
    return app


def main():
    """
    The Flask application when started stand-alone parses the spec as a
    command line argument and initializes the application through environment
    provided host and port values.

    The version of the logging configuration that is loaded depends on whether FLASK_ENV
    is "production" or "development".

    Explicitly setting a truthy value for FLASK_DEBUG will run the application in debug mode.

    Explicitly setting a truthy value for FLASK_PROFILE will attach a WSGI
    profiler middleware to the app.
    """
    dirname = os.path.split(__file__)[0]
    env = os.getenv('FLASK_ENV', settings.DEFAULT_FLASK_ENV)
    assert env in ('production', 'development')
    logging.config.fileConfig(os.path.join(dirname, '%s_logging.conf' % env))

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--spec', action='store',
                        help='Fully qualified path to the pipeline specification in JSON')
    args = parser.parse_args()

    app = bootstrap_app(args.spec)

    host = os.getenv('FLASK_SERVER_NAME', settings.DEFAULT_FLASK_SERVER_NAME)
    port = int(os.getenv('FLASK_SERVER_PORT', settings.DEFAULT_FLASK_SERVER_PORT))
    logger = logging.getLogger()
    logger.info('>>>>> Starting TensorFlow REST client at http://%s:%d/ >>>>>', host, port)
    register_metrics()
    flask_debug = as_boolean(os.getenv('FLASK_DEBUG', settings.DEFAULT_FLASK_DEBUG))

    flask_profile = as_boolean(os.getenv('FLASK_PROFILE', settings.DEFAULT_FLASK_PROFILE))
    if flask_profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
        flask_debug = True

    app.run(debug=flask_debug, host=host, port=port, threaded=True)


if __name__ == '__main__':
    main()
