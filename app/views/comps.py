"""Page ②: comparable deals from app/data/deals.csv (snapshot columns only), filters, source as a link column.

U2 (config/public.yaml fixes U2-1 B): the five filters sit in one bordered box, each behind a small button whose label
summarises the selection ('Senior unsecured +2'), with the matching count and a reset button on top; the chart hover shows
issuer, issue date, tenor, spread, spread basis and sample tier; the source column shows the page ③ badge text (same
rule, ui.source_kind / ui.source_label) right after the issuer; less used columns behind a 'More columns' switch."""

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from app.i18n import current_lang, t, t_or
from app.lib import data as D
from app.lib import look, ui
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

FILTERS = ("comps_nature", "comps_type", "comps_tier", "comps_bucket")  # language-scoped multiselects (ui.wkey)
tier_default = [x for x in TIER_DEFAULT if x in tiers] or tiers  # fixes R3-10: C (estimated currency) is off by default
SPEC = {  # name -> (title key, options, default, option label, short label for the summary on the button)
    "comps_nature": ("a_f_nature", natures, nature_default, ui.labels(natures, lambda v: t_or(f"a_nature_{v}", v)), None),
    "comps_type": ("a_f_type", types, types, ui.labels(types, lambda v: t_or(f"a_type_{v}", v)), None),
    "comps_tier": ("a_f_tier", tiers, tier_default, ui.labels(tiers, lambda v: t_or(f"a_tier_{v}", v)), str),  # 'A', not the long text
    "comps_bucket": ("a_f_tenor", buckets, buckets, ui.labels(buckets, t), None),
}


def reset_filters() -> None:
    """[Reset]: back to the default filters (selections of both languages, the kept ids and the period are dropped)."""
    ui.forget(*FILTERS)
    st.session_state.pop("comps_period", None)


sel = {}
with st.container(border=True, key="kpd_card_comps_filters"):
    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center", key="kpd_fhead"):
        count_slot = st.empty()  # filled once the rows are filtered (below)
        st.button(t("a_f_reset"), key="comps_reset", on_click=reset_filters)
    with st.container(horizontal=True, gap="small", key="kpd_frow"):  # wraps to more lines on a phone
        for name, (title, options, default, fn, short) in SPEC.items():
            summ = ui.pick_summary(ui.current(name, options, default), options, short or fn)
            with st.popover(t("a_f_pop", name=t(title), value=summ), key=f"{name}_pop"):
                sel[name] = st.multiselect(t(title), options=options, default=ui.kept(name, options, default),
                                           key=ui.wkey(name), format_func=fn)
        p_now = st.session_state.get("comps_period", (d_min, d_max))
        p_lo, p_hi = (p_now[0], p_now[-1]) if isinstance(p_now, (tuple, list)) and p_now else (d_min, d_max)
        with st.popover(t("a_f_pop", name=t("a_f_period"), value=t("a_f_period_val", lo=p_lo, hi=p_hi)),
                        key="comps_period_pop"):
            period = st.date_input(t("a_f_period"), value=(d_min, d_max), min_value=d_min, max_value=d_max,
                                   key="comps_period")
sel_nature, sel_type, sel_tier, sel_bucket = (sel[n] for n in FILTERS)

# filters kept as codes across a language switch (fixes U1-2 C: each language has its own widget, see ui.wkey / ui.kept)
for _name in FILTERS:
    ui.keep(_name, sel[_name])
lo, hi = (period[0], period[-1]) if isinstance(period, (tuple, list)) and period else (d_min, d_max)
m = (deals["bond_nature"].isin(sel_nature) & deals["issuer_type"].isin(sel_type) & deals["sample_tier"].isin(sel_tier) & deals["bucket"].isin(sel_bucket)
     & deals["issue_date"].map(lambda d: d is None or pd.isna(d) or lo <= d <= hi))  # no issue date: kept (audit A9-3)
view = deals[m].sort_values(["issue_date", "deal_key"], ascending=[False, True])
count_slot.markdown(look.el("div", {"class": "kpd-count"}, look.txt(t("a_f_count", n=len(view)))), unsafe_allow_html=True)
st.caption(t("a_comps_nature_note"))
st.caption(t("a_comps_tier_note"))
if view.empty:
    st.info(t("a_comps_empty"))
