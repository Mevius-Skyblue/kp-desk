"""Treasury par curve -> zero curve (bootstrap), G-spread, Z-spread, spread duration (config/p2.yaml curve / z_spread).

Exact definition (so QuantLib can replicate it):
  anchor A = bond settlement date; grid G_k = A + 6k months (k = 1..K, K >= 60 and G_K >= last cash flow);
  par c_k = par_yield(k/2) (linear default); par bond k pays c_k/2 on G_1..G_k + 100 at G_k, price 100;
  DF_k = (1 - c_k/2 * sum_{j<k} DF_j) / (1 + c_k/2); tau = days(A, d) / 365; DF log-linear in tau over (0, 1), (tau_k, DF_k);
  zero z(tau) = 2 * (DF^(-1/(2 tau)) - 1); Z-spread s: P_dirty = sum CF_i * (1 + (z_i + s)/2)^(-2 tau_i).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import numpy as np

from src.bond.daycount import add_months
from src.bond.interp import LINEAR, interpolate
from src.bond.pricing import Bond, accrued_interest, cash_flows

MIN_GRID = 60  # 30 years of semi-annual nodes


def par_yield(points: dict[float, float], tenor: float, method: str = LINEAR) -> float:
    """만기 tenor(년)의 par 수익률(%)을 재무부 par 커브 점들에서 보간한다(기본 선형, 양 끝 밖은 평평하게)."""
    xs = list(points.keys())
    ys = list(points.values())
    return float(interpolate(xs, ys, tenor, method))


def g_spread(yield_pct: float, points: dict[float, float], tenor: float, method: str = LINEAR) -> float:
    """G-spread(bp) = 채권 수익률 - 같은 만기의 보간 미국채 par 수익률."""
    return (yield_pct - par_yield(points, tenor, method)) * 100


@dataclass
class ZeroCurve:
    """부트스트랩한 할인 커브: 기준일 A, 격자 날짜·할인계수. 그 사이 날짜는 log(DF)를 선형 보간한다."""

    anchor: date
    node_dates: list[date]
    node_df: np.ndarray
    par_on_grid: np.ndarray

    def __post_init__(self):
        # node times (0 = anchor) and ln(DF) for the log-linear interpolation
        self._nt = np.array([0.0] + [self.tau(d) for d in self.node_dates])
        self._lndf = np.log(np.concatenate([[1.0], self.node_df]))

    def tau(self, d: date) -> float:
        """기준일부터 d까지의 시간(년, Act/365 Fixed)."""
        return (d - self.anchor).days / 365.0

    def df(self, d: date) -> float:
        """날짜 d의 할인계수: 격자 점 사이에서 ln(DF)를 시간에 대해 직선으로 잇는다(log-linear)."""
        t = self.tau(d)
        if t < 0:
            raise ValueError("date before curve anchor")
        if t > self._nt[-1] + 1e-12:
            raise ValueError("date beyond the last curve node")
        return float(np.exp(np.interp(t, self._nt, self._lndf)))

    def zero_rate(self, d: date) -> float:
        """반기 복리 제로 금리(소수): DF = (1 + z/2)^(-2τ) 를 z에 대해 푼 값."""
        t = self.tau(d)
        if t <= 0:
            raise ValueError("zero rate needs tau > 0")
        return 2 * (self.df(d) ** (-1 / (2 * t)) - 1)


def bootstrap(points: dict[float, float], anchor: date, last_date: date | None = None, method: str = LINEAR) -> ZeroCurve:
    """재무부 par 커브 -> 제로 커브. 6개월 격자마다 'par 채권 가격 = 100' 조건으로 할인계수를 차례로 푼다."""
    k_max = MIN_GRID
    if last_date is not None:
        while add_months(anchor, 6 * k_max) < last_date:
            k_max += 1
    dates = [add_months(anchor, 6 * k) for k in range(1, k_max + 1)]
    par = np.array([par_yield(points, k / 2, method) for k in range(1, k_max + 1)]) / 100
    df = np.empty(k_max)
    annuity = 0.0  # sum of DF_j for j < k
    for i, c in enumerate(par):
        df[i] = (1 - c / 2 * annuity) / (1 + c / 2)
        annuity += df[i]
    return ZeroCurve(anchor, dates, df, par * 100)


def _z_price_and_slope(cfs, curve: ZeroCurve, settle: date, s: float) -> tuple[float, float]:
    """Z-spread s(소수)에서의 더티 가격과 dP/ds. 결제일이 기준일과 다르면 결제일 할인계수로 나눈다(QuantLib npvDate 방식)."""

    def disc(d: date) -> tuple[float, float]:
        t = curve.tau(d)
        if t <= 0:
            return 1.0, 0.0
        base = 1 + (curve.zero_rate(d) + s) / 2
        v = base ** (-2 * t)
        return v, -t * v / base  # value, derivative wrt s

    ds, dds = disc(settle)
    p = dp = 0.0
    for cf in cfs:
        v, dv = disc(cf.pay_date)
        p += cf.amount * v / ds
        dp += cf.amount * (dv * ds - v * dds) / ds**2
    return p, dp


def z_spread(bond: Bond, price: float, settle: date, curve: ZeroCurve, clean: bool = True) -> float:
    """Z-spread(bp): 제로 커브의 모든 점(반기 복리)에 같은 s를 더해 할인한 값이 시장 더티 가격과 같아지는 s."""
    target = price + (accrued_interest(bond, settle) if clean else 0.0)
    cfs = cash_flows(bond, settle)
    lo, hi, s = -0.5, 1.0, 0.0
    for _ in range(200):
        p, d = _z_price_and_slope(cfs, curve, settle, s)
        err = p - target
        if abs(err) < 1e-12:
            return s * 1e4
        if err > 0:
            lo = s
        else:
            hi = s
        s_new = s - err / d if d != 0 else (lo + hi) / 2
        s = s_new if lo < s_new < hi else (lo + hi) / 2
        if hi - lo < 1e-15:
            break
    if not math.isfinite(s):  # pragma: no cover
        raise ValueError("z-spread did not converge")
    return s * 1e4


def z_price(bond: Bond, z_bp: float, settle: date, curve: ZeroCurve, clean: bool = True) -> float:
    """주어진 Z-spread(bp)로 할인한 가격(검증·시험용, z_spread의 역함수)."""
    p, _ = _z_price_and_slope(cash_flows(bond, settle), curve, settle, z_bp / 1e4)
    return p - accrued_interest(bond, settle) if clean else p


def spread_duration(bond: Bond, z_bp: float, settle: date, curve: ZeroCurve) -> float:
    """스프레드 듀레이션(년) = -(1/P) dP/ds: Z-spread가 1%p 오를 때 가격이 몇 % 내리는지."""
    p, dp = _z_price_and_slope(cash_flows(bond, settle), curve, settle, z_bp / 1e4)
    return -dp / p
