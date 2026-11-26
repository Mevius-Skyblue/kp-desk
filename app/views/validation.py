"""Page ④: validation results from app/data/scorecard.json, sample downloads (samples/, KO / EN), link to the known issues.

U1 layout (config/public.yaml fixes U1-1): four cards (bond engine, demo book, outputs, fair spread estimate) with bars made
only from report cells, a link to the matching section of the public VALIDATION document instead of private report paths,
and the samples grouped by kind with format badges: the current language's edition open, the other one folded.
"""

import re

import streamlit as st

from app.i18n import current_lang, t, t_or
from app.lib import data as D
from app.lib import look, ui

SAMPLE_RE = [  # file name -> (kind, issuer id or None, language)
    re.compile(r"^(?P<kind>memo1p|memo|pitchbook)_(?P<issuer>.+)_(?P<lang>ko|en)\.(pdf|xlsx)$"),
    re.compile(r"^(?P<kind>mtm)_demo_book_(?P<lang>ko|en)\.xlsx$"),
    re.compile(r"^(?P<kind>mi)_dashboard_(?P<lang>ko|en)\.xlsx$"),
]
MIME = {".pdf": "application/pdf", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
GROUPS = (("memo", "a_sg_memo"), ("memo1p", "a_sg_memo1p"), ("pitchbook", "a_sg_pitchbook"), ("book", "a_sg_book"))
GROUP_OF = {"memo": "memo", "memo1p": "memo1p", "pitchbook": "pitchbook", "mtm": "book", "mi": "book"}
BOOK_LABEL = {"mtm": "a_sb_mtm", "mi": "a_sb_mi"}


def sample_files() -> list[dict]:
    """{kind, group, issuer, lang, path} of every recognised sample file, sorted by name; unknown files are not offered."""
    out = []
    folder = D.samples_dir()
    if not folder.is_dir():
        return out
    for p in sorted(folder.iterdir()):
        for rx in SAMPLE_RE:
            m = rx.match(p.name)
            if m:
                g = m.groupdict()
                out.append({"kind": g["kind"], "group": GROUP_OF[g["kind"]], "issuer": g.get("issuer"), "lang": g["lang"],
                            "path": p})
                break
    return out


def button_label(f: dict) -> str:
    """Issuer name for the per-issuer samples, the book name for the demo book / MI workbooks."""
    if f["issuer"] is not None:
        return t_or(f"a_iss_{f['issuer']}", f["issuer"])
    return t(BOOK_LABEL[f["kind"]])


def sample_groups(files: list[dict], lang: str) -> None:
    """One bordered card per sample group (badge + title + one download button per file) for one language edition."""
    mine = [f for f in files if f["lang"] == lang]
    shown = [(g, k) for g, k in GROUPS if any(f["group"] == g for f in mine)]
    for col, (g, title_key) in zip(st.columns(max(len(shown), 1)), shown):
        fs = [f for f in mine if f["group"] == g]
        kinds = sorted({f["path"].suffix.lower() for f in fs})
        bdg = "".join(look.badge(t("a_fmt_pdf") if x == ".pdf" else t("a_fmt_xlsx"), x.lstrip(".")) for x in kinds)
        with col.container(key=f"kpd_card_sg_{lang}_{g}"):
            st.markdown(look.el("div", {"class": "kpd-gtitle"}, bdg, look.txt(t(title_key))), unsafe_allow_html=True)
            with st.container(horizontal=True, gap="small"):  # buttons side by side, wrapping on narrow screens
                for f in fs:
                    st.download_button(button_label(f), data=f["path"].read_bytes(), file_name=f["path"].name,
                                       mime=MIME.get(f["path"].suffix.lower()), key=f"dl_{f['path'].stem}")


def v(sc: dict, key: str) -> str:
    """Display text of one scorecard number."""
    return str(D.item(sc, key)["value"])


def count_pair(text: str) -> tuple[int, int]:
    """'90/90' -> (90, 90) (report cell of the demo-book audit)."""
    a, b = text.replace(" ", "").split("/")
    return int(a), int(b)


st.title(t("a_val_title"))
st.markdown(look.note(t("a_val_intro"), cls="kpd-text"), unsafe_allow_html=True)  # links: one per card (fixes U1-2 B2)
try:
    sc = D.read_scorecard()
    total, bad = int(v(sc, "a1_total")), int(v(sc, "a1_mismatch"))
    hand_ok, hand_n = count_pair(v(sc, "a3_hand"))
    cells, cell_bad = int(v(sc, "r3_mi_cells")), int(v(sc, "r3_mismatch"))
    n0, pm = float(v(sc, "ho_n0_mae")), float(v(sc, "ho_p_mae"))
    # icon and bar colour follow the report cell (audit A10-R3, fixes U1-2 B5): no mismatch -> green check + green bar,
    # otherwise the grey info icon + grey bar
    status = lambda ok: (look.icon("pass", look.PASS, box=None, width=2.2, label=t("a_ico_pass")) if ok  # noqa: E731
                         else look.icon("info", look.INFO, box=None, width=2.2, label=t("a_ico_info")))
    bar_kind = lambda ok: "pass" if ok else "base"  # noqa: E731
    more = lambda anchor: look.link(t("a_more"), ui.doc_url("a_doc_valid", anchor))  # noqa: E731
    cards = [
        look.card(look.head(status(bad == 0), t("a_vc_bond"), strong=True),
                  look.big(t("a_g_match", n=f"{total - bad:,}", total=f"{total:,}")), look.bar((total - bad) / total, bar_kind(bad == 0)),
                  look.note(t("a_val_bond_body", total=v(sc, "a1_total"), gate=v(sc, "a1_gate_n"), ref=v(sc, "a1_ref_n"),
                              mismatch=v(sc, "a1_mismatch"), tb=v(sc, "a1_textbook")), cls="kpd-text"),
                  more("a_anchor_bond")),
        look.card(look.head(status(hand_ok == hand_n), t("a_vc_mtm"), strong=True),
                  look.big(t("a_g_match", n=f"{hand_ok:,}", total=f"{hand_n:,}")), look.bar(hand_ok / hand_n, bar_kind(hand_ok == hand_n)),
                  look.note(t("a_val_mtm_body", hand=v(sc, "a3_hand"), engine=v(sc, "a3_engine_diff")), cls="kpd-text"),
                  look.note(t("a_val_demo_label")), more("a_anchor_mtm")),
        look.card(look.head(status(cell_bad == 0), t("a_vc_out"), strong=True),
                  look.big(t("a_g_match", n=f"{cells - cell_bad:,}", total=f"{cells:,}")),
                  look.bar((cells - cell_bad) / cells, bar_kind(cell_bad == 0)),
                  look.note(t("a_val_out_body", files=v(sc, "r3_mc_files"), cells=v(sc, "r3_mi_cells"),
                              mismatch=v(sc, "r3_mismatch"), pdf=v(sc, "r3_pdf_1p")), cls="kpd-text"),
                  more("a_anchor_out")),
        look.card(look.head(look.icon("info", look.INFO, box=None, width=2.2, label=t("a_ico_info")), t("a_vc_fair"),
                            strong=True),
                  look.big(t("a_similar")),
                  look.compare([(t("a_bar_base"), t("a_bp", v=v(sc, "ho_n0_mae")), n0 / max(n0, pm), "base"),
                                (t("a_bar_model"), t("a_bp", v=v(sc, "ho_p_mae")), pm / max(n0, pm), "accent")]),
                  look.note(t("a_val_ho_scope", n=v(sc, "ho_n")), cls="kpd-text"),  # 2-3 lines (fixes U1-2 B3)
                  more("a_anchor_model")),
    ]
    st.markdown(look.grid(*cards, cls="kpd-grid2"), unsafe_allow_html=True)
    # grey notes under the cards: public-mode sentence with its 95% interval (moved out of the card, numbers unchanged)
    st.caption(t("a_val_ho_public", rule=v(sc, "ho_p_mae"), n0=v(sc, "ho_n0_mae"), diff=v(sc, "ho_p_diff"),
                 ci=v(sc, "ho_p_ci")))
    st.caption(t("a_val_ho_internal", i4=v(sc, "ho_i4_mae"), n0=v(sc, "ho_n0_mae"), diff=v(sc, "ho_i4_diff"),
                 ci=v(sc, "ho_i4_ci"), ci_c=v(sc, "ho_i4_ci_c")))
    st.caption(t("a_val_out_prev", files=v(sc, "a8_files"), cells=v(sc, "a8_cells"), mismatch=v(sc, "a8_mismatch")))
except D.DataError as e:
    ui.data_error(e)

lang = current_lang()
other = "en" if lang == "ko" else "ko"
st.subheader(t("a_val_samples_head", edition=t(f"a_sample_lang_{lang}")))
st.caption(t("a_val_samples_note"))
files = sample_files()
if not files:
    st.info(t("a_val_samples_none"))
else:
    sample_groups(files, lang)
    if any(f["lang"] == other for f in files):
        with st.expander(t("a_val_samples_other", edition=t(f"a_sample_lang_{other}"))):
            sample_groups(files, other)

st.subheader(t("a_doc_known"))
st.markdown(t("a_val_known_note"))
st.markdown(f"[{t('a_val_known')}]({ui.doc_url('a_doc_known')})")
