"""uvquad 核心 API：UV 四边形取样与透视校正。

- 取样使用双线性插值，四角精确返回原始顶点；
- 透视校正返回四个角的齐次权重，权重恒和为 1；
- 构造后对象不可变，可安全地在多线程间共享。
"""

_NEGLIGIBLE = 1e-12
_INF = float("inf")


def _as_float(value, name):
    """把输入转成有限 float：类型错误 -> TypeError，非有限 -> ValueError。"""
    if type(value) is float:
        if -_INF < value < _INF:
            return value
        raise ValueError("%s 必须为有限数值，收到 %r" % (name, value))
    if isinstance(value, (str, bytes, bytearray)):
        raise TypeError("%s 必须为数值，收到 %r" % (name, type(value).__name__))
    try:
        out = float(value)
    except (TypeError, ValueError):
        raise TypeError("%s 必须为数值，收到 %r" % (name, type(value).__name__))
    if not -_INF < out < _INF:
        raise ValueError("%s 必须为有限数值，收到 %r" % (name, value))
    return out


def _unit(value, name):
    """UV 参数校验：必须在 [0, 1] 内。"""
    out = _as_float(value, name)
    if out < 0.0 or out > 1.0:
        raise ValueError("%s 必须位于 [0, 1] 内，收到 %r" % (name, value))
    return out


def _positive(value, name):
    """深度校验：必须是有限正数。"""
    out = _as_float(value, name)
    if out <= 0.0:
        raise ValueError("%s 必须为正数，收到 %r" % (name, value))
    return out


class UvQuad:
    """由四个角点（左上、右上、右下、左下）定义的四边形。"""

    __slots__ = ("_corners", "_ox", "_oy", "_ax", "_ay", "_bx", "_by", "_cx", "_cy")

    def __init__(self, corners):
        """按四角构造，顺序为 (0,0), (1,0), (1,1), (0,1)。

        退化四边形（共线、重合、自交或面积可忽略）抛出 ValueError。
        """
        try:
            points = list(corners)
        except TypeError:
            raise TypeError("corners 必须为可迭代的四个点")
        if len(points) != 4:
            raise ValueError("corners 必须恰好包含四个点，收到 %d 个" % len(points))

        pts = []
        for index, point in enumerate(points):
            try:
                px, py = point
            except (TypeError, ValueError):
                raise TypeError("corners[%d] 必须为 (x, y) 二元组" % index)
            pts.append((_as_float(px, "corners[%d].x" % index),
                        _as_float(py, "corners[%d].y" % index)))

        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts

        # 两个三角形的有向面积必须同号且不可忽略，否则视为退化。
        area_a = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)
        area_b = (x2 - x0) * (y3 - y0) - (y2 - y0) * (x3 - x0)
        scale = max(
            max(x for x, _ in pts) - min(x for x, _ in pts),
            max(y for _, y in pts) - min(y for _, y in pts),
        )
        threshold = _NEGLIGIBLE * scale * scale
        same_winding = (area_a > threshold and area_b > threshold) or (
            area_a < -threshold and area_b < -threshold
        )
        if not same_winding:
            raise ValueError("四边形退化，无法构造 UvQuad")

        self._corners = pts
        self._ox, self._oy = x0, y0
        # 双线性展开：P(u, v) = P0 + A*u + B*v + C*u*v
        self._ax, self._ay = x1 - x0, y1 - y0
        self._bx, self._by = x3 - x0, y3 - y0
        self._cx, self._cy = x0 - x1 + x2 - x3, y0 - y1 + y2 - y3

    def sample(self, u, v):
        """双线性取样，返回 (x, y)；四角返回精确顶点坐标。"""
        u = _unit(u, "u")
        v = _unit(v, "v")

        corners = self._corners
        if u == 0.0:
            if v == 0.0:
                return corners[0]
            if v == 1.0:
                return corners[3]
        elif u == 1.0:
            if v == 0.0:
                return corners[1]
            if v == 1.0:
                return corners[2]

        return (
            self._ox + self._ax * u + self._bx * v + self._cx * u * v,
            self._oy + self._ay * u + self._by * v + self._cy * u * v,
        )

    def perspective_correct(self, u, v, w):
        """透视校正：按四角双线性权重与深度 w 计算归一化权重。

        w 为四个角点处的深度（必须为有限正数）。返回长度为 4 的权重元组，
        保证和为 1；退化深度（<= 0）抛出 ValueError。
        """
        u = _unit(u, "u")
        v = _unit(v, "v")

        wtype = type(w)
        if wtype is tuple or wtype is list:
            if len(w) != 4:
                raise ValueError("w 必须恰好包含四个数值，收到 %d 个" % len(w))
            w0, w1, w2, w3 = w
        else:
            try:
                items = list(w)
            except TypeError:
                raise TypeError("w 必须为可迭代的四个数值")
            if len(items) != 4:
                raise ValueError("w 必须恰好包含四个数值，收到 %d 个" % len(items))
            w0, w1, w2, w3 = items

        w0 = _positive(w0, "w[0]")
        w1 = _positive(w1, "w[1]")
        w2 = _positive(w2, "w[2]")
        w3 = _positive(w3, "w[3]")

        # 齐次权重：1/w 参与插值，再做归一化，保证权重和为 1。
        iu = 1.0 - u
        iv = 1.0 - v
        q0 = iu * iv / w0
        q1 = u * iv / w1
        q2 = u * v / w2
        q3 = iu * v / w3
        total = q0 + q1 + q2 + q3
        return (q0 / total, q1 / total, q2 / total, q3 / total)
