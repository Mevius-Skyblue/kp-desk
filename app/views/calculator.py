"""Page ①: bond calculator. Inputs -> app.lib.calc.calculate (src/bond engine as is) -> number cards + results table +
cash-flow chart (fixes U2-1 A: the cards show the table's own texts; the chart takes the engine's cash_flows as is)."""

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from app.i18n import t
from app.lib import data as D
from app.lib import look, ui
from app.lib.calc import SPREAD_CONVENTIONS, CalcInputError, calculate, cash_flow_rows, defaults
from src.bond.pricing import CONVENTIONS

MIN_D, MAX_D = date(1990, 1, 1), date(2100, 12, 31)
ROW_PX = 35  # st.dataframe row height: the results table is sized to its rows, so it never scrolls inside (fixes U2-1 A)

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

inputs = st.container(border=True, key="kpd_card_calc_inputs")  # one input card, three columns as before (fixes U2-1 A)
inputs.markdown(look.head(look.icon("calc", size=18, width=2, box="kpd-ico-sm"), t("a_calc_inputs"), strong=True),
                unsafe_allow_html=True)
c1, c2, c3 = inputs.columns(3)
with c1:
    convs = list(CONVENTIONS)
    conv = st.selectbox(t("a_calc_conv"), options=convs, key=ui.wkey("calc_conv"),
                        index=convs.index(ui.kept("calc_conv", convs, convs[0])),
                        format_func=ui.labels(CONVENTIONS, lambda v: t(f"a_conv_{v}")))
    ui.keep("calc_conv", conv)  # kept as the convention code across a language switch (fixes U1-2 C)
    coupon = st.number_input(t("a_calc_coupon"), min_value=0.0, max_value=30.0, value=dflt["coupon"], step=0.125,
                             format="%.3f", key="calc_coupon")
    face = st.number_input(t("a_calc_face"), min_value=1.0, value=dflt["face"], step=100_000.0, format="%.0f", key="calc_face")
with c2:
    issue = st.date_input(t("a_calc_issue"), value=dflt["issue"], min_value=MIN_D, max_value=MAX_D, key="calc_issue")
    maturity = st.date_input(t("a_calc_maturity"), value=dflt["maturity"], min_value=MIN_D, max_value=MAX_D, key="calc_maturity")
    settle = st.date_input(t("a_calc_settle"), value=dflt["settle"], min_value=MIN_D, max_value=MAX_D, key="calc_settle")
with c3:
    modes = ["yield", "price"]
    mode = st.radio(t("a_calc_input_mode"), options=modes, key=ui.wkey("calc_mode"),
                    index=modes.index(ui.kept("calc_mode", modes, modes[0])),
                    format_func=ui.labels(modes, lambda v: t("a_calc_by_yield") if v == "yield" else t("a_calc_by_price")))
    ui.keep("calc_mode", mode)
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

# display decimals (fixes R3-9): price 4, yield % 3, bp 1, durations 3, money with thousands separators (values unchanged)
P, Y, B, Q = ui.DEC["price"], ui.DEC["pct"], ui.DEC["bp"], ui.DEC["dur"]
rows = [
    ("a_res_clean", ui.num(r["clean"], P, sep=True)), ("a_res_dirty", ui.num(r["dirty"], P, sep=True)),
    ("a_res_yield", ui.num(r["yield_pct"], Y)), ("a_res_accrued", ui.num(r["accrued"], P, sep=True)),
    ("a_res_settle_amt", ui.num(r["settle_amount"], 2, sep=True)),
    ("a_res_mac", ui.num(r["mac_duration"], Q)), ("a_res_mod", ui.num(r["mod_duration"], Q)),
    ("a_res_convexity", ui.num(r["convexity"], Q)), ("a_res_dv01", ui.num(r["dv01"], 2, sep=True)),
    ("a_res_tenor", ui.num(r["tenor_years"], ui.DEC["years"])),
]
if r["g_spread_bp"] is not None:
    rows += [("a_res_ust_par", ui.num(r["ust_par_pct"], Y)), ("a_res_g", ui.num(r["g_spread_bp"], B)),
             ("a_res_z", ui.num(r["z_spread_bp"], B))]

