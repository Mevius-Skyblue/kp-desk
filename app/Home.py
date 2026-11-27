"""KP Desk public app entry (config/public.yaml 5. app). Run: streamlit run app/Home.py  (Python 3.13)

Four pages + home, Korean / English toggle at the top right next to the as-of date (default Korean). Menu titles come from i18n through
st.navigation + st.Page(title=t(...)), so file names never show in the menu. Works from the bundle layout
(app/, src/bond/, app/data/, samples/) without any database.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from app.i18n import current_lang, init_lang, switch_keep_lang, t  # noqa: E402
from app.lib import look, ui  # noqa: E402

init_lang()
st.set_page_config(page_title=t("a_app_title"), layout="wide")
st.html(look.css())  # U1 style sheet (config/public.yaml fixes U1-1), once per run for every page
ui.top_bar()  # as-of date + language switch, top right

PAGES = [  # (file, title key, url path)
    ("views/home.py", "a_nav_home", "main"),  # default page: its address is always "/" (internal name only; "/home" = alias)
    ("views/calculator.py", "a_nav_calc", "calculator"),
    ("views/comps.py", "a_nav_comps", "comps"),
    ("views/fair_spread.py", "a_nav_fair", "fair-spread"),
    ("views/validation.py", "a_nav_valid", "validation"),
]

# Page menu (fixes U2-2 D5): Streamlit's own menu links cannot carry a query, so its menu is hidden and the pages are
# listed with st.page_link, whose address keeps ?lang=<current> (a link opened in a new tab shows the same language).
# A page link to the default page has no path of its own (its address becomes '?lang=..', relative to the current page),
# so the Home entry points to a hidden '/home' page that only switches to the home page in the same language.
pages = [st.Page(f, title=t(k), url_path=u, default=(i == 0)) for i, (f, k, u) in enumerate(PAGES)]


def _home_alias() -> None:
    switch_keep_lang(pages[0])


home_alias = st.Page(_home_alias, title=t("a_nav_home"), url_path="home", visibility="hidden")
nav = st.navigation(pages + [home_alias], position="hidden")
with st.sidebar:
    for pg in [home_alias] + pages[1:]:
        st.page_link(pg, query_params={"lang": current_lang()})
nav.run()
ui.footer()
