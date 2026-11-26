"""B4 채권 엔진 경계 사례: 일수 계산·결제일·단기·무이표·음수 금리·보간·Z-spread (합성 입력)."""

from datetime import date

import numpy as np
import pytest

from src.bond.curve import bootstrap, g_spread, par_yield, spread_duration, z_price, z_spread
from src.bond.daycount import add_months, add_weekdays, days_30_360, settlement_date
from src.bond.interp import interpolate, linear, monotone_cubic
from src.bond.pricing import (
    Bond,
    accrued_interest,
    bond_for,
    cash_flows,
    convexity,
    coupon_amount,
    dirty_price,
    dv01,
    mod_duration,
    price_from_yield,
    schedule,
    settlement_amount,
    yield_from_price,
)

B = Bond(4.0, date(2025, 1, 15), date(2030, 1, 15))
FLAT = {0.5: 4.0, 1.0: 4.0, 30.0: 4.0}


@pytest.mark.parametrize(
    "d1,d2,want",
    [(date(2025, 1, 31), date(2025, 3, 31), 60), (date(2025, 1, 30), date(2025, 3, 31), 60),
     (date(2025, 1, 29), date(2025, 3, 31), 62), (date(2024, 2, 29), date(2024, 3, 31), 32),
     (date(2025, 2, 28), date(2025, 3, 31), 33), (date(2025, 1, 15), date(2025, 1, 15), 0)],
)
def test_30_360_month_end(d1, d2, want):
    """30/360: 시작일 31→30, 끝일 31은 시작일이 30 이상일 때만 30으로, 2월 말은 그대로."""
    assert days_30_360(d1, d2) == want


def test_add_months_clamps_to_month_end():
    """add_months: 8/31 -6개월은 평·윤년 2월 말로, 1/31 +1개월은 2/28로 자른다."""
    assert add_months(date(2024, 8, 31), -6) == date(2024, 2, 29)
    assert add_months(date(2025, 8, 31), -6) == date(2025, 2, 28)
    assert add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)
    assert add_months(date(2025, 12, 15), 2) == date(2026, 2, 15)


def test_settlement_skips_weekend():
    """T+1: 금요일 거래는 월요일 결제, T+0은 그대로, 음수는 앞 영업일."""
    assert settlement_date(date(2025, 1, 3), 1) == date(2025, 1, 6)
    assert settlement_date(date(2025, 1, 3), 0) == date(2025, 1, 3)
    assert add_weekdays(date(2025, 1, 6), -1) == date(2025, 1, 3)


def test_schedule_end_of_month_maturity():
    """만기가 월말(8/31)이면 이자 지급일은 2월에 말일로 잘린다."""
    b = Bond(4.0, date(2024, 8, 31), date(2026, 8, 31))
    pays = [p for _, p in schedule(b)]
    assert date(2025, 2, 28) in pays and date(2025, 8, 31) in pays and date(2026, 2, 28) in pays


def test_accrued_zero_on_coupon_date_and_before_it():
    """경과이자: 지급일 당일 0, 지급 하루 전은 179/180 반기 쿠폰."""
    assert accrued_interest(B, date(2025, 7, 15)) == 0.0
    assert accrued_interest(B, date(2025, 1, 15)) == 0.0
    assert accrued_interest(B, date(2025, 7, 14)) == pytest.approx(2.0 * 179 / 180)


def test_cash_flows_on_coupon_date_excludes_that_coupon():
    """결제일이 지급일이면 그날 쿠폰은 현금흐름에 없고 첫 흐름의 기간 수는 정확히 1."""
    cfs = cash_flows(B, date(2025, 7, 15))
    assert cfs[0].pay_date == date(2026, 1, 15) and cfs[0].periods == pytest.approx(1.0)


def test_one_day_before_coupon_first_flow_is_tiny_fraction():
    """지급 하루 전 결제: 첫 흐름 기간 수는 1/180, 쿠폰 전체를 포함."""
    cfs = cash_flows(B, date(2025, 7, 14))
    assert cfs[0].periods == pytest.approx(1 / 180) and cfs[0].amount == pytest.approx(2.0)


def test_maturity_under_six_months_single_cash_flow():
    """잔존 6개월 미만: 현금흐름은 1건(마지막 쿠폰+원금), 쿠폰=수익률이면 깨끗한 가격 약 100."""
    b = Bond(4.0, date(2025, 1, 15), date(2025, 6, 15))
    st = date(2025, 2, 15)
    cfs = cash_flows(b, st)
    assert len(cfs) == 1 and cfs[0].amount > 100
    assert price_from_yield(b, 4.0, st) == pytest.approx(100.0, abs=1e-3)


