import inspect
import functools
import threading
from timeit import default_timer

from flask import Flask
from werkzeug.serving import is_running_from_reloader
from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_client import multiprocess
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY as DEFAULT_REGISTRY


def register_endpoint(port, host='0.0.0.0', endpoint='/metrics'):
    """Exposes Prometheus metrics as a separate flask application
    on a different thread. This ensures that worker processes are
    used only for prediction requests and frequently scraping metrics
    does not result in a worker process not being available for serving.

    :param port: the HTTP port to expose the metrics endpoint on
    :param host: the HTTP host to listen on (default: `0.0.0.0`)
    :param endpoint: the URL path to expose the endpoint on
        (default: `/metrics`)
    """
    if is_running_from_reloader():
        return

    app = Flask('prometheus-metrics-exporter-%d' % port)

    @app.route(endpoint)
    def prometheus_metrics():
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        headers = {'Content-Type': CONTENT_TYPE_LATEST}
        return generate_latest(registry), 200, headers

    def run_app():
        # Since we run in a separate thread, we turn off debugging and
        # the use of the reloader explicitly. The reloader expects the
        # Flask application to run in the main thread and the metric
        # app dies with a `ValueError: signal only works in main thread`
        # if started with the reloader.
        app.run(host=host, port=port, debug=False, use_reloader=False)

    thread = threading.Thread(target=run_app)
    thread.setDaemon(True)
    thread.start()


def histogram(name, description, labels=None, **kwargs):
    """
    Use a Histogram to track the execution time and invocation count
    of the method.
    :param name: the name of the metric
    :param description: the description of the metric
    :param labels: a dictionary of `{labelname: callable_or_value}` for labels
    :param kwargs: additional keyword arguments for creating the Histogram
    """

    return _track(
        Histogram,
        lambda metric, time: metric.observe(time),
        kwargs, name, description, labels,
        registry=DEFAULT_REGISTRY
    )


def summary(name, description, labels=None, **kwargs):
    """
    Use a Summary to track the execution time and invocation count
    of the method.
    :param name: the name of the metric
    :param description: the description of the metric
    :param labels: a dictionary of `{labelname: callable_or_value}` for labels
    :param kwargs: additional keyword arguments for creating the Summary
    """

    return _track(
        Summary,
        lambda metric, time: metric.observe(time),
        kwargs, name, description, labels,
        registry=DEFAULT_REGISTRY
    )


def gauge(name, description, labels=None, **kwargs):
    """
    Use a Gauge to track the number of invocations in progress
    for the method.
    :param name: the name of the metric
    :param description: the description of the metric
    :param labels: a dictionary of `{labelname: callable_or_value}` for labels
    :param kwargs: additional keyword arguments for creating the Gauge
    """

    return _track(
        Gauge,
        lambda metric, time: metric.dec(),
        kwargs, name, description, labels,
        registry=DEFAULT_REGISTRY,
        before=lambda metric: metric.inc()
    )


def counter(name, description, labels=None, **kwargs):
    """
    Use a Counter to track the total number of invocations of the method.
    :param name: the name of the metric
    :param description: the description of the metric
    :param labels: a dictionary of `{labelname: callable_or_value}` for labels
    :param kwargs: additional keyword arguments for creating the Counter
    """

    return _track(
        Counter,
        lambda metric, time: metric.inc(),
        kwargs, name, description, labels,
        registry=DEFAULT_REGISTRY
    )


def _track(metric_type, metric_call, metric_kwargs, name, description, labels,
           registry, before=None):
    """
    Internal method decorator logic.
    :param metric_type: the type of the metric from the `prometheus_client` library
    :param metric_call: the invocation to execute as a callable with `(metric, time)`
    :param metric_kwargs: additional keyword arguments for creating the metric
    :param name: the name of the metric
    :param description: the description of the metric
    :param labels: a dictionary of `{labelname: callable_or_value}` for labels
    :param registry: the Prometheus Registry to use
    :param before: an optional callable to invoke before executing the
        request handler method accepting the single `metric` argument
    """

    if labels is not None and not isinstance(labels, dict):
        raise TypeError('labels needs to be a dictionary of {labelname: callable}')

    label_names = labels.keys() if labels else tuple()
    parent_metric = metric_type(
        name, description, labelnames=label_names, registry=registry,
        **metric_kwargs
    )

    def label_value(f):
        if not callable(f):
            return lambda x: f
        if inspect.getargspec(f).args:
            return lambda x: f(x)
        else:
            return lambda x: f()

    label_generator = tuple(
        (key, label_value(call))
        for key, call in labels.items()
    ) if labels else tuple()

    def get_metric(response):
        if label_names:
            return parent_metric.labels(
                **{key: call(response) for key, call in label_generator}
            )
        else:
            return parent_metric

    def decorator(f):
        @functools.wraps(f)
        def func(*args, **kwargs):
            if before:
                metric = get_metric(None)
                before(metric)

            else:
                metric = None

            start_time = default_timer()
            response = f(*args, **kwargs)
            total_time = max(default_timer() - start_time, 0)

            if not metric:
                metric = get_metric(response)

            metric_call(metric, time=total_time)
            return response

        return func

    return decorator

