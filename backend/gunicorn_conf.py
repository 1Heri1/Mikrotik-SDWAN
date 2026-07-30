bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"

# Pinned to a single worker: the in-process APScheduler and the in-memory
# rate limiter (app/core/rate_limit.py) are both process-local singletons.
# Running more than one worker would poll the router multiple times per
# interval and split the login rate-limit counters across processes.
workers = 1

accesslog = "-"
errorlog = "-"
loglevel = "info"
timeout = 60
graceful_timeout = 30
