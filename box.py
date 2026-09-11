# box.py - Firewall & Anti-DDoS Shield
# (C) MRX 2026

import time
import threading
from collections import defaultdict, deque
from flask import request, jsonify


class Shield:
    def __init__(self):
        self.lock = threading.Lock()
        self.requests = defaultdict(deque)
        self.blocks = {}
        self.strikes = defaultdict(int)

        self.RATE_LIMIT = 60
        self.RATE_WINDOW = 10
        self.BLOCK_TIME = 300
        self.MAX_STRIKES = 5
        self.BAD_PATHS = ('/admin', '/.env', '/wp-admin', '/phpmyadmin', '/.git')
        self.BAD_AGENTS = ('sqlmap', 'nikto', 'nmap', 'masscan', 'acunetix', 'hydra')

        threading.Thread(target=self._cleanup_loop, daemon=True).start()

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            now = time.time()
            with self.lock:
                expired = [ip for ip, t in self.blocks.items() if t < now]
                for ip in expired:
                    del self.blocks[ip]
                for ip in list(self.requests.keys()):
                    if not self.requests[ip]:
                        del self.requests[ip]

    def get_ip(self):
        return (
            request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            or request.headers.get('X-Real-IP')
            or request.remote_addr
            or 'unknown'
        )

    def check(self):
        ip = self.get_ip()
        ua = (request.headers.get('User-Agent') or '').lower()
        path = request.path.lower()
        now = time.time()

        with self.lock:
            if ip in self.blocks:
                if now < self.blocks[ip]:
                    return False
                else:
                    del self.blocks[ip]

            if any(bad in ua for bad in self.BAD_AGENTS):
                self.blocks[ip] = now + 86400
                return False

            if any(p in path for p in self.BAD_PATHS):
                self._strike(ip)
                return False

            dq = self.requests[ip]
            while dq and dq[0] < now - self.RATE_WINDOW:
                dq.popleft()

            if len(dq) >= self.RATE_LIMIT:
                self._strike(ip)
                return False

            dq.append(now)
        return True

    def _strike(self, ip):
        self.strikes[ip] += 1
        if self.strikes[ip] >= self.MAX_STRIKES:
            self.blocks[ip] = time.time() + self.BLOCK_TIME
        else:
            self.blocks[ip] = time.time() + 30


shield = Shield()


def protect(app):
    @app.before_request
    def _before():
        if request.path in ('/health',):
            return None
        if not shield.check():
            return jsonify({"error": "Access Denied"}), 403
        return None

    @app.after_request
    def _after(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(self)'
        return response

    return app
