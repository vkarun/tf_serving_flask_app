import multiprocessing

from prometheus_client import multiprocess
from tf_serving_flask_app.app import register_metrics

# Registers multiprocess metrics.
register_metrics()

# http://docs.gunicorn.org/en/stable/settings.html#bind
bind = '0.0.0.0:5001'

# Maximum number of pending connections.
# http://docs.gunicorn.org/en/stable/settings.html#backlog
backlog = 2048

# The number of worker processes for handling requests.
# TODO(karun): Load test to determine ideal default.
workers = multiprocessing.cpu_count() * 4

# Asynchronous workers through eventlet http://eventlet.net/
worker_class = 'eventlet'

# The maximum number of simultaneous clients.
worker_connections = 1000

loglevel = 'info'


def pre_fork(server, worker):
    pass


def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")


# See https://github.com/prometheus/client_python#multiprocess-mode-gunicorn
def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
