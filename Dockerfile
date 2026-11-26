# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATABASE=/data/jobboard.db UPLOAD_FOLDER=/data/cvs
WORKDIR /srv
COPY requirements.txt .
RUN --mount=type=bind,from=builder,source=/wheels,target=/wheels \
    pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && groupadd -g 10001 app && useradd -u 10001 -g app -s /usr/sbin/nologin app \
    && mkdir -p /data/cvs && chown -R app:app /data

FROM runtime AS lab
COPY --chown=app:app app ./app
COPY --chown=app:app scripts/__init__.py scripts/start_vulnerable.py ./scripts/
USER 10001:10001
EXPOSE 8001
ENTRYPOINT ["python", "-m", "scripts.start_vulnerable", "--docker"]

FROM runtime AS reference
COPY --chown=app:app app ./app
COPY --chown=app:app scripts/entrypoint.sh /srv/entrypoint.sh
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["/bin/sh","/srv/entrypoint.sh"]
