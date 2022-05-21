import io
import time
import datetime
import socket
import threading
import logging
from .metrics import Counter, Gauge, Series


logger = logging.getLogger(__name__)


class Pyrite:
    DEBT_MAX_SIZE = 100_000

    def __init__(self, host, port, interval=60, timeout=10, prefix=''):
        self.host = host
        self.port = port
        self.interval = interval
        self.timeout = timeout
        self.prefix = prefix
        self.metrics = {}
        self.metrics_lock = threading.Lock()
        self.sender_shutdown = threading.Event()
        self.sender = threading.Thread(target=self.send, daemon=True)
        self.sender.start()

    def __del__(self):
        self.close()

    def counter(self, name):
        return self.metric(name, Counter)

    def gauge(self, name, value):
        return self.metric(name, lambda n: Gauge(n, value))

    def series(self, name):
        return self.metric(name, Series)

    def close(self):
        self.sender_shutdown.set()
        self.sender.join()

    def metric(self, name, clazz):
        with self.metrics_lock:
            if name not in self.metrics:
                m = clazz(name)
                self.metrics[name] = m
                return m
            else:
                return self.metrics[name]

    def send(self):
        debt = []
        last_time = time.time()

        while True:
            next_time = last_time + self.interval
            self.sender_shutdown.wait(next_time - time.time())
            last_time = next_time

            with self.metrics_lock:
                t = int(time.time())
                sn = debt
                for m in self.metrics.values():
                    for s in m.snapshot():
                        sn.append((s[0], s[1], t))

            try:
                hp = (self.host, self.port)
                with socket.create_connection(hp, self.timeout) as s:
                    s.sendall(self.serialize(sn).encode())
                debt = []
            except Exception as e:
                logger.warn('Failed to send metrics: %s', e)
                debt = sn[-self.DEBT_MAX_SIZE:]

            if self.sender_shutdown.is_set():
                break

    def serialize(self, metrics):
        s = io.StringIO()
        for m in metrics:
            if self.prefix:
                s.write(self.prefix)
                s.write('.')
            s.write(m[0])
            s.write(' ')
            s.write(str(m[1]))
            s.write(' ')
            s.write(str(m[2]))
            s.write('\n')

        return s.getvalue()

    def delay(self):
        now = datetime.datetime.now()
        next_min = now.replace(second=0) + datetime.timedelta(minutes=1)

        return (next_min - now).total_seconds()
