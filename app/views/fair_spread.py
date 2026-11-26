"""Page ③: fair spread range lookup from app/data/fair_spread.csv (public mode N0 only) + the scorecard on the same page."""

import pandas as pd
import streamlit as st

from app.i18n import current_lang, t
from app.lib import data as D
from app.lib import ui

st.title(t("a_fair_title"))
st.warning(t("a_fair_wording"))
st.markdown(t("a_fair_intro"))
try:
    fair = D.read_fair()
    sc = D.read_scorecard()
except D.DataError as e:
    ui.data_error(e)

name_col = "issuer_name_ko" if current_lang() == "ko" else "issuer_name_en"
issuers = fair.drop_duplicates("issuer_id").sort_values(name_col)
names = dict(zip(issuers["issuer_id"], issuers[name_col]))
# Default selection: the first of the published sample issuers (samples/ memos) that is in the snapshot, else the first row.
SAMPLE_ISSUERS = ("posco_holdings", "kb_bank", "kexim")
opts = list(names)
default_idx = next((opts.index(s) for s in SAMPLE_ISSUERS if s in names), 0)
c1, c2 = st.columns(2)
with c1:
    iid = st.selectbox(t("a_fair_issuer"), options=opts, index=default_idx, key=ui.wkey("fair_issuer"),
                       format_func=ui.labels(names, lambda v: str(names[v])))
tenors = sorted(fair.loc[fair["issuer_id"] == iid, "tenor_years"].dropna().unique().tolist())
with c2:
    tenor = st.selectbox(t("a_fair_tenor"), options=tenors, key="fair_tenor",
                         format_func=ui.labels(tenors, lambda v: ui.num(v, 0)))

row = fair[(fair["issuer_id"] == iid) & (fair["tenor_years"] == tenor)]
if row.empty or pd.isna(row.iloc[0]["point_bp"]):
    st.info(t("a_fair_none"))
else:
    r = row.iloc[0]
    m1, m2, m3 = st.columns(3)
    m1.metric(t("a_fair_point"), t("a_bp", v=ui.num(r["point_bp"], 1)))
    m2.metric(t("a_fair_low"), t("a_bp", v=ui.num(r["low_bp"], 1)))
    m3.metric(t("a_fair_high"), t("a_bp", v=ui.num(r["high_bp"], 1)))
    lvl = r["level"]
    lvl_txt = t(f"a_level_{int(lvl)}") if pd.notna(lvl) and int(lvl) in (1, 2, 3) else t("a_na")
    st.markdown(f"- {t('a_fair_level')}: {lvl_txt}\n- {t('a_fair_ncomps')}: {ui.num(r['n_comps'], 0)}")
st.caption(t("a_fair_tenor_note"))
st.caption(t("a_fair_range_note"))

# ---------------- scorecard (public mode): numbers from scorecard.json, labels from i18n
st.subheader(t("a_sc_title"))
st.markdown(t("a_sc_summary"))
try:
    dev = {k: D.item(sc, k) for k in ("dev_n", "dev_n0_mae", "dev_p_mae", "dev_p_diff", "dev_p_ci")}
    ho = {k: D.item(sc, k) for k in ("ho_n", "ho_n0_mae", "ho_p_mae", "ho_p_diff", "ho_p_ci", "ho_n0_median")}
except D.DataError as e:
    ui.data_error(e)
table = pd.DataFrame({
    t("a_sc_period"): [t("a_sc_dev"), t("a_sc_holdout")],
    t("a_sc_n"): [dev["dev_n"]["value"], ho["ho_n"]["value"]],
    t("a_sc_mae_n0"): [dev["dev_n0_mae"]["value"], ho["ho_n0_mae"]["value"]],
    t("a_sc_mae_rule"): [dev["dev_p_mae"]["value"], ho["ho_p_mae"]["value"]],
    t("a_sc_diff"): [dev["dev_p_diff"]["value"], ho["ho_p_diff"]["value"]],
    t("a_sc_ci"): [dev["dev_p_ci"]["value"], ho["ho_p_ci"]["value"]],
    t("a_sc_verdict"): [t("a_sc_not_better"), t("a_sc_not_better")],
}).astype(str)
st.dataframe(table, hide_index=True, width="stretch")
st.markdown(t("a_sc_median", v=ho["ho_n0_median"]["value"]))
st.caption(t("a_sc_method"))
for it in (dev["dev_n0_mae"], ho["ho_n0_mae"]):
    st.caption(t("a_sc_source", path=it.get("path", "?"), commit=it.get("commit", "?")))
