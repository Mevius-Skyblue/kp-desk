"""Day counts and date helpers (config/p2.yaml conventions / settlement)."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

DC_30360 = "30/360"
DC_ICMA = "ACT/ACT_ICMA"


def add_months(d: date, months: int) -> date:
    """날짜에 개월 수를 더한다. 그 달에 같은 날이 없으면 월말로 자른다(예: 8/31 - 6개월 = 2/28)."""
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def days_30_360(d1: date, d2: date) -> int:
    """30/360(미국 채권 기준) 일수: 시작일 31일 -> 30일, 끝일 31일은 시작일이 30일 이상이면 30일로 본다."""
    a, b = min(d1.day, 30), d2.day
    if a == 30 and b == 31:
        b = 30
    return 360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (b - a)


def period_fraction(a: date, b: date, pc: date, nc: date, freq: int, dc: str) -> float:
    """a~b 기간이 이자 한 기간(pc~nc)의 몇 분의 몇인지. 30/360은 (30/360 일수)/(360/f), ICMA는 실제일수 비율."""
    if dc == DC_30360:
        return days_30_360(a, b) / (360 / freq)
    if dc == DC_ICMA:
        return (b - a).days / (nc - pc).days
    raise ValueError(f"unknown day count {dc}")


def add_weekdays(d: date, n: int) -> date:
    """d에서 영업일(월~금, 공휴일 무시) n일 뒤 날짜."""
    out, step = d, (1 if n >= 0 else -1)
    for _ in range(abs(n)):
        out += timedelta(days=step)
        while out.weekday() >= 5:
            out += timedelta(days=step)
    return out


def settlement_date(trade_date: date, t_plus: int) -> date:
    """결제일 = 거래일 + T+n 영업일 (n은 config/p2.yaml settlement 값)."""
    return add_weekdays(trade_date, t_plus)
