"""Page ②: comparable deals from app/data/deals.csv (snapshot columns only), filters, source as a link column."""

from datetime import date

import pandas as pd
import streamlit as st

from app.i18n import current_lang, t, t_or
from app.lib import data as D
from app.lib import ui
from app.lib.keys import BUCKETS, TIER_ORDER


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
dates = [d for d in deals["issue_date"].dropna()]
d_min, d_max = (min(dates), max(dates)) if dates else (date(2000, 1, 1), date.today())

f1, f2, f3, f4 = st.columns(4)
with f1:
    sel_type = st.multiselect(t("a_f_type"), options=types, default=types, key=ui.wkey("comps_type"),
                              format_func=ui.labels(types, lambda v: t_or(f"a_type_{v}", v)))
with f2:
    sel_tier = st.multiselect(t("a_f_tier"), options=tiers, default=tiers, key=ui.wkey("comps_tier"),
                              format_func=ui.labels(tiers, lambda v: t_or(f"a_tier_{v}", v)))
with f3:
    sel_bucket = st.multiselect(t("a_f_tenor"), options=buckets, default=buckets, key=ui.wkey("comps_bucket"),
                                format_func=ui.labels(buckets, t))
with f4:
    period = st.date_input(t("a_f_period"), value=(d_min, d_max), min_value=d_min, max_value=d_max, key="comps_period")

lo, hi = (period[0], period[-1]) if isinstance(period, (tuple, list)) and period else (d_min, d_max)
m = (deals["issuer_type"].isin(sel_type) & deals["sample_tier"].isin(sel_tier) & deals["bucket"].isin(sel_bucket)
     & deals["issue_date"].map(lambda d: d is None or pd.isna(d) or lo <= d <= hi))  # no issue date: kept (audit A9-3)
view = deals[m].sort_values(["issue_date", "deal_key"], ascending=[False, True])

st.caption(t("a_comps_count", n=len(view)))
if view.empty:
    st.info(t("a_comps_empty"))
else:
    name_col = "issuer_name_ko" if current_lang() == "ko" else "issuer_name_en"
    out = pd.DataFrame({
        t("a_col_issuer"): view[name_col],
        t("a_col_type"): view["issuer_type"].map(lambda v: t_or(f"a_type_{v}", str(v))),
        t("a_col_issue_date"): view["issue_date"],
        t("a_col_maturity"): view["maturity"],
        t("a_col_tenor"): view["tenor_years"].round(2),
        t("a_col_ccy"): view["currency"],
        t("a_col_coupon"): view["coupon_pct"],
        t("a_col_yield"): view["reoffer_yield_pct"],
        t("a_col_spread"): view["rep_spread_bp"].round(1),
        t("a_col_basis"): view["rep_spread_basis"].map(lambda v: t_or(f"a_basis_{v}", "" if pd.isna(v) else str(v))),
        t("a_col_tier"): view["sample_tier"],
        t("a_col_rating"): view["rating_bucket"].map(rating_label),
        t("a_col_source"): view["source_url"],
        t("a_col_key"): view["deal_key"],
    })
    st.dataframe(out, hide_index=True, width="stretch",
                 column_config={t("a_col_source"): st.column_config.LinkColumn(t("a_col_source"),
                                                                              display_text=t("a_source_link"))})
st.caption(t("a_comps_coupon_note"))