def test_short_first_period_coupon_and_accrual():
    """짧은 첫 기간(발행 3/1, 첫 지급 7/15): 첫 쿠폰은 134/180 비율, 발행일 경과이자 0."""
    b = Bond(4.0, date(2025, 3, 1), date(2030, 1, 15))
    first = schedule(b)[0]
    assert coupon_amount(b, *first) == pytest.approx(2.0 * 134 / 180)
    assert accrued_interest(b, date(2025, 3, 1)) == 0.0
    assert accrued_interest(b, date(2025, 4, 1)) == pytest.approx(2.0 * 30 / 180)


def test_settlement_outside_life_raises():
    """결제일이 만기 당일이거나 발행 전이면 오류(경계: 발행일 포함, 만기일 제외)."""
    with pytest.raises(ValueError):
        cash_flows(B, B.maturity)
    with pytest.raises(ValueError):
        accrued_interest(B, date(2025, 1, 14))
    assert accrued_interest(B, B.issue) == 0.0


def test_maturity_not_after_issue_raises():
    """만기가 발행일 이하이면 일정 생성이 오류."""
    with pytest.raises(ValueError):
        schedule(Bond(4.0, date(2030, 1, 15), date(2030, 1, 15)))


def test_unknown_currency_convention_raises():
    """관행 표에 없는 통화는 오류(추정하지 않는다)."""
    with pytest.raises(ValueError):
        bond_for("JPY", 1.0, date(2025, 1, 1), date(2030, 1, 1))


def test_zero_coupon_price_and_yield():
    """무이표채: 가격 = 100/(1+y/2)^(2T), 경과이자 0, 가격→수익률 되돌리기."""
    z = Bond(0.0, date(2025, 1, 15), date(2030, 1, 15))
    assert price_from_yield(z, 4.0, z.issue) == pytest.approx(100 / 1.02**10)
    assert accrued_interest(z, date(2025, 5, 1)) == 0.0
    assert yield_from_price(z, 100 / 1.02**10, z.issue) == pytest.approx(4.0, abs=1e-9)


def test_negative_yield_round_trip():
    """음수 수익률(-1%): 가격이 액면 위로 올라가고 수익률이 되돌아온다."""
    p = price_from_yield(B, -1.0, B.issue)
    assert p > 100
    assert yield_from_price(B, p, B.issue) == pytest.approx(-1.0, abs=1e-9)


@pytest.mark.parametrize("price", [50.0, 150.0])
def test_extreme_price_round_trip(price):
    """극단 가격(50, 150)에서도 가격→수익률→가격이 되돌아온다."""
    st = date(2025, 3, 3)
    y = yield_from_price(B, price, st)
    assert price_from_yield(B, y, st) == pytest.approx(price, abs=1e-9)


def test_price_monotone_decreasing_in_yield():
    """수익률이 오르면 가격은 내린다(여러 수준에서 단조)."""
    ps = [price_from_yield(B, y, B.issue) for y in (-2, 0, 2, 4, 8, 15)]
    assert all(a > b for a, b in zip(ps, ps[1:]))


def test_dv01_positive_scales_with_face_and_matches_bump():
    """DV01은 양수, 액면에 비례, 1bp 이동 가격 변화(중심차분)와 일치."""
    d = dv01(B, 4.0, B.issue)
    assert d > 0 and dv01(B, 4.0, B.issue, face=5e6) == pytest.approx(d * 5e4)
    bump = price_from_yield(B, 3.995, B.issue) - price_from_yield(B, 4.005, B.issue)
    assert d == pytest.approx(bump, rel=1e-4)


def test_zero_coupon_duration_is_maturity_and_convexity_positive():
    """무이표채의 수정 듀레이션 = 만기/(1+y/2), 볼록성 > 0."""
    z = Bond(0.0, date(2025, 1, 15), date(2030, 1, 15))
    assert mod_duration(z, 4.0, z.issue) == pytest.approx(5.0 / 1.02)
    assert convexity(z, 4.0, z.issue) > 0


def test_settlement_amount_on_coupon_date_has_no_accrued():
    """지급일 당일 결제 금액 = 가격 × 액면/100 (경과이자 0)."""
    assert settlement_amount(B, 99.0, date(2025, 7, 15), face=1e6) == pytest.approx(990000.0)


