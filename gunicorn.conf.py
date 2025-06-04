# Gunicorn configuration for improved startup and health checks
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 1  # Start with single worker for faster startup
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers proactively
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'accellis_app'

# Server mechanics
preload_app = True  # Preload application for faster worker spawning
enable_stdio_inheritance = True

# SSL (if needed)
# keyfile = None
# certfile = None

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)