import random
import threading


class Metric:
    def __init__(self, name):
        self.name = name

    def snapshot(self):
        raise NotImplemented()


class Counter(Metric):
    def __init__(self, name):
        super().__init__(name)
        self.value = 0
        self.lock = threading.Lock()

    def inc(self, delta=1):
        with self.lock:
            self.value += delta

    def snapshot(self):
        with self.lock:
            v = self.value
            self.value = 0

            return ((self.name, v),)


class Gauge(Metric):
    def __init__(self, name, value):
        super().__init__(name)
        self.value = value

    def snapshot(self):
        v = self.value()
        if v is None:
            return None
        else:
            return ((self.name, v),)


class Gauges(Metric):
    def __init__(self, name, values):
        super().__init__(name)
        self.values = values

    def snapshot(self):
        s = []
        for n, v in self.values():
            s.append((self.name + '.' + n, v))

        return s


class Series(Metric):
    MAX_SAMPLES = 1000
    INF = float("inf")

    def __init__(self, name):
        super().__init__(name)
        self.lock = threading.Lock()
        self.samples = [None] * self.MAX_SAMPLES
        self.count = 0
        self.sum = 0
        self.min = 0
        self.max = 0

    def add(self, value):
        with self.lock:
            self.sum += value
            if self.count == 0 or value < self.min:
                self.min = value
            if self.count == 0 or value > self.max:
                self.max = value
            # Add new sample or replace one of the existing N samples
            # with probability MAX_SAMPLES/count otherwise.
            if self.count < self.MAX_SAMPLES:
                self.samples[self.count] = value
            else:
                if random.random() < (self.MAX_SAMPLES / float(count)):
                    i = int(random.random() * self.MAX_SAMPLES)
                    self.samples[i] = value
            self.count += 1

    def snapshot(self):
        with self.lock:
            s = []
            s.append((self.name + '.sum', self.sum))
            s.append((self.name + '.count', self.count))
            s.append((self.name + '.min', self.min))
            s.append((self.name + '.max', self.max))
            if self.count:
                i = min(self.count, self.MAX_SAMPLES)
                self.samples.sort(key=lambda x: x if x is not None else self.INF)
                s.append((self.name + '.pct50', self.samples[int(i / 2)]))
                s.append((self.name + '.pct75', self.samples[int(i * 3 / 4)]))
                s.append((self.name + '.pct95', self.samples[int(i * 95 / 100)]))
                s.append((self.name + '.pct99', self.samples[int(i * 99 / 100)]))
                s.append((self.name + '.avg', self.sum / self.count))
            else:
                s.append((self.name + '.pct50', 0.0));
                s.append((self.name + '.pct75', 0.0));
                s.append((self.name + '.pct95', 0.0));
                s.append((self.name + '.pct99', 0.0));
                s.append((self.name + '.avg', 0.0));

            self.count = 0;
            self.sum = 0;
            self.min = 0;
            self.max = 0;

            return s
