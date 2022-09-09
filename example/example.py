import time
import random
import pyrite


g = pyrite.Pyrite('graphite.localdomain', 2003,
                  interval=60, prefix='example')

# Callable passed to gauge will be called every time
# metrics snapshot is taken.
g.gauge('gauge', lambda: int(time.time()))

# Multiple gauges can be generated withing a single call.
g.gauges('gauges', lambda: (('a', 1), ('b', 2), ('c', 3)))

# Counter is simple as usual.
c = g.counter('counter')
c.inc(random.randint(0, 100))

# Series will generate sum, count, min, max, average,
# 50pct, 75pct, 95pct, and 99pct metrics.
s = g.series('series')
s.add(random.randint(0, 100))

g.close()
