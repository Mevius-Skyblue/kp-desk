"""P2 textbook examples with fixed answers (config/p2.yaml tests.textbook_examples = 5).

Each example states its source. Published answers are checked to their published rounding; the same numbers
are also checked against an independent closed-form formula (annuity / zero-coupon algebra) to 1e-10.
"""

from datetime import date

import pytest

from src.bond.daycount import DC_30360, DC_ICMA, days_30_360
from src.bond.pricing import Bond, accrued_interest, convexity, macaulay_duration, mod_duration, price_from_yield


def annuity_price(c_pct: float, y_pct: float, n: int, f: int = 2) -> float:
    """Closed form: coupon annuity + discounted principal, n whole periods."""
    r = y_pct / 100 / f
    return c_pct / f * (1 - (1 + r) ** -n) / r + 100 * (1 + r) ** -n


def test_tb1_fabozzi_price_20y_10pct_at_11pct():
    # Fabozzi, "Bond Markets, Analysis, and Strategies" (Pearson), chapter "Pricing of Bonds":
    # a 20-year 10% coupon bond (semi-annual) priced to yield 11% is worth $919.77 per $1,000 face.
    b = Bond(10.0, date(2020, 1, 15), date(2040, 1, 15), 2, DC_ICMA)
    p = price_from_yield(b, 11.0, date(2020, 1, 15))
    assert round(p * 10, 2) == 919.77
    assert abs(p - annuity_price(10, 11, 40)) < 1e-10


def test_tb2_fabozzi_duration_5y_9pct_at_9pct():
    # Fabozzi, same book, chapter "Measuring Interest Rate Risk": 5-year 9% coupon bond selling to yield 9%
    # has Macaulay duration 4.13 years and modified duration 3.96.
    b = Bond(9.0, date(2020, 1, 15), date(2025, 1, 15), 2, DC_ICMA)
    s = date(2020, 1, 15)
    mac, mod = macaulay_duration(b, 9.0, s), mod_duration(b, 9.0, s)
    assert round(mac, 2) == 4.13 and round(mod, 2) == 3.96
    # closed form for a par bond: Macaulay (periods) = (1 + r) / r * (1 - (1 + r)^-n)
    r, n = 0.045, 10
    assert abs(mac - (1 + r) / r * (1 - (1 + r) ** -n) / 2) < 1e-10
    assert abs(price_from_yield(b, 9.0, s) - 100) < 1e-10


def test_tb3_zero_coupon_closed_form():
    # CFA Program curriculum, Fixed Income, "Understanding Fixed-Income Risk and Return": the Macaulay duration of a
    # zero-coupon bond equals its time to maturity. Closed forms (semi-annual compounding, T = 10, y = 6%):
    # P = 100 / 1.03^20 = 55.3676, MacD = 10, ModD = 10 / 1.03, Convexity = T (T + 0.5) / 1.03^2.
    b = Bond(0.0, date(2020, 1, 15), date(2030, 1, 15), 2, DC_ICMA)
    s = date(2020, 1, 15)
    p = price_from_yield(b, 6.0, s)
    assert round(p, 4) == 55.3676
    assert abs(p - 100 / 1.03**20) < 1e-10
    assert abs(macaulay_duration(b, 6.0, s) - 10) < 1e-12
    assert abs(mod_duration(b, 6.0, s) - 10 / 1.03) < 1e-12
    assert abs(convexity(b, 6.0, s) - 10 * 10.5 / 1.03**2) < 1e-10


def test_tb4_30_360_accrued_msrb_g33():
    # MSRB Rule G-33 (https://www.msrb.org/Rules-and-Interpretations/MSRB-Rules/General/Rule-G-33), 30/360 day count:
    # days = (Y2-Y1)*360 + (M2-M1)*30 + (D2-D1), D1 = 31 -> 30, D2 = 31 -> 30 when D1 is 30 or 31.
    # Example: 6% semi-annual corporate, last coupon 2025-03-01, settlement 2025-07-17 -> 136 days,
    # accrued = 6/2 * 136/180 = 2.266667 per 100.
    assert days_30_360(date(2025, 3, 1), date(2025, 7, 17)) == 136
    assert days_30_360(date(2025, 1, 31), date(2025, 3, 31)) == 60
    assert days_30_360(date(2025, 1, 30), date(2025, 2, 28)) == 28
    b = Bond(6.0, date(2024, 9, 1), date(2030, 9, 1), 2, DC_30360)
    ai = accrued_interest(b, date(2025, 7, 17))
    assert round(ai, 6) == 2.266667
    assert abs(ai - 3 * 136 / 180) < 1e-12


def test_tb5_treasury_act_act_accrued_and_par():
    # US Treasury notes: accrued interest = (C/2) * (days since last interest date / days in the half-year period),
    # 31 CFR Part 356 Appendix B (https://www.ecfr.gov/current/title-31/subtitle-B/chapter-II/subchapter-A/part-356).
    # Example: 2.5% note, coupons Feb 15 / Aug 15, settlement 2023-03-01: 14 of 181 days -> 1.25 * 14/181 = 0.096685.
    b = Bond(2.5, date(2020, 2, 15), date(2030, 2, 15), 2, DC_ICMA)
    ai = accrued_interest(b, date(2023, 3, 1))
    assert round(ai, 6) == 0.096685
    assert abs(ai - 1.25 * 14 / 181) < 1e-12
    # on a coupon date a note priced at a yield equal to its coupon is at par
    assert abs(price_from_yield(b, 2.5, date(2023, 2, 15)) - 100) < 1e-10
    assert price_from_yield(b, 2.5, date(2023, 3, 1)) == pytest.approx(100, abs=0.01)
