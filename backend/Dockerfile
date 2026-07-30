FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini gunicorn_conf.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /var/log/mikrotik-monitor \
    && chown -R appuser:appuser /app /var/log/mikrotik-monitor
USER appuser

ENV LOG_DIR=/var/log/mikrotik-monitor
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
