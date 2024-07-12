FROM python:3.11 AS base

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PIP_QUIET 2
ENV PIP_USER 1
ENV UV_NO_CACHE 1
ENV PYTHONUSERBASE /djangoenv
ENV PATH="$PYTHONUSERBASE/bin:$PATH"

RUN mkdir /logs
VOLUME /logs

WORKDIR /django

RUN pip install pip==23.3.1
COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8300


FROM base as dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# to ensure all make commands are also working in docker dev setup we need to overwrite requirements.txt
COPY requirements-dev.txt requirements.txt
RUN uv pip sync requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8300"]


FROM base as prod

COPY . .

CMD ["rainbow-saddle", "--pid", "/var/run/django.pid", "--gunicorn-pidfile", "/var/run/gunicorn.pid", "gunicorn", "image.wsgi", "-c", "/django/gunicorn-conf.py"]
