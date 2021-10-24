import time
import random
import pygraphite


g = pygraphite.Graphite('graphite.localdomain', 2003,
                        interval=60, prefix='example')

# Callable passed to gauge will be called every time
# metrics snapshot is taken.
g.gauge('gauge', lambda: int(time.time()))

# Counter is simple as usual.
c = g.counter('counter')
c.inc(random.randint(0, 100))

# Series will generate sum, count, min, max, average,
# 50pct, 75pct, 95pct, and 99pct metrics.
s = g.series('series')
s.add(random.randint(0, 100))

g.close()
