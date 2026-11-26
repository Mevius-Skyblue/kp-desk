"""Shared UI pieces: language toggle, as-of line, data-error message, footer, number formatting, document links."""

from __future__ import annotations

import math

import streamlit as st

from app.i18n import LANGS, STATE_KEY, current_lang, init_lang, t
from app.lib import data as D
from app.lib import look

REPO_URL = "https://github.com/Mevius-Skyblue/kp-desk"
DOCS = {"a_doc_readme": ("README.md", "README_en.md"), "a_doc_method": ("docs/METHODOLOGY_ko.md", "docs/METHODOLOGY_en.md"),
        "a_doc_valid": ("docs/VALIDATION_ko.md", "docs/VALIDATION_en.md"),
        "a_doc_known": ("docs/KNOWN_ISSUES_ko.md", "docs/KNOWN_ISSUES_en.md"),
        "a_doc_data": ("docs/DATA_NOTICE_ko.md", "docs/DATA_NOTICE_en.md")}


def lang_toggle() -> None:
    """Korean / English switch at the top of every page (default Korean, kept in st.session_state). The label stays for
    screen readers but is not drawn (fixes U1-1: the switch sits at the top right next to the as-of date)."""
    init_lang()
    st.radio(t("a_lang_label"), options=list(LANGS), key=STATE_KEY, horizontal=True, label_visibility="collapsed",
             width="content", format_func=labels(LANGS, lambda v: t(f"a_lang_{v}")))


def top_bar() -> None:
    """As-of date + language switch, right-aligned at the top of the page body (the sidebar keeps the page menu)."""
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", key="kpd_top"):
        asof_line()
        lang_toggle()


def wkey(name: str) -> str:
    """Widget key that includes the language: a widget whose option labels are translated starts fresh after the
    language switch (otherwise the browser can keep showing the previous language's label of the selected option)."""
    return f"{name}_{current_lang()}"


KEEP_PREFIX = "keep_"  # session keys holding a widget's selection as language-free ids (config/public.yaml fixes U1-2 C)


def kept(name: str, options: list, fallback):
    """Selection to start a language-scoped widget with: the ids kept from the last run (any language) that are still
    options, else `fallback`. A list for a multiselect (kept ids filtered to the options), one id for a selectbox / radio.

    Why: wkey() gives each language its own widget, so the new language's widget is created fresh after a switch; it then
    starts from these kept ids instead of the defaults (A9-R17). The kept value is an id or code, never a translated label."""
    v = st.session_state.get(KEEP_PREFIX + name)
    if v is None:
        return fallback
    if isinstance(fallback, list):
        return [x for x in v if x in options]
    return v if v in options else fallback


def keep(name: str, value) -> None:
    """Store the widget's current selection (ids) for kept()."""
    st.session_state[KEEP_PREFIX + name] = list(value) if isinstance(value, (list, tuple)) else value


def labels(options, fn):
    """format_func for a widget: labels are computed now (in the script run, current language) and looked up later.
    A plain lambda would be called later outside the run by AppTest and then see the default language."""
    table = {o: fn(o) for o in options}
    return lambda v: table.get(v, str(v))


def asof_line() -> None:
    """'기준일 YYYY-MM-DD' / 'As of YYYY-MM-DD' from the snapshot."""
    a = D.asof()
    st.caption(t("a_asof", asof=a) if a else t("a_asof_unknown"), width="content")


def data_error(e: D.DataError) -> None:
    """Translated message for a missing / unreadable snapshot file, then stop the page."""
    name = e.args[0] if e.args else "?"
    st.warning(t("a_data_missing", name=name))
    st.stop()


def footer() -> None:
    """End of every page: the disclaimer once (small grey text), 'built with' and the public documents (fixes U1-1)."""
    st.divider()
    docs = [look.link(t(k), doc_url(k), cls="") for k in DOCS]
    right = look.el("span", None, look.txt(t("a_built_with")), *(" · " + d for d in docs))
    st.markdown(look.el("div", {"class": "kpd-foot"}, look.el("span", None, look.txt(t("a_disclaimer"))), right),
                unsafe_allow_html=True)


def doc_url(key: str, anchor_key: str | None = None) -> str:
    """GitHub link of a public document in the current language; anchor_key = i18n key of a section anchor
    (e.g. a_anchor_bond: the heading id GitHub gives that section of docs/VALIDATION_ko.md / _en.md)."""
    ko, en = DOCS[key]
    url = f"{REPO_URL}/blob/main/{ko if current_lang() == 'ko' else en}"
    return url + "#" + t(anchor_key) if anchor_key else url


def num(v, nd: int = 2, sep: bool = False) -> str:
    """Number -> text with nd decimals (thousands separator optional); NA -> '–'."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return t("a_na")
    try:
        f = float(v)
    except (TypeError, ValueError):
        return t("a_na")
    if math.isnan(f):
        return t("a_na")
    return f"{f:,.{nd}f}" if sep else f"{f:.{nd}f}"


# display decimals (fixes R3-9): price 4, yield % 3, bp 1 - display only, the data keep their values
DEC = {"price": 4, "pct": 3, "bp": 1, "years": 2, "dur": 3}


def sortable_text_col(values, nd: int) -> list[str]:
    """Numbers as equal-width, right-aligned display text with nd decimals; empty -> '–' (fixes R3-10).

    Why text and not a number column: Streamlit's table always draws an empty number cell as 'None' (the Styler's na_rep
    is not used for empty cells), so '–' needs text. A click on a text column header sorts with the browser's string
    comparison (localeCompare); padding every value with leading spaces to the same width makes that comparison follow
    the numeric order (checked in en / ko / de / ja collation; empty cells come first). Values are non-negative here."""
    texts = [t("a_na") if v is None or v != v else f"{float(v):.{nd}f}" for v in values]
    width = max((len(x) for x in texts), default=0)
    return [x.rjust(width) for x in texts]


def text_col(values, nd: int, sep: bool = True) -> list[str]:
    """A column of numbers as display text with nd decimals and thousands separators; empty -> '–' (never None / nan)."""
    return [num(v, nd, sep) for v in values]


def date_col(values) -> list[str]:
    """A column of dates as YYYY-MM-DD text; empty -> '–'."""
    out = []
    for v in values:
        try:
            out.append(t("a_na") if v is None or v != v or str(v) in ("", "NaT", "nan", "None") else str(v)[:10])
        except (TypeError, ValueError):
            out.append(t("a_na"))
    return out


def source_kind(url) -> str | None:
    """deals.csv source_url -> source badge kind (fixes U1-2 A): SEC filing (sec.gov), DART viewer (dart.fss.or.kr), any
    other web page = press; empty or not a web address -> None (shown as '–', no link)."""
    u = url if isinstance(url, str) else ""  # None / NaN / pd.NA -> ''
    if not u.startswith("http"):
        return None
    return "sec" if "sec.gov" in u else "dart" if "dart.fss.or.kr" in u else "news"
