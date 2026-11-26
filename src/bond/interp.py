"""Interpolation of par yields by tenor (config/p2.yaml curve): linear (default) and monotone cubic (sensitivity)."""

from __future__ import annotations

import numpy as np

LINEAR = "linear"
MONOTONE_CUBIC = "monotone_cubic"


def _clean(xs, ys) -> tuple[np.ndarray, np.ndarray]:
    """NaN을 빼고 만기 순으로 정렬한 (x, y) 배열."""
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    ok = ~(np.isnan(x) | np.isnan(y))
    order = np.argsort(x[ok], kind="stable")
    return x[ok][order], y[ok][order]


def linear(xs, ys, x):
    """선형 보간. 양 끝 밖은 가장 가까운 끝 값(평평하게)."""
    xa, ya = _clean(xs, ys)
    return np.interp(x, xa, ya)


def fritsch_carlson_slopes(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """단조 3차 보간의 각 점 기울기(Fritsch-Carlson 1980): 할선 평균 -> 부호가 바뀌면 0 -> a²+b²>9면 줄인다."""
    n = len(x)
    d = np.diff(y) / np.diff(x)  # secants
    m = np.empty(n)
    m[0], m[-1] = d[0], d[-1]
    for k in range(1, n - 1):
        m[k] = 0.0 if d[k - 1] * d[k] <= 0 else (d[k - 1] + d[k]) / 2
    for k in range(n - 1):
        if d[k] == 0:
            m[k] = m[k + 1] = 0.0
            continue
        a, b = m[k] / d[k], m[k + 1] / d[k]
        s = a * a + b * b
        if s > 9:
            tau = 3 / np.sqrt(s)
            m[k], m[k + 1] = tau * a * d[k], tau * b * d[k]
    return m


def monotone_cubic(xs, ys, x):
    """단조 3차(에르미트) 보간: 점 사이에서 값이 튀어 오르지 않게(단조 유지) 매끄럽게 잇는다. 양 끝 밖은 평평하게."""
    xa, ya = _clean(xs, ys)
    xq = np.asarray(x, dtype=float)
    scalar = xq.ndim == 0
    xq = np.atleast_1d(xq)
    if len(xa) < 3:
        out = np.interp(xq, xa, ya)
        return float(out[0]) if scalar else out
    m = fritsch_carlson_slopes(xa, ya)
    xc = np.clip(xq, xa[0], xa[-1])
    k = np.clip(np.searchsorted(xa, xc, side="right") - 1, 0, len(xa) - 2)
    h = xa[k + 1] - xa[k]
    t = (xc - xa[k]) / h
    h00 = 2 * t**3 - 3 * t**2 + 1
    h10 = t**3 - 2 * t**2 + t
    h01 = -2 * t**3 + 3 * t**2
    h11 = t**3 - t**2
    out = h00 * ya[k] + h10 * h * m[k] + h01 * ya[k + 1] + h11 * h * m[k + 1]
    return float(out[0]) if scalar else out


def interpolate(xs, ys, x, method: str = LINEAR):
    """method 이름으로 보간 방법을 고른다(linear 기본, monotone_cubic 민감도)."""
    if method == LINEAR:
        return linear(xs, ys, x)
    if method == MONOTONE_CUBIC:
        return monotone_cubic(xs, ys, x)
    raise ValueError(method)