def test_eur_act_act_accrued_half_year():
    """EUR Act/Act 연 1회: 반년 경과이자는 쿠폰의 (실제일수/연일수) 비율."""
    e = bond_for("EUR", 3.0, date(2025, 1, 1), date(2030, 1, 1))
    assert accrued_interest(e, date(2025, 7, 1)) == pytest.approx(3.0 * 181 / 365)


def test_interp_flat_ends_and_nan_dropped():
    """보간: 양 끝 밖은 끝값으로 평평(선형·단조3차 모두), NaN 점은 무시."""
    assert list(linear([1, 2], [1, 3], [0, 3])) == [1.0, 3.0]
    assert list(monotone_cubic([1, 2, 3], [1, 2, 4], [0, 5])) == [1.0, 4.0]
    assert par_yield({1: 3.0, 2: float("nan"), 10: 4.0}, 5.5) == pytest.approx(3.5)


def test_interp_unsorted_input_and_two_points():
    """입력 순서가 뒤섞여도 정렬해 보간하고, 두 점뿐이면 단조3차가 선형으로 폴백."""
    assert float(monotone_cubic([3, 1, 2], [4, 1, 2], 2.5)) == pytest.approx(2.9375)
    assert float(monotone_cubic([1, 2], [1, 3], 1.5)) == pytest.approx(2.0)


def test_monotone_cubic_stays_within_data_range():
    """단조 3차: 단조 증가 자료에서 값이 자료 범위를 넘거나 거꾸로 가지 않는다."""
    xs, ys = [0.5, 1, 2, 5, 10, 30], [1.0, 1.1, 1.2, 4.0, 4.1, 4.2]
    grid = np.linspace(0.5, 30, 200)
    v = monotone_cubic(xs, ys, grid)
    assert v.min() >= 1.0 - 1e-12 and v.max() <= 4.2 + 1e-12 and np.all(np.diff(v) >= -1e-12)


def test_interpolate_unknown_method_raises():
    """모르는 보간 이름은 오류."""
    with pytest.raises(ValueError):
        interpolate([1, 2], [1, 2], 1.5, "spline")


def test_g_spread_and_par_yield_flat_ends():
    """G-spread: 곡선 끝 밖 만기는 끝 값 기준, 곡선과 같으면 0."""
    pts = {1: 3.0, 10: 4.0}
    assert par_yield(pts, 0.1) == 3.0 and par_yield(pts, 30) == 4.0
    assert g_spread(4.0, pts, 30) == pytest.approx(0.0)
    assert g_spread(4.5, pts, 5.5) == pytest.approx(100.0)


def test_z_spread_zero_on_curve_and_roundtrip():
    """평평한 4% par 커브 위의 4% 쿠폰 채권(가격 100)은 Z-spread 0, z=123bp로 값매김하면 123을 되찾는다."""
    c = bootstrap(FLAT, B.issue, B.maturity)
    assert z_spread(B, 100.0, B.issue, c) == pytest.approx(0.0, abs=1e-6)
    p = z_price(B, 123.0, B.issue, c)
    assert z_spread(B, p, B.issue, c) == pytest.approx(123.0, abs=1e-6)


def test_z_spread_negative_and_spread_duration_positive():
    """가격이 높으면 Z-spread 음수, 스프레드 듀레이션은 양수."""
    c = bootstrap(FLAT, B.issue, B.maturity)
    assert z_spread(B, 105.0, B.issue, c) < 0
    assert spread_duration(B, 50.0, B.issue, c) > 0


def test_curve_with_missing_tenors_still_bootstraps():
    """만기 점이 드문 곡선(0.5·30년 두 점)도 부트스트랩되어 할인계수가 1보다 작고 감소."""
    c = bootstrap({0.5: 3.0, 30.0: 5.0}, date(2025, 1, 15), date(2040, 1, 15))
    dfs = [c.df(d) for d in c.node_dates[:20]]
    assert all(0 < x < 1 for x in dfs) and all(a > b for a, b in zip(dfs, dfs[1:]))


def test_zero_curve_date_bounds():
    """제로 커브: 기준일 이전 날짜는 오류, 기준일 DF는 1, 기준일의 제로 금리는 오류."""
    c = bootstrap(FLAT, B.issue, B.maturity)
    assert c.df(B.issue) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        c.df(date(2025, 1, 1))
    with pytest.raises(ValueError):
        c.zero_rate(B.issue)


def test_dirty_equals_clean_plus_accrued_on_odd_date():
    """임의 결제일에서 더티 = 깨끗한 가격 + 경과이자."""
    st = date(2026, 4, 20)
    assert dirty_price(B, 3.7, st) == pytest.approx(price_from_yield(B, 3.7, st) + accrued_interest(B, st))
