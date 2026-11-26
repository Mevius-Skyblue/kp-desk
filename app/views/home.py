"""Home page: what the app answers, four glance cards, the four pages, what is not included, links to the public documents.

Card numbers come only from app/data/scorecard.json (report cells), the deals.csv row count and the as-of date.
"""

import streamlit as st

from app.i18n import t
from app.lib import data as D
from app.lib import ui

st.title(t("a_home_title"))
st.markdown(t("a_app_tagline"))
st.markdown(t("a_home_intro"))

# ---------------- glance cards (fixes R3-9); a missing snapshot file hides the card instead of stopping the page
st.subheader(t("a_home_glance"))
try:
    sc = D.read_scorecard()
    n_deals = len(D.read_deals())
    v = {k: str(D.item(sc, k)["value"]) for k in ("a1_total", "a1_gate_n", "a1_ref_n", "a1_mismatch", "ho_n0_mae",
                                                  "ho_p_diff", "ho_p_ci")}
    asof = sc.get("asof") or t("a_na")
except D.DataError:
    sc = None
cards = st.columns(4)
if sc is not None:
    with cards[0].container(border=True):
        st.metric(t("a_card_deals_title"), t("a_card_deals_value", n=f"{n_deals:,}"))
        st.caption(t("a_card_deals_note", asof=asof))
    with cards[1].container(border=True):
        st.metric(t("a_card_bond_title"), t("a_card_bond_value", total=v["a1_total"]))
        st.caption(t("a_card_bond_note", gate=v["a1_gate_n"], ref=v["a1_ref_n"], mismatch=v["a1_mismatch"]))
    with cards[2].container(border=True):
        st.metric(t("a_card_ho_title"), t("a_card_ho_value", mae=v["ho_n0_mae"]))
        st.caption(t("a_card_ho_note", diff=v["ho_p_diff"], ci=v["ho_p_ci"]))
with cards[3].container(border=True):
    st.metric(t("a_card_samples_title"), t("a_card_samples_value"))
    st.caption(t("a_card_samples_note"))
    st.page_link("views/validation.py", label=t("a_card_samples_link"))

st.subheader(t("a_home_pages"))
for k in ("a_home_calc", "a_home_comps", "a_home_fair", "a_home_valid"):
    st.markdown(f"- {t(k)}")
st.info(t("a_home_scope"))
st.subheader(t("a_home_docs"))
for k in ui.DOCS:
    st.markdown(f"- [{t(k)}]({ui.doc_url(k)})")
