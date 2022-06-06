#!/bin/bash

DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)

usage() { echo "Usage: $0 [-s <path to pipeline specification> -a <optional assets dir> ]" 1>&2; exit 1; }

while getopts ":s:a:" i; do
    case "${i}" in
        s)
            s=${OPTARG%/}
            ;;
        a)
            a=${OPTARG%/}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${s}" ]; then
    usage
fi

# Assign defaults if unspecified for critical environment variables.
: "${FLASK_ENV:=production}"
: "${FLASK_MODE:=multiprocess}"

if [ "$FLASK_ENV" == "production" ] || [ "$FLASK_ENV" == "development" ]; then
  echo "Running the Flask application in the '$FLASK_ENV' environment"
else
  echo "Bad value for environment '$FLASK_ENV'. Should be one of 'production' or 'development'."
  exit 1
fi

if [ "$FLASK_MODE" == "multiprocess" ] || [ "$FLASK_MODE" == "multithreaded" ]; then
  echo "Running the Flask application in the '$FLASK_MODE' mode"
else
  echo "Bad value for mode '$FLASK_MODE'. Should be one of 'multiprocess' or 'multithreaded'."
  exit 1
fi

cd $DIR/..

# In production, FLASK_TMP_DIR should be set to a `tmpfs` mount.
#
# The gunicorn heartbeat system involves calling os.fchmod on temporary file handlers
# and may block a worker for arbitrary time if the directory is on a disk-backed
# filesystem. For example, by default /tmp is not mounted as tmpfs in Ubuntu; in AWS
# an EBS root instance volume may sometimes hang for half a minute and during this
# time Gunicorn workers may completely block in os.fchmod.
: "${FLASK_TMP_DIR:=/tmp}"

if [ ! -d ${FLASK_TMP_DIR} ] || [ ! -w ${FLASK_TMP_DIR} ]; then
    msg="Invalid temporary directory '$FLASK_TMP_DIR' specified."
    msg="$msg The directory needs to exist and be writable."
    echo "$msg"
    exit 1
fi

set -e -x

# We run prometheus exports in a multiprocess mode even if we
# are only starting a single process.
multiproc_tmp_dir=${FLASK_TMP_DIR}/multiproc-tmp

rm -rf ${multiproc_tmp_dir}
mkdir -p ${multiproc_tmp_dir}
export prometheus_multiproc_dir=${multiproc_tmp_dir}

if [ "$FLASK_ENV" == "production" ] && [ "$FLASK_MODE" == "multiprocess" ]; then
    GUNICORN_CONFIG=${DIR}/gunicorn_config.py
    if [[ "$FLASK_PROFILE" =~ ^(y|yes|t|true|on|1)$ ]]; then
        GUNICORN_CONFIG=${DIR}/gunicorn_profiler_config.py
    fi
    gunicorn -c ${GUNICORN_CONFIG} \
    --worker-tmp-dir ${FLASK_TMP_DIR} \
    --no-sendfile \
    --log-config ${DIR}/production_logging.conf \
    "tf_serving_flask_app.wsgi:app(spec='${s}')"
else
    python ${DIR}/app.py --spec=${s}
fi
