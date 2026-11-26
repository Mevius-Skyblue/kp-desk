"""Page ①: bond calculator. Inputs -> app.lib.calc.calculate (src/bond engine as is) -> results table."""

from datetime import date

import pandas as pd
import streamlit as st

from app.i18n import t
from app.lib import data as D
from app.lib import ui
from app.lib.calc import SPREAD_CONVENTIONS, CalcInputError, calculate, defaults
from src.bond.pricing import CONVENTIONS

MIN_D, MAX_D = date(1990, 1, 1), date(2100, 12, 31)

st.title(t("a_calc_title"))
st.markdown(t("a_calc_intro"))

asof_txt = D.asof()
asof = date.fromisoformat(asof_txt) if asof_txt else date.today()
dflt = defaults(asof)
try:
    points = D.curve_points()
    curve_df = D.read_curve()
except D.DataError:
    points, curve_df = {}, None

c1, c2, c3 = st.columns(3)
with c1:
    conv = st.selectbox(t("a_calc_conv"), options=list(CONVENTIONS), key=ui.wkey("calc_conv"),
                        format_func=ui.labels(CONVENTIONS, lambda v: t(f"a_conv_{v}")))
    coupon = st.number_input(t("a_calc_coupon"), min_value=0.0, max_value=30.0, value=dflt["coupon"], step=0.125,
                             format="%.3f", key="calc_coupon")
    face = st.number_input(t("a_calc_face"), min_value=1.0, value=dflt["face"], step=100_000.0, format="%.0f", key="calc_face")
with c2:
    issue = st.date_input(t("a_calc_issue"), value=dflt["issue"], min_value=MIN_D, max_value=MAX_D, key="calc_issue")
    maturity = st.date_input(t("a_calc_maturity"), value=dflt["maturity"], min_value=MIN_D, max_value=MAX_D, key="calc_maturity")
    settle = st.date_input(t("a_calc_settle"), value=dflt["settle"], min_value=MIN_D, max_value=MAX_D, key="calc_settle")
with c3:
    mode = st.radio(t("a_calc_input_mode"), options=["yield", "price"], key=ui.wkey("calc_mode"),
                    format_func=ui.labels(["yield", "price"],
                                          lambda v: t("a_calc_by_yield") if v == "yield" else t("a_calc_by_price")))
    if mode == "yield":
        y_in = st.number_input(t("a_calc_yield"), min_value=-5.0, max_value=50.0, value=dflt["yield_pct"], step=0.01,
                               format="%.4f", key="calc_yield")
        p_in = None
    else:
        p_in = st.number_input(t("a_calc_price"), min_value=1.0, max_value=300.0, value=dflt["clean_price"], step=0.01,
                               format="%.4f", key="calc_price")
        y_in = None

try:
    r = calculate(conv, coupon, issue, maturity, settle, face, yield_pct=y_in, clean_price=p_in, curve_points=points)
except CalcInputError as e:
    st.error(t("a_calc_err_dates") if e.args and e.args[0] == "dates" else t("a_calc_err_generic"))
    st.stop()
except (ValueError, ZeroDivisionError, OverflowError):
    st.error(t("a_calc_err_generic"))
    st.stop()

rows = [
    ("a_res_clean", ui.num(r["clean"], 6)), ("a_res_dirty", ui.num(r["dirty"], 6)), ("a_res_yield", ui.num(r["yield_pct"], 6)),
    ("a_res_accrued", ui.num(r["accrued"], 6)), ("a_res_settle_amt", ui.num(r["settle_amount"], 2, sep=True)),
    ("a_res_mac", ui.num(r["mac_duration"], 4)), ("a_res_mod", ui.num(r["mod_duration"], 4)),
    ("a_res_convexity", ui.num(r["convexity"], 4)), ("a_res_dv01", ui.num(r["dv01"], 2, sep=True)),
    ("a_res_tenor", ui.num(r["tenor_years"], 4)),
]
if r["g_spread_bp"] is not None:
    rows += [("a_res_ust_par", ui.num(r["ust_par_pct"], 4)), ("a_res_g", ui.num(r["g_spread_bp"], 2)),
             ("a_res_z", ui.num(r["z_spread_bp"], 2))]

st.subheader(t("a_calc_results"))
st.dataframe(pd.DataFrame({t("a_col_item"): [t(k) for k, _ in rows], t("a_col_value"): [v for _, v in rows]}),
             hide_index=True, width="stretch")
if conv not in SPREAD_CONVENTIONS:
    st.caption(t("a_calc_spread_usd_only"))
elif not points:
    st.caption(t("a_calc_no_curve"))
st.caption(t("a_calc_curve_note"))
st.caption(t("a_calc_engine_note"))
if curve_df is not None:
    with st.expander(t("a_calc_curve_show")):
        st.dataframe(curve_df.rename(columns={"tenor": t("a_curve_tenor"), "tenor_years": t("a_curve_years"),
                                              "yield_pct": t("a_curve_yield")}), hide_index=True)
