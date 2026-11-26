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

from app.i18n import init_lang, t  # noqa: E402
from app.lib import look, ui  # noqa: E402

init_lang()
st.set_page_config(page_title=t("a_app_title"), layout="wide")
st.html(look.css())  # U1 style sheet (config/public.yaml fixes U1-1), once per run for every page
ui.top_bar()  # as-of date + language switch, top right

PAGES = [  # (file, title key, url path)
    ("views/home.py", "a_nav_home", "home"),
    ("views/calculator.py", "a_nav_calc", "calculator"),
    ("views/comps.py", "a_nav_comps", "comps"),
    ("views/fair_spread.py", "a_nav_fair", "fair-spread"),
    ("views/validation.py", "a_nav_valid", "validation"),
]

nav = st.navigation([st.Page(f, title=t(k), url_path=u, default=(i == 0)) for i, (f, k, u) in enumerate(PAGES)])
nav.run()
ui.footer()