# number cards (fixes U2-1 A): the same texts as the table rows below (one source: `text`), spreads '–' when not applicable
text = dict(rows)
CARDS = [("tag", "a_card_clean", "a_res_clean", "a_unit_per100"), ("pct", "a_card_yield", "a_res_yield", "a_unit_pct"),
         ("clock", "a_card_mod", "a_res_mod", "a_unit_years"), ("delta", "a_card_dv01", "a_res_dv01", "a_unit_face"),
         ("gap", "a_card_g", "a_res_g", "a_unit_bp"), ("curve", "a_card_z", "a_res_z", "a_unit_bp")]
st.subheader(t("a_calc_results"))
st.markdown(look.grid(*(look.stat(ic, t(lab), text.get(row, t("a_na")), t(unit)) for ic, lab, row, unit in CARDS),
                      cls="kpd-grid6"), unsafe_allow_html=True)
st.dataframe(pd.DataFrame({t("a_col_item"): [t(k) for k, _ in rows], t("a_col_value"): [v for _, v in rows]}),
             hide_index=True, width="stretch", row_height=ROW_PX, height=(len(rows) + 1) * ROW_PX + 3)
if conv not in SPREAD_CONVENTIONS:
    st.caption(t("a_calc_spread_usd_only"))
elif not points:
    st.caption(t("a_calc_no_curve"))
st.caption(t("a_calc_curve_note"))
st.caption(t("a_calc_engine_note"))

# ---------------- cash flows after settlement (fixes U2-1 A): engine cash_flows / schedule / coupon_amount, per 100 face.
# Stacked bars per payment date (coupon below, principal above in another colour); the hover shows date, coupon, principal,
# total as text. Dates are text for the hover and UTC dates for the axis, so no browser time zone shifts a day.
flows = cash_flow_rows(conv, coupon, issue, maturity, settle)
lab_c, lab_p = t("a_cf_coupon"), t("a_cf_principal")
cf = pd.DataFrame({"d": [f["date"].isoformat() for f in flows],
                   "c": [ui.num(f["coupon"], P) for f in flows], "p": [ui.num(f["principal"], P) for f in flows],
                   "s": [ui.num(f["total"], P) for f in flows], "cv": [f["coupon"] for f in flows],
                   "pv": [f["principal"] for f in flows]})
bars = pd.concat([cf.assign(part=lab_c, v=cf["cv"], o=0), cf.assign(part=lab_p, v=cf["pv"], o=1)], ignore_index=True)
bars = bars[bars["v"] > 0]
st.subheader(t("a_cf_title"))
fig = (
    alt.Chart(bars)
    .mark_bar(size=max(2, min(20, int(260 / max(len(flows), 1)))))  # 30y semi-annual: 4px, fits a 390px phone (A12-R3)
    .encode(
        x=alt.X("d:T", title=t("a_cf_date"), scale=alt.Scale(type="utc"), axis=alt.Axis(format="%Y-%m")),
        y=alt.Y("v:Q", title=t("a_cf_amount"), stack="zero"),
        color=alt.Color("part:N", legend=None, scale=alt.Scale(domain=[lab_c, lab_p], range=[look.ACCENT, look.PRINCIPAL])),
        order=alt.Order("o:Q"),
        tooltip=[alt.Tooltip("d:N", title=t("a_cf_date")), alt.Tooltip("c:N", title=lab_c),
                 alt.Tooltip("p:N", title=lab_p), alt.Tooltip("s:N", title=t("a_cf_total"))],
    )
    .properties(height=260)
)
st.altair_chart(fig, width="stretch")
st.markdown(look.legend(t("a_cf_legend"), [(lab_c, look.ACCENT), (lab_p, look.PRINCIPAL)]), unsafe_allow_html=True)
st.caption(t("a_cf_note"))
if curve_df is not None:
    with st.expander(t("a_calc_curve_show")):
        st.dataframe(pd.DataFrame({t("a_curve_tenor"): curve_df["tenor"].fillna(t("a_na")).tolist(),
                                   t("a_curve_years"): ui.text_col(curve_df["tenor_years"], ui.DEC["years"]),
                                   t("a_curve_yield"): ui.text_col(curve_df["yield_pct"], ui.DEC["pct"])}), hide_index=True)
