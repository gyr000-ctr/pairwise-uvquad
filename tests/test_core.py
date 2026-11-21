import math

import pytest

import uvquad

def _raises(fn, exc=ValueError):
    try:
        fn()
    except exc:
        return True
    return False

C = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def _q():
    return uvquad.UvQuad(C)


def _check_corner00():
    return _q().sample(0.0, 0.0) == (0.0, 0.0)


def _check_corner11():
    return _q().sample(1.0, 1.0) == (1.0, 1.0)


def _check_center():
    p = _q().sample(0.5, 0.5)
    return abs(p[0] - 0.5) < 1e-9 and abs(p[1] - 0.5) < 1e-9


def _check_out_of_range():
    return _raises(lambda: _q().sample(1.5, 0.5))


def _check_bad_corners():
    return _raises(lambda: uvquad.UvQuad([(0.0, 0.0)]))


def _check_degenerate():
    return _raises(lambda: uvquad.UvQuad([(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]))


def _check_perspective_sum():
    w = _q().perspective_correct(0.5, 0.5, [1.0, 1.0, 1.0, 1.0])
    return abs(sum(w) - 1.0) < 1e-9


def _check_perspective_corners():
    return _q().perspective_correct(0.0, 0.0, [1.0, 1.0, 1.0, 1.0])[0] > 0.9


def _check_type():
    return isinstance(_q().sample(0.2, 0.2), tuple)


def _check_range():
    return all(0.0 <= v <= 1.0 for v in _q().sample(0.7, 0.3))


def _check_det():
    return _q().sample(0.4, 0.4) == _q().sample(0.4, 0.4)


def _check_perspective_weights():
    return len(_q().perspective_correct(0.3, 0.3, [1.0, 2.0, 3.0, 4.0])) == 4


def _check_bad_w():
    return _raises(lambda: _q().perspective_correct(0.5, 0.5, [1.0, 1.0, 0.0, 1.0]))


def _check_no_mut():
    src = list(C)
    _q().sample(0.5, 0.5)
    return C == src


def _check_non_square():
    q = uvquad.UvQuad([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)])
    return abs(q.sample(0.5, 0.5)[0] - 1.0) < 1e-9

CASES = [("corner00", "_check_corner00"), ("corner11", "_check_corner11"), ("center", "_check_center"), ("out_of_range", "_check_out_of_range"), ("bad_corners", "_check_bad_corners"), ("degenerate", "_check_degenerate"), ("perspective_sum", "_check_perspective_sum"), ("perspective_corners", "_check_perspective_corners"), ("type", "_check_type"), ("range", "_check_range"), ("det", "_check_det"), ("perspective_weights", "_check_perspective_weights"), ("bad_w", "_check_bad_w"), ("no_mut", "_check_no_mut"), ("non_square", "_check_non_square")]


@pytest.mark.parametrize("name,check", CASES, ids=[c[0] for c in CASES])
def test_spec(name, check):
    assert globals()[check]() is True
