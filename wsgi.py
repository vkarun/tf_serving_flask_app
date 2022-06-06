from tf_serving_flask_app.app import bootstrap_app


def app(spec):
    """gunicorn wsgi entry point.

    The path to the pipeline specification is passed as a
    key value pair as seen in the sample invocation below:

    gunicorn [options] "tf_serving_flask_app.wsgi:app(spec=<path to spec>)"

    Important behavior note:

    The Flask application -- when started stand-alone without gunicorn
    -- parses the spec as a command line argument and initializes the
    application through environment provided host and port values.

    With gunicorn, port bindings and all other configuration is
    specified through a more nuanced DSL. Exporting FLASK_DEBUG
    while in gunicorn is not going to work as expected and developers
    should run the standalone mode whenever debugging is required.
    """
    return bootstrap_app(spec)