else:
    name_col = "issuer_name_ko" if current_lang() == "ko" else "issuer_name_en"
    type_lbl = view["issuer_type"].map(lambda v: t_or(f"a_type_{v}", str(v)))
    # ---------------- chart (fixes R3-9, R3-10): tenor x representative spread, colour = issuer type, current filters.
    # altair without .interactive(): no wheel zoom / pan, so the page scroll is not captured by the chart. x fixed 0-30 years
    # (points outside are clipped). Legend (fixes U1-2 B6): drawn as HTML under the chart, because the chart's own two-column
    # legend ran off a 390px screen in English; the colours are given explicitly (present types in sorted order -> the theme
    # palette, as the chart did by default) so the HTML legend matches.
    st.subheader(t("a_chart_title"))
    basis_lbl = view["rep_spread_basis"].map(lambda v: t_or(f"a_basis_{v}", "" if pd.isna(v) else str(v)))
    chart = pd.DataFrame({"x": view["tenor_years"].astype(float), "y": view["rep_spread_bp"].astype(float),
                          "kind": type_lbl, "who": view[name_col], "issued": ui.date_col(view["issue_date"]),
                          "basis": basis_lbl, "tier": view["sample_tier"].fillna(t("a_na"))}).dropna(subset=["x", "y"])
    kinds = sorted(chart["kind"].dropna().unique().tolist())
    colors = {k: look.CHART_COLORS[i % len(look.CHART_COLORS)] for i, k in enumerate(kinds)}
    fig = (
        alt.Chart(chart)
        .mark_circle(size=56, opacity=0.8, clip=True)
        .encode(
            x=alt.X("x:Q", title=t("a_col_tenor"), scale=alt.Scale(domain=[0, 30], nice=False)),
            y=alt.Y("y:Q", title=t("a_col_spread")),
            color=alt.Color("kind:N", title=t("a_col_type"), legend=None,
                            scale=alt.Scale(domain=kinds, range=[colors[k] for k in kinds])),
            tooltip=[alt.Tooltip("who:N", title=t("a_col_issuer")), alt.Tooltip("issued:N", title=t("a_col_issue_date")),
                     alt.Tooltip("x:Q", title=t("a_col_tenor"), format=".2f"),
                     alt.Tooltip("y:Q", title=t("a_col_spread"), format=".1f"),
                     alt.Tooltip("basis:N", title=t("a_col_basis")), alt.Tooltip("tier:N", title=t("a_col_tier"))],
        )
        .properties(height=360)
    )
    st.altair_chart(fig, width="stretch")
    st.markdown(look.legend(t("a_col_type"), [(k, colors[k]) for k in kinds]), unsafe_allow_html=True)
    st.caption(t("a_chart_note"))
    # ---------------- table (fixes R3-9, R3-10, U2-1 B): issuer, source badge text, then the main columns; the rest behind
    # 'More columns'. Fixed decimals, empty = '–'. The source cell keeps the URL (link target, sort key) and shows the
    # page ③ badge text through the Styler format, in the ③ badge colours (a table cell cannot hold an HTML badge).
    st.subheader(t("a_comps_table"))
    src = t("a_col_source")
    out = pd.DataFrame({
        t("a_col_issuer"): view[name_col].tolist(),
        src: view["source_url"].tolist(),
        t("a_col_nature"): view["bond_nature"].map(lambda v: t_or(f"a_nature_{v}", "" if pd.isna(v) else str(v))).tolist(),
        t("a_col_type"): type_lbl.tolist(),
        t("a_col_issue_date"): ui.date_col(view["issue_date"]),
        t("a_col_tenor"): ui.sortable_text_col(view["tenor_years"], ui.DEC["years"]),
        t("a_col_spread"): view["rep_spread_bp"].astype(float).round(ui.DEC["bp"]).tolist(),
        t("a_col_basis"): basis_lbl.tolist(),
        t("a_col_tier"): view["sample_tier"].tolist(),
        t("a_col_ccy"): view["currency"].fillna(t("a_na")).tolist(),
        t("a_col_coupon"): ui.sortable_text_col(view["coupon_pct"], ui.DEC["pct"]),
        t("a_col_yield"): ui.sortable_text_col(view["reoffer_yield_pct"], ui.DEC["pct"]),
        t("a_col_maturity"): ui.date_col(view["maturity"]),
        t("a_col_rating"): view["rating_bucket"].map(rating_label).tolist(),
        t("a_col_key"): view["deal_key"].tolist(),
    })
    base = [t(k) for k in ("a_col_issuer", "a_col_source", "a_col_nature", "a_col_type", "a_col_issue_date", "a_col_tenor",
                           "a_col_spread", "a_col_basis", "a_col_tier")]
    more = [t(k) for k in ("a_col_ccy", "a_col_coupon", "a_col_yield", "a_col_maturity", "a_col_rating")]
    show_more = st.toggle(t("a_f_more_cols"), key="comps_more_cols")
    shown = base + more if show_more else base  # the stable key stays in the CSV, not on screen
    styled = out.style.format({src: ui.source_label}).map(lambda u: look.SRC_CELL.get(ui.source_kind(u), ""), subset=[src])
    # tenor / coupon / yield: equal-width text so '–' shows and a header click still sorts in numeric order (ui.sortable_
    # text_col); the spread has no empty cell and stays a number column
    num_right = {t(k): st.column_config.TextColumn(alignment="right") for k in ("a_col_tenor", "a_col_coupon", "a_col_yield")}
    st.dataframe(styled, hide_index=True, width="stretch", column_order=shown, column_config={
        **num_right,
        t("a_col_spread"): st.column_config.NumberColumn(format="%.1f"),
        t("a_col_issuer"): st.column_config.TextColumn(width="medium", pinned=True),
        t("a_col_ccy"): st.column_config.TextColumn(width="small"),
        t("a_col_tier"): st.column_config.TextColumn(width="small"),
        src: st.column_config.LinkColumn(src, width="small"),
    })
st.caption(t("a_comps_coupon_note"))
