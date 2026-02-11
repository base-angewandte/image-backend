FROM python:3.12 AS base

ENV TZ="Europe/Vienna"

ENV PYTHONUNBUFFERED=1
ENV UV_NO_CACHE=1
ENV UV_SYSTEM_PYTHON=1
ENV UV_COMPILE_BYTECODE=1

RUN mkdir /logs
VOLUME /logs

WORKDIR /django

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt .
RUN uv pip sync requirements.txt

EXPOSE 8300


FROM base AS dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# to ensure all make commands are also working in docker dev setup we need to overwrite requirements.txt
COPY requirements-dev.txt requirements.txt
RUN uv pip sync requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8300"]


FROM base AS prod

COPY . .

CMD ["rainbow-saddle", "--pid", "/var/run/django.pid", "--gunicorn-pidfile", "/var/run/gunicorn.pid", "gunicorn", "image.wsgi", "-c", "/django/gunicorn_conf.py"]
