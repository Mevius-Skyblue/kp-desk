"""Page ③: fair spread range lookup from app/data/fair_spread.csv (public mode N0 only) + the scorecard on the same page.

U1 layout (config/public.yaml fixes U1-1): the wording as a small grey line, a result card with the point estimate, the range,
a grey chip with the number of comparable deals and a range bar, then the scorecard as error bars for both periods.
U1b (fixes U1-2 A): the comparable deals the engine used are read from app/data/fair_spread_comps.csv (deal keys only,
written by scripts/export_fair_comps.py from the engine's own list) and joined to deals.csv for spread, issue date and
source: dots on the range bar + a table. The list cannot be rebuilt from the public columns (the 18-month window uses the
pricing date, which is not public), which is why it is a file of its own. No file -> no dots, no table.
"""

import math

import pandas as pd
import streamlit as st

from app.i18n import current_lang, t
from app.lib import data as D
from app.lib import look, ui

SMALL_SAMPLE_N = 3  # 'small sample' below this many comparable deals = pre-registered memo rule DC3 (src/credit/memo.TH)
AXIS_STEP = 50.0  # range-bar axis rounded out to multiples of 50bp, the same axis for every issuer


st.title(t("a_fair_title"))
st.markdown(t("a_fair_intro"))
st.caption(t("a_fair_wording"))
try:
    fair = D.read_fair()
    sc = D.read_scorecard()
except D.DataError as e:
    ui.data_error(e)
comps = D.read_comps()  # optional file (None = missing)
deals = None
if comps is not None:
    try:
        deals = D.read_deals()
    except D.DataError:
        comps = None

name_col = "issuer_name_ko" if current_lang() == "ko" else "issuer_name_en"
issuers = fair.drop_duplicates("issuer_id").sort_values(name_col)
names = dict(zip(issuers["issuer_id"], issuers[name_col]))
# Default selection: the first of the published sample issuers (samples/ memos) that is in the snapshot, else the first row.
SAMPLE_ISSUERS = ("posco_holdings", "kb_bank", "kexim")
opts = list(names)
default_id = next((s for s in SAMPLE_ISSUERS if s in names), opts[0] if opts else None)
c1, c2 = st.columns(2)
with c1:  # the issuer is kept as its id across a language switch (fixes U1-2 C)
    iid = st.selectbox(t("a_fair_issuer"), options=opts, index=opts.index(ui.kept("fair_issuer", opts, default_id)),
                       key=ui.wkey("fair_issuer"), format_func=ui.labels(names, lambda v: str(names[v])))
ui.keep("fair_issuer", iid)
tenors = sorted(fair.loc[fair["issuer_id"] == iid, "tenor_years"].dropna().unique().tolist())
with c2:
    tenor = st.selectbox(t("a_fair_tenor"), options=tenors, key="fair_tenor",
                         format_func=ui.labels(tenors, lambda v: ui.num(v, 0)))

# comparable deals: deal keys of the file joined to deals.csv; every row of the file feeds the common axis
used = pd.DataFrame()
all_spreads: list[float] = []
if comps is not None:
    # the file's tenor_years is the fair_spread row key (renamed: deals.csv has its own tenor_years = the deal's tenor)
    joined = comps.rename(columns={"tenor_years": "row_tenor"}).merge(deals, on="deal_key", how="inner")
    all_spreads = joined["rep_spread_bp"].dropna().astype(float).tolist()
    used = joined[(joined["issuer_id"] == iid) & (joined["row_tenor"] == tenor)]
    used = used.sort_values(["issue_date", "deal_key"], ascending=[False, True], na_position="last", kind="stable")

row = fair[(fair["issuer_id"] == iid) & (fair["tenor_years"] == tenor)]
if row.empty or pd.isna(row.iloc[0]["point_bp"]):
    st.info(t("a_fair_none"))
