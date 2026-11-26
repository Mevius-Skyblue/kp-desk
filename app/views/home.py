"""Home page: what the app answers, the four pages, what is not included, links to the public documents."""

import streamlit as st

from app.i18n import t
from app.lib import ui

st.title(t("a_home_title"))
st.markdown(t("a_app_tagline"))
st.markdown(t("a_home_intro"))
st.subheader(t("a_home_pages"))
for k in ("a_home_calc", "a_home_comps", "a_home_fair", "a_home_valid"):
    st.markdown(f"- {t(k)}")
st.info(t("a_home_scope"))
st.subheader(t("a_home_docs"))
for k in ui.DOCS:
    st.markdown(f"- [{t(k)}]({ui.doc_url(k)})")
