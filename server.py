# server.py - Optimized Gunicorn Server
# (C) MRX 2026

import os
import multiprocessing
from gunicorn.app.base import BaseApplication
from app import app


def workers_count():
    try:
        return multiprocessing.cpu_count() * 2 + 1
    except Exception:
        return 4


class GunicornApp(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


options = {
    'bind': f"0.0.0.0:{os.environ.get('PORT', 5000)}",
    'workers': workers_count(),
    'worker_class': 'gthread',
    'threads': 8,
    'timeout': 60,
    'keepalive': 5,
    'max_requests': 2000,
    'max_requests_jitter': 500,
    'accesslog': '-',
    'errorlog': '-',
    'loglevel': 'warning',
    'preload_app': True,
}


if __name__ == '__main__':
    print(f"🚀 Starting MRX GPT on {options['bind']}")
    print(f"⚙️ Workers: {options['workers']} | Threads: {options['threads']}")
    GunicornApp(app, options).run()
