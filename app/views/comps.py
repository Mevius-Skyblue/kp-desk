"""Page ②: comparable deals from app/data/deals.csv (snapshot columns only), filters, source as a link column."""

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from app.i18n import current_lang, t, t_or
from app.lib import data as D
from app.lib import ui
from app.lib.keys import BUCKETS, NATURE_DEFAULT, NATURES, TIER_DEFAULT, TIER_ORDER


def tenor_bucket(x) -> str:
    """Tenor in years -> bucket key (upper bound included, e.g. exactly 5.0 -> 3-5)."""
    if x is None or pd.isna(x):
        return "a_tb_na"
    for k, lo, hi in BUCKETS:
        if lo < float(x) <= hi or (lo == 0.0 and float(x) <= hi):
            return k
    return "a_tb_na"


def rating_label(v) -> str:
    """Rating bucket code -> text; 'check_source' (covered-bond rating not shown as issuer rating) and none are translated."""
    if v is None or pd.isna(v) or str(v) in ("", "none"):
        return t("a_rating_none")
    if str(v) == "check_source":
        return t("a_rating_check_source")
    return str(v)


st.title(t("a_comps_title"))
st.markdown(t("a_comps_intro"))
try:
    deals = D.read_deals()
except D.DataError as e:
    ui.data_error(e)

deals["bucket"] = deals["tenor_years"].map(tenor_bucket)
types = sorted(deals["issuer_type"].dropna().unique().tolist())
tiers = [x for x in TIER_ORDER if x in set(deals["sample_tier"].dropna())] + sorted(
    set(deals["sample_tier"].dropna()) - set(TIER_ORDER))
buckets = [k for k, _, _ in BUCKETS] + ["a_tb_na"]
buckets = [k for k in buckets if k in set(deals["bucket"])]
# bond nature (fixes R3-8): known codes in fixed order, default = senior unsecured only (other natures can be switched on)
natures = [x for x in NATURES if x in set(deals["bond_nature"].dropna())] + sorted(
    set(deals["bond_nature"].dropna()) - set(NATURES))
nature_default = [x for x in NATURE_DEFAULT if x in natures] or natures
dates = [d for d in deals["issue_date"].dropna()]
d_min, d_max = (min(dates), max(dates)) if dates else (date(2000, 1, 1), date.today())

f0, f1, f2, f3, f4 = st.columns(5)
with f0:
    sel_nature = st.multiselect(t("a_f_nature"), options=natures, default=nature_default, key=ui.wkey("comps_nature"),
                                format_func=ui.labels(natures, lambda v: t_or(f"a_nature_{v}", v)))
with f1:
    sel_type = st.multiselect(t("a_f_type"), options=types, default=types, key=ui.wkey("comps_type"),
                              format_func=ui.labels(types, lambda v: t_or(f"a_type_{v}", v)))
with f2:
    tier_default = [x for x in TIER_DEFAULT if x in tiers] or tiers  # fixes R3-10: C (estimated currency) is off by default
    sel_tier = st.multiselect(t("a_f_tier"), options=tiers, default=tier_default, key=ui.wkey("comps_tier"),
                              format_func=ui.labels(tiers, lambda v: t_or(f"a_tier_{v}", v)))
with f3:
    sel_bucket = st.multiselect(t("a_f_tenor"), options=buckets, default=buckets, key=ui.wkey("comps_bucket"),
                                format_func=ui.labels(buckets, t))
with f4:
    period = st.date_input(t("a_f_period"), value=(d_min, d_max), min_value=d_min, max_value=d_max, key="comps_period")

lo, hi = (period[0], period[-1]) if isinstance(period, (tuple, list)) and period else (d_min, d_max)
m = (deals["bond_nature"].isin(sel_nature) & deals["issuer_type"].isin(sel_type) & deals["sample_tier"].isin(sel_tier) & deals["bucket"].isin(sel_bucket)
     & deals["issue_date"].map(lambda d: d is None or pd.isna(d) or lo <= d <= hi))  # no issue date: kept (audit A9-3)
view = deals[m].sort_values(["issue_date", "deal_key"], ascending=[False, True])

st.caption(t("a_comps_count", n=len(view)))
st.caption(t("a_comps_nature_note"))
st.caption(t("a_comps_tier_note"))
if view.empty:
    st.info(t("a_comps_empty"))
