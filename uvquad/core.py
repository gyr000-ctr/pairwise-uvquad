"""uvquad 核心 API（初始未实现）。"""


class UvQuad:
    def __init__(self, corners):
        """按四角构造"""
        raise NotImplementedError

    def sample(self, u, v):
        """取样"""
        raise NotImplementedError

    def perspective_correct(self, u, v, w):
        """透视校正"""
        raise NotImplementedError
