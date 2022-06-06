FROM python:3.6

MAINTAINER Venkat Karun <karun@gmail.com>

RUN apt-get update -y
RUN apt-get install -y build-essential

COPY ./tf_serving_flask_app/requirements.txt /app/tf_serving_flask_app/
WORKDIR /app/tf_serving_flask_app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY ./tf_serving_flask_app /app/tf_serving_flask_app
COPY ./spec /app/spec

ENV PYTHONPATH=/app
ENTRYPOINT ["./run.sh"]