else:
    name_col = "issuer_name_ko" if current_lang() == "ko" else "issuer_name_en"
    type_lbl = view["issuer_type"].map(lambda v: t_or(f"a_type_{v}", str(v)))
    # ---------------- chart (fixes R3-9, R3-10): tenor x representative spread, colour = issuer type, current filters.
    # altair without .interactive(): no wheel zoom / pan, so the page scroll is not captured by the chart. x fixed 0-30 years
    # (points outside are clipped), legend below the plot so a narrow screen does not cut it.
    st.subheader(t("a_chart_title"))
    chart = pd.DataFrame({"x": view["tenor_years"].astype(float), "y": view["rep_spread_bp"].astype(float),
                          "kind": type_lbl, "who": view[name_col]}).dropna(subset=["x", "y"])
    fig = (
        alt.Chart(chart)
        .mark_circle(size=56, opacity=0.8, clip=True)
        .encode(
            x=alt.X("x:Q", title=t("a_col_tenor"), scale=alt.Scale(domain=[0, 30], nice=False)),
            y=alt.Y("y:Q", title=t("a_col_spread")),
            color=alt.Color("kind:N", title=t("a_col_type"),
                            legend=alt.Legend(orient="bottom", direction="horizontal", columns=2, labelLimit=220)),
            tooltip=[alt.Tooltip("who:N", title=t("a_col_issuer")), alt.Tooltip("kind:N", title=t("a_col_type")),
                     alt.Tooltip("x:Q", title=t("a_col_tenor"), format=".2f"),
                     alt.Tooltip("y:Q", title=t("a_col_spread"), format=".1f")],
        )
        .properties(height=360)
    )
    st.altair_chart(fig, width="stretch")
    st.caption(t("a_chart_note"))
    # ---------------- table: important columns first; fixed decimals, empty = '–' (fixes R3-9, R3-10)
    st.subheader(t("a_comps_table"))
    out = pd.DataFrame({
        t("a_col_issuer"): view[name_col].tolist(),
        t("a_col_nature"): view["bond_nature"].map(lambda v: t_or(f"a_nature_{v}", "" if pd.isna(v) else str(v))).tolist(),
        t("a_col_type"): type_lbl.tolist(),
        t("a_col_issue_date"): ui.date_col(view["issue_date"]),
        t("a_col_tenor"): ui.sortable_text_col(view["tenor_years"], ui.DEC["years"]),
        t("a_col_spread"): view["rep_spread_bp"].astype(float).round(ui.DEC["bp"]).tolist(),
        t("a_col_basis"): view["rep_spread_basis"].map(lambda v: t_or(f"a_basis_{v}", "" if pd.isna(v) else str(v))).tolist(),
        t("a_col_ccy"): view["currency"].fillna(t("a_na")).tolist(),
        t("a_col_coupon"): ui.sortable_text_col(view["coupon_pct"], ui.DEC["pct"]),
        t("a_col_yield"): ui.sortable_text_col(view["reoffer_yield_pct"], ui.DEC["pct"]),
        t("a_col_maturity"): ui.date_col(view["maturity"]),
        t("a_col_tier"): view["sample_tier"].tolist(),
        t("a_col_rating"): view["rating_bucket"].map(rating_label).tolist(),
        t("a_col_source"): view["source_url"].tolist(),
        t("a_col_key"): view["deal_key"].tolist(),
    })
    shown = [c for c in out.columns if c != t("a_col_key")]  # the stable key stays in the CSV, not on screen
    # tenor / coupon / yield: equal-width text so '–' shows and a header click still sorts in numeric order (ui.sortable_
    # text_col); the spread has no empty cell and stays a number column
    num_right = {t(k): st.column_config.TextColumn(alignment="right") for k in ("a_col_tenor", "a_col_coupon", "a_col_yield")}
    st.dataframe(out, hide_index=True, width="stretch", column_order=shown, column_config={
        **num_right,
        t("a_col_spread"): st.column_config.NumberColumn(format="%.1f"),
        t("a_col_issuer"): st.column_config.TextColumn(width="medium", pinned=True),
        t("a_col_ccy"): st.column_config.TextColumn(width="small"),
        t("a_col_tier"): st.column_config.TextColumn(width="small"),
        t("a_col_source"): st.column_config.LinkColumn(t("a_col_source"), display_text=t("a_source_link"), width="small"),
    })
st.caption(t("a_comps_coupon_note"))