else:
    r = row.iloc[0]
    n = int(r["n_comps"]) if pd.notna(r["n_comps"]) else 0
    chip = t("a_fair_chip_small" if n < SMALL_SAMPLE_N else "a_fair_chip", n=n)
    # axis: 0 (or the lowest range / comparable spread) .. the highest, over all rows, rounded out to 50bp (fixes U1-2)
    lo_axis = min(0.0, math.floor(min([float(fair["low_bp"].min())] + all_spreads) / AXIS_STEP) * AXIS_STEP)
    hi_axis = max(AXIS_STEP, math.ceil(max([float(fair["high_bp"].max())] + all_spreads) / AXIS_STEP) * AXIS_STEP)
    lvl = r["level"]
    lvl_txt = t(f"a_level_{int(lvl)}") if pd.notna(lvl) and int(lvl) in (1, 2, 3) else t("a_na")
    has_range = pd.notna(r["low_bp"]) and pd.notna(r["high_bp"])
    result = look.el("div", {"class": "kpd-result"},
                     look.el("span", {"class": "kpd-head"}, look.txt(t("a_fair_est"))),
                     look.big(t("a_bp", v=ui.num(r["point_bp"], 1)), cls="kpd-huge"),
                     look.el("span", {"class": "kpd-text"}, look.txt(t(
                         "a_fair_range_txt", low=ui.num(r["low_bp"], 1), high=ui.num(r["high_bp"], 1)))),
                     look.chip(chip))
    recs = used.to_dict("records")
    dots = [(float(x["rep_spread_bp"]), t("a_fair_dot_tip", issuer=str(x[name_col]), date=ui.date_col([x["issue_date"]])[0],
                                          v=ui.num(x["rep_spread_bp"], 1)))
            for x in recs if pd.notna(x["rep_spread_bp"])]
    parts = [result]
    if has_range:
        parts += [look.range_bar(float(r["low_bp"]), float(r["high_bp"]), float(r["point_bp"]), lo_axis, hi_axis,
                                 t("a_bp", v=f"{hi_axis:g}"), dots=dots),
                  look.note(t("a_fair_bar_legend_dots" if dots else "a_fair_bar_legend"))]
    parts.append(look.note(f"{t('a_fair_level')}: {lvl_txt}", cls="kpd-text"))
    st.markdown(look.card(*parts), unsafe_allow_html=True)
    if recs:  # table of the comparable deals used for this estimate (deals.csv cells only)
        src_txt = {"sec": t("a_src_sec"), "dart": t("a_src_dart"), "news": t("a_src_news")}
        rows = []
        for x in recs:
            kind = ui.source_kind(x["source_url"])
            rows.append([look.txt(x[name_col]), look.txt(ui.date_col([x["issue_date"]])[0]),
                         look.txt(ui.num(x["tenor_years"], 2)), look.txt(ui.num(x["rep_spread_bp"], 1)),
                         look.source_badge(kind, src_txt.get(kind, t("a_na")), x["source_url"] if kind else None)])
        head = [(t("a_col_issuer"), False), (t("a_col_issue_date"), False), (t("a_col_tenor"), True),
                (t("a_col_spread"), True), (t("a_col_source"), False)]
        st.markdown(look.card(look.head(look.icon("rows", size=18, width=2, box="kpd-ico-sm"), t("a_fair_comps_title"),
                                        strong=True),
                              look.note(t("a_fair_comps_note", level=lvl_txt)), look.table(head, rows)),
                    unsafe_allow_html=True)
st.caption(t("a_fair_tenor_note"))
st.caption(t("a_fair_range_note"))

# ---------------- scorecard (public mode): numbers from scorecard.json, labels from i18n
try:
    dev = {k: str(D.item(sc, k)["value"]) for k in ("dev_n", "dev_n0_mae", "dev_p_mae", "dev_p_diff", "dev_p_ci")}
    ho = {k: str(D.item(sc, k)["value"]) for k in ("ho_n", "ho_n0_mae", "ho_p_mae", "ho_p_diff", "ho_p_ci", "ho_n0_median")}
except D.DataError as e:
    ui.data_error(e)
top = max(float(dev["dev_n0_mae"]), float(dev["dev_p_mae"]), float(ho["ho_n0_mae"]), float(ho["ho_p_mae"]))


def period_card(label: str, n0: str, pm: str, diff: str, ci: str) -> str:
    """One period: baseline vs public-model mean absolute error bars (same scale for both periods) + difference line."""
    return look.card(look.note(label, cls="kpd-head"),
                     look.compare([(t("a_bar_base"), t("a_bp", v=n0), float(n0) / top, "base"),
                                   (t("a_bar_model"), t("a_bp", v=pm), float(pm) / top, "accent")]),
                     look.note(t("a_sc_diff_line", diff=diff, ci=ci)), cls="kpd-sub")


st.markdown(look.card(
    look.head(look.icon("bars", size=18, width=2, box="kpd-ico-sm"), t("a_sc_title"), strong=True),
    look.note(t("a_sc_summary"), cls="kpd-text"),
    look.grid(period_card(t("a_sc_card_dev", n=dev["dev_n"]), dev["dev_n0_mae"], dev["dev_p_mae"], dev["dev_p_diff"],
                          dev["dev_p_ci"]),
              period_card(t("a_sc_card_ho", n=ho["ho_n"]), ho["ho_n0_mae"], ho["ho_p_mae"], ho["ho_p_diff"], ho["ho_p_ci"]),
              cls="kpd-grid2"),
    look.note(t("a_sc_median", v=ho["ho_n0_median"]), cls="kpd-text"),
    look.note(t("a_sc_method")),
    look.link(t("a_more"), ui.doc_url("a_doc_valid", "a_anchor_model"))), unsafe_allow_html=True)
