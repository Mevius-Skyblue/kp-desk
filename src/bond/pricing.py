"""Fixed-coupon bond: schedule, price <-> yield, accrued interest, duration, convexity, DV01 (config/p2.yaml).

Yields and coupons are in percent (4.5 = 4.5%); prices are per 100 face. The yield is the street-convention
yield compounded at the coupon frequency: P_dirty = sum CF_i / (1 + y/f)^(f * t_i), t_i = (w + i - 1) / f.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.bond.daycount import DC_30360, DC_ICMA, add_months, days_30_360, period_fraction

# currency -> (coupon frequency, day count): config/p2.yaml conventions
CONVENTIONS = {"USD": (2, DC_30360), "EUR": (1, DC_ICMA), "UST": (2, DC_ICMA)}


@dataclass(frozen=True)
class Bond:
    """고정금리 채권 한 종목의 조건: 쿠폰(%), 발행일, 만기일, 연 이자 횟수, 일수 계산 관행."""

    coupon_pct: float
    issue: date
    maturity: date
    freq: int = 2
    dc: str = DC_30360


@dataclass(frozen=True)
class CashFlow:
    """결제일 이후 현금흐름 1건: 지급일, 금액(액면 100당), 수익률 할인 지수 f*t(기간 수)."""

    pay_date: date
    amount: float
    periods: float  # f * t_i = w + i - 1


def bond_for(currency: str, coupon_pct: float, issue: date, maturity: date) -> Bond:
    """통화별 관행(USD 30/360 반기, EUR Act/Act 연 1회)으로 Bond를 만든다."""
    if currency not in CONVENTIONS:
        raise ValueError(f"no convention for {currency}")
    f, dc = CONVENTIONS[currency]
    return Bond(coupon_pct, issue, maturity, f, dc)


def schedule(bond: Bond) -> list[tuple[date, date]]:
    """이자 지급일 목록 [(기간 시작(명목), 지급일)]. 만기에서 12/f개월씩 거꾸로 만들고, 첫 기간은 짧을 수 있다."""
    step = 12 // bond.freq
    out, k = [], 0
    while True:
        pay = add_months(bond.maturity, -step * k)
        if pay <= bond.issue:
            break
        out.append((add_months(bond.maturity, -step * (k + 1)), pay))
        k += 1
    if not out:
        raise ValueError("maturity must be after issue")
    return out[::-1]


def coupon_amount(bond: Bond, start: date, pay: date) -> float:
    """한 기간의 쿠폰(액면 100당). 정규 기간은 c/f, 발행일이 기간 중간이면(짧은 첫 기간) 일수 비율만큼."""
    c = bond.coupon_pct / bond.freq
    if start >= bond.issue:
        return c
    return c * period_fraction(bond.issue, pay, start, pay, bond.freq, bond.dc)


def _bracket(bond: Bond, settle: date) -> tuple[date, date]:
    """결제일이 속한 이자 기간 (직전 명목 지급일 pc, 다음 지급일 nc), pc <= settle < nc."""
    if not (bond.issue <= settle < bond.maturity):
        raise ValueError("settlement must be on/after issue and before maturity")
    for pc, nc in schedule(bond):
        if pc <= settle < nc:
            return pc, nc
    raise ValueError("settlement outside schedule")  # pragma: no cover


def accrued_interest(bond: Bond, settle: date) -> float:
    """경과이자(액면 100당): 직전 지급일(첫 기간이면 발행일)부터 결제일까지 쌓인 쿠폰."""
    pc, nc = _bracket(bond, settle)
    start = max(bond.issue, pc)
    return bond.coupon_pct / bond.freq * period_fraction(start, settle, pc, nc, bond.freq, bond.dc)


def cash_flows(bond: Bond, settle: date) -> list[CashFlow]:
    """결제일 이후의 현금흐름(쿠폰 + 만기 원금)과 각 흐름까지의 기간 수(w + i - 1)."""
    pc, nc = _bracket(bond, settle)
    w = period_fraction(settle, nc, pc, nc, bond.freq, bond.dc)
    out, i = [], 0
    for start, pay in schedule(bond):
        if pay <= settle:
            continue
        amt = coupon_amount(bond, start, pay) + (100.0 if pay == bond.maturity else 0.0)
        out.append(CashFlow(pay, amt, w + i))
        i += 1
    return out


def regular_period_not_180(bond: Bond) -> bool:
    """30/360에서 정규 기간 일수가 360/f가 아닌 기간이 있는지(2월 말 근처). QuantLib과 쿠폰 금액이 달라질 수 있는 표시."""
    if bond.dc != DC_30360:
        return False
    return any(days_30_360(pc, nc) != 360 // bond.freq for pc, nc in schedule(bond))


def dirty_price(bond: Bond, y_pct: float, settle: date) -> float:
    """수익률 -> 더티 가격(경과이자 포함): 각 현금흐름을 (1 + y/f)^(기간 수)로 할인해 더한다."""
    r = y_pct / 100 / bond.freq
    return sum(cf.amount / (1 + r) ** cf.periods for cf in cash_flows(bond, settle))


def price_from_yield(bond: Bond, y_pct: float, settle: date, clean: bool = True) -> float:
    """수익률 -> 가격. clean=True면 깨끗한 가격(더티 - 경과이자)."""
    p = dirty_price(bond, y_pct, settle)
    return p - accrued_interest(bond, settle) if clean else p


def settlement_amount(bond: Bond, clean_price: float, settle: date, face: float = 100.0) -> float:
    """실제 결제 금액 = (깨끗한 가격 + 경과이자) × 액면/100."""
    return (clean_price + accrued_interest(bond, settle)) * face / 100


def _price_and_slope(bond: Bond, y: float, settle: date) -> tuple[float, float]:
    """더티 가격과 dP/dy (y는 소수, 0.045 = 4.5%)."""
    f = bond.freq
    p = d = 0.0
    for cf in cash_flows(bond, settle):
        v = cf.amount / (1 + y / f) ** cf.periods
        p += v
        d -= (cf.periods / f) * v / (1 + y / f)
    return p, d


def yield_from_price(bond: Bond, price: float, settle: date, clean: bool = True) -> float:
    """가격 -> 수익률(%): 뉴턴법(기울기 사용) + 구간 이분법 안전장치. |P(y) - P| < 1e-12에서 멈춘다."""
    target = price + (accrued_interest(bond, settle) if clean else 0.0)
    lo, hi = -0.5, 1.0
    y = bond.coupon_pct / 100
    for _ in range(200):
        p, d = _price_and_slope(bond, y, settle)
        err = p - target
        if abs(err) < 1e-12:
            return y * 100
        if err > 0:  # price too high -> yield must rise
            lo = y
        else:
            hi = y
        y_new = y - err / d if d != 0 else (lo + hi) / 2
        y = y_new if lo < y_new < hi else (lo + hi) / 2
        if hi - lo < 1e-15:
            break
    return y * 100


def macaulay_duration(bond: Bond, y_pct: float, settle: date) -> float:
    """맥컬리 듀레이션(년): 현금흐름 시점 t_i를 현재가치 비중으로 가중평균."""
    r = y_pct / 100 / bond.freq
    pv = [(cf.periods / bond.freq, cf.amount / (1 + r) ** cf.periods) for cf in cash_flows(bond, settle)]
    p = sum(v for _, v in pv)
    return sum(t * v for t, v in pv) / p


def mod_duration(bond: Bond, y_pct: float, settle: date) -> float:
    """수정 듀레이션 = 맥컬리 / (1 + y/f): 수익률 1%p 변화 시 가격 변화율(%)."""
    return macaulay_duration(bond, y_pct, settle) / (1 + y_pct / 100 / bond.freq)


def convexity(bond: Bond, y_pct: float, settle: date) -> float:
    """볼록성 = (1/P) d²P/dy² (년²): 듀레이션만으로 설명 못 하는 가격 곡률."""
    f, r = bond.freq, y_pct / 100 / bond.freq
    cfs = cash_flows(bond, settle)
    p = sum(cf.amount / (1 + r) ** cf.periods for cf in cfs)
    s = sum(cf.amount * (cf.periods / f) * (cf.periods / f + 1 / f) / (1 + r) ** (cf.periods + 2) for cf in cfs)
    return s / p


def dv01(bond: Bond, y_pct: float, settle: date, face: float = 100.0) -> float:
    """DV01: 수익률 1bp 상승 시 가격 하락액(양수) = 수정 듀레이션 × 더티 가격 × 0.0001 × 액면/100."""
    return mod_duration(bond, y_pct, settle) * dirty_price(bond, y_pct, settle) * 1e-4 * face / 100
