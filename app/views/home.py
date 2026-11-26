"""Home page (config/public.yaml fixes U1-1): title + one line, four page tiles, four evidence cards, scope note.

Card numbers come only from app/data/scorecard.json (report cells), the deals.csv row count and simple ratios of those
cells for the bar lengths. The collected-deal count is not in the public documents, so the first card has no ratio bar.
"""

import streamlit as st

from app.i18n import t
from app.lib import data as D
from app.lib import look

st.title(t("a_home_title"))
st.markdown(t("a_home_intro"))

# ---------------- page tiles: icon + title + static preview + one line + 'Open' link inside the card
TILES = [  # (page file, title key = menu title, description key, icon, preview)
    ("views/calculator.py", "a_nav_calc", "a_tile_calc", "calc", "calc"),
    ("views/comps.py", "a_nav_comps", "a_tile_comps", "rows", "comps"),
    ("views/fair_spread.py", "a_nav_fair", "a_tile_fair", "range", "fair"),
    ("views/validation.py", "a_nav_valid", "a_tile_valid", "check", "valid"),
]
for col, (page, title_key, desc_key, ico, prev) in zip(st.columns(4), TILES):
    with col.container(key=f"kpd_card_tile_{ico}"):
        st.markdown(look.head(look.icon(ico), t(title_key), strong=True) + look.preview(prev)
                    + look.note(t(desc_key), cls="kpd-text"), unsafe_allow_html=True)
        st.page_link(page, label=t("a_open"))

# ---------------- evidence cards; a missing snapshot file hides the number cards instead of stopping the page
st.subheader(t("a_home_glance"))
cards = []
try:
    sc = D.read_scorecard()
    n_deals = len(D.read_deals())
    v = {k: str(D.item(sc, k)["value"]) for k in ("a1_total", "a1_mismatch", "ho_n", "ho_n0_mae", "ho_p_mae")}
except D.DataError:
    sc = None
if sc is not None:
    total = int(v["a1_total"])
    matched = total - int(v["a1_mismatch"])
    n0, pm = float(v["ho_n0_mae"]), float(v["ho_p_mae"])
    top = max(n0, pm)
    cards += [
        look.card(look.head(look.icon("db", box=None, size=18, width=2), t("a_card_deals_title")),
                  look.big(t("a_card_deals_value", n=f"{n_deals:,}")), look.note(t("a_g_deals_note"))),
        look.card(look.head(look.icon("ok", look.PASS, box=None, size=18, width=2), t("a_g_bond_title")),
                  look.big(t("a_g_match", n=f"{matched:,}", total=f"{total:,}")), look.bar(matched / total, "pass"),
                  look.note(t("a_g_bond_note"))),
        look.card(look.head(look.icon("bars", box=None, size=18, width=2), t("a_g_ho_title", n=v["ho_n"])),
                  look.big(t("a_similar")),
                  look.compare([(t("a_bar_base"), t("a_bp", v=v["ho_n0_mae"]), n0 / top, "base"),
                                (t("a_bar_model"), t("a_bp", v=v["ho_p_mae"]), pm / top, "accent")]),
                  look.note(t("a_g_ho_note"))),
    ]
cards.append(look.card(
    look.head(look.icon("file", box=None, size=18, width=2), t("a_g_samples_title")), look.big(t("a_card_samples_value")),
    look.badges(look.badge(t("a_fmt_pdf"), "pdf"), look.badge(t("a_fmt_xlsx"), "xlsx"), look.badge(t("a_badge_ko"), "lang"),
                look.badge(t("a_badge_en"), "lang")),
    look.note(t("a_g_samples_note"))))
st.markdown(look.grid(*cards), unsafe_allow_html=True)
st.caption(t("a_home_scope"))
