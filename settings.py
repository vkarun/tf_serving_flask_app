# Flask settings
DEFAULT_FLASK_ENV = 'production'
DEFAULT_FLASK_SERVER_NAME = '0.0.0.0'
DEFAULT_FLASK_SERVER_PORT = 5001

# Debugger and profiler flags for
# the stand-alone Flask application.
DEFAULT_FLASK_DEBUG = False
DEFAULT_FLASK_PROFILE = False

# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False
RESTPLUS_ERROR_404_HELP = True

# Default TensorFlow serving backend.
DEFAULT_TF_SERVER_NAME = '0.0.0.0'
DEFAULT_TF_SERVER_PORT = 9000
DEFAULT_PREDICTION_RPC_TIMEOUT_SECS = 30

# Configuration for the Flask app running on a separate thread for metrics.
DEFAULT_METRICS_HOST = '0.0.0.0'
DEFAULT_METRICS_PORT = 5002

