import cProfile
import pstats
from io import StringIO
import logging
import os
import time


PSTATS_FUNCTION_LIMIT = int(os.environ.get("FLASK_PSTATS_FUNCTION_LIMIT", 30))

print("""
# ** USAGE:
$ FLASK_PSTATS_FUNCTION_LIMIT=100 gunicorn -c ./tf_serving_flask_app/gunicorn_profiler_config.py ...
""")

bind = '0.0.0.0:5001'

worker_class = 'eventlet'


def profiler_enable(worker, req):
    worker.profile = cProfile.Profile()
    worker.profile.enable()
    worker.log.info("PROFILING %d: %s" % (worker.pid, req.uri))


def profiler_summary(worker, req):
    s = StringIO()
    worker.profile.disable()
    ps = pstats.Stats(worker.profile, stream=s).sort_stats('time', 'cumulative')
    ps.print_stats(PSTATS_FUNCTION_LIMIT)

    logging.error("\n[%d] [INFO] [%s] URI %s" % (worker.pid, req.method, req.uri))
    logging.error("[%d] [INFO] %s" % (worker.pid, s.getvalue()))


def pre_request(worker, req):
    worker.start_time = time.time()
    profiler_enable(worker, req)


def post_request(worker, req):
    total_time = time.time() - worker.start_time
    logging.error("\n[%d] [INFO] [%s] Load Time: %.3fs\n" % (
        worker.pid, req.method, total_time))
    profiler_summary(worker, req)
