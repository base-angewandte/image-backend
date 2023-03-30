FROM python:3.8
ENV PYTHONUNBUFFERED 1

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

WORKDIR /docs
VOLUME /docs
