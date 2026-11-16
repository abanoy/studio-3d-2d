import math
I=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
def require(ok, why):
    if not ok:
        raise ValueError(why)

def mm(a, b):
    return [sum((a[4 * r + k] * b[4 * k + c] for k in range(4))) for r in range(4) for c in range(4)]

def mv(a, v, w=1.0):
    return [sum((a[4 * r + k] * v[k] for k in range(3))) + a[4 * r + 3] * w for r in range(3)]

def inv(a):
    rows = [list(a[4 * r:4 * r + 4]) + I[4 * r:4 * r + 4] for r in range(4)]
    for c in range(4):
        pivot = max(range(c, 4), key=lambda r: abs(rows[r][c]))
        require(abs(rows[pivot][c]) > 1e-14, 'singular matrix')
        rows[c], rows[pivot] = (rows[pivot], rows[c])
        f = rows[c][c]
        rows[c] = [v / f for v in rows[c]]
        for r in range(4):
            if r != c:
                f = rows[r][c]
                rows[r] = [x - f * y for x, y in zip(rows[r], rows[c])]
    return [v for r in rows for v in r[4:]]

def maximum(a, b):
    return max((abs(x - y) for x, y in zip(a, b)))

def norm(v):
    return math.sqrt(sum((x * x for x in v)))

def trs(t, q, s=(1.0, 1.0, 1.0)):
    x, y, z, w = q
    n = norm(q)
    require(abs(n - 1) < 0.0001, 'nonunit quaternion')
    x, y, z, w = [v / n for v in q]
    a = [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), t[0], 2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), t[1], 2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), t[2], 0.0, 0.0, 0.0, 1.0]
    for r in range(3):
        for c in range(3):
            a[4 * r + c] *= s[c]
    return a
