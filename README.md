## TensorFlow Serving client hosted by Flask web framework

This directory contains a Flask web server that hosts the TensorFlow serving client.
It receives REST requests for predictions which are serialized as JSON.

## Running the Flask application locally

### The environment variable FLASK_ENV

Can be one of `production` or `development`. Works in conjunction
with the environment variable `FLASK_MODE`.

- `production` implies the use of structured JSON logs and `INFO` for
  most loggers with the assumption that this will be fed to ELK.

- `development` implies developer friendly line by line logging with
  verbosity set to `DEBUG`.

### The environment variable FLASK_MODE

Can be one of `multiprocess` or `multithreaded`.

- `multiprocess` and `FLASK_ENV` set to `production` implies we run
  gunicorn with a preconfigured number of worker processes with each
  worker process handling a request asynchronously with eventlet.

- `multithreaded` and `FLASK_ENV` set to `production` implies we run
  a single worker process with multiple threads and the application
  performing production logging.

- `multithreaded` and `FLASK_ENV` set to `development` implies we run
  a single worker process with multiple threads and the application
  performing developer friendly logging.

### Running the Flask application in development mode

The following command runs the Flask application in development mode: a
single multi-threaded worker process where each thread synchronously
serves a single prediction request.

```sh
FLASK_ENV=development ./tf_serving_flask_app/run.sh -s /tmp/models/inceptionv3.spec
```

### Debugging the Flask application in development mode

If you enable debug support the server will reload itself on changes
to source code rooted under `tf_serving_flask_app`.

```sh
FLASK_ENV=development FLASK_DEBUG=1 ./tf_serving_flask_app/run.sh -s /tmp/models/inceptionv3.spec
```

### Profiling the Flask application in development mode

```sh
FLASK_ENV=development FLASK_PROFILE=1 ./tf_serving_flask_app/run.sh -s /tmp/models/inceptionv3.spec
```

The screenshot below gives the overhead of the top 30 frames of a
prediction request.

![Sample prediction profile](https://user-images.githubusercontent.com/38099930/40659534-2f3b5ef0-636c-11e8-8a53-13cb648ddc86.png)

### Running the Flask application in production mode with gunicorn and eventlets

Please note that `FLASK_DEBUG` does not do anything while running in production mode.

```sh
FLASK_ENV=production ./tf_serving_flask_app/run.sh -s /tmp/models/inceptionv3.spec
```

### Profiling the Flask application in production

```sh
FLASK_ENV=production FLASK_PROFILE=1 ./tf_serving_flask_app/run.sh -s /tmp/models/inceptionv3.spec
```

### Running the Flask application in multithreaded mode and production logging

```sh
FLASK_ENV=production FLASK_MODE=multithreaded ./tf_serving_flask_app/run.sh -s /tmp/models/inceptionv3.spec
```

## Building the docker image of the Flask application

Please note that the docker build must be invoked from the root of
the grace git repository with the build context encapsulating both
the flask application and the source directory containing generated
spec protocol buffer files.

```sh
docker build -t <dockerhub-user>/tf-serving-rest-client -f tf_serving_flask_app/Dockerfile .
```

Deploy after building to dockerhub with:

```sh
docker login
```

```sh
docker push <dockerhub-user>/tf-serving-rest-client
```
