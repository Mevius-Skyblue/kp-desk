"""Bond calculator of page ①: a thin wrapper that calls the validated engine src/bond as is (no new formula).

The same rules as src/bond/analytics.py are used for the spreads: G-spread = yield - linearly interpolated par yield at the
remaining tenor (days / 365.25), Z-spread on the zero curve bootstrapped from the as-of par curve anchored at settlement.
"""

from __future__ import annotations

from datetime import date

from src.bond.curve import bootstrap, g_spread, par_yield, z_spread
from src.bond.daycount import add_months
from src.bond.pricing import (
    CONVENTIONS,
    Bond,
    accrued_interest,
    cash_flows,
    convexity,
    coupon_amount,
    dirty_price,
    dv01,
    macaulay_duration,
    mod_duration,
    price_from_yield,
    schedule,
    settlement_amount,
    yield_from_price,
)

SPREAD_CONVENTIONS = ("USD",)  # spreads over US Treasuries only make sense for USD bonds


class CalcInputError(ValueError):
    """Inputs the engine cannot price (dates out of order). args[0] is a short code, not a sentence."""


def defaults(asof: date) -> dict:
    """Example inputs: settle on the as-of date, issued two months earlier, 5-year bond, 4.5% coupon, 5.0% yield."""
    issue = add_months(asof, -2)
    return {"conv": "USD", "coupon": 4.5, "issue": issue, "maturity": add_months(issue, 60), "settle": asof,
            "face": 1_000_000.0, "yield_pct": 5.0, "clean_price": 98.0}


def calculate(conv: str, coupon: float, issue: date, maturity: date, settle: date, face: float,
              yield_pct: float | None = None, clean_price: float | None = None,
              curve_points: dict[float, float] | None = None) -> dict:
    """Price / yield, accrued, settlement amount, durations, convexity, DV01, and G / Z spreads (USD with a curve).

    Give either yield_pct (-> price) or clean_price (-> yield). Returns plain floats; spreads are None when not applicable.
    """
    if conv not in CONVENTIONS:
        raise CalcInputError("convention")
    if not (issue <= settle < maturity):
        raise CalcInputError("dates")
    freq, dc = CONVENTIONS[conv]
    bond = Bond(float(coupon), issue, maturity, freq, dc)
    if yield_pct is not None:
        y = float(yield_pct)
        clean = price_from_yield(bond, y, settle)
    elif clean_price is not None:
        clean = float(clean_price)
        y = yield_from_price(bond, clean, settle)
    else:
        raise CalcInputError("yield_or_price")
    ai = accrued_interest(bond, settle)
    out = {
        "clean": clean, "dirty": dirty_price(bond, y, settle), "yield_pct": y, "accrued": ai,
        "settle_amount": settlement_amount(bond, clean, settle, face),
        "mac_duration": macaulay_duration(bond, y, settle), "mod_duration": mod_duration(bond, y, settle),
        "convexity": convexity(bond, y, settle), "dv01": dv01(bond, y, settle, face),
        "tenor_years": (maturity - settle).days / 365.25, "ust_par_pct": None, "g_spread_bp": None, "z_spread_bp": None,
    }
    if conv in SPREAD_CONVENTIONS and curve_points:
        out["ust_par_pct"] = par_yield(curve_points, out["tenor_years"])
        out["g_spread_bp"] = g_spread(y, curve_points, out["tenor_years"])
        out["z_spread_bp"] = z_spread(bond, clean, settle, bootstrap(curve_points, settle, maturity))
    return out


def cash_flow_rows(conv: str, coupon: float, issue: date, maturity: date, settle: date) -> list[dict]:
    """Payments after the settlement date for the ① chart, per 100 face, taken from the engine as is (fixes U2-1 A):
    date, total and discount periods from cash_flows(); the coupon from coupon_amount() on the same schedule() period;
    principal = the 100 that cash_flows() adds on the maturity date. No new formula: coupon + principal = total.

    Call after calculate() succeeded (same inputs), which has already checked the dates."""
    if conv not in CONVENTIONS:
        raise CalcInputError("convention")
    freq, dc = CONVENTIONS[conv]
    bond = Bond(float(coupon), issue, maturity, freq, dc)
    periods = [(start, pay) for start, pay in schedule(bond) if pay > settle]  # the periods cash_flows() keeps
    flows = cash_flows(bond, settle)
    if len(periods) != len(flows) or any(pay != cf.pay_date for (_, pay), cf in zip(periods, flows)):
        raise CalcInputError("schedule")  # pragma: no cover - the engine builds both from schedule()
    return [{"date": cf.pay_date, "coupon": coupon_amount(bond, start, pay),
             "principal": 100.0 if pay == bond.maturity else 0.0, "total": cf.amount, "periods": cf.periods, "freq": freq}
            for (start, pay), cf in zip(periods, flows)]
