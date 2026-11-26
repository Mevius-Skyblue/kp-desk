"""Page ④: validation results from app/data/scorecard.json, sample downloads (samples/, KO / EN), link to the known issues."""

import re

import streamlit as st

from app.i18n import t, t_or
from app.lib import data as D
from app.lib import ui

SAMPLE_RE = [  # file name -> (label key, issuer id or None, language)
    re.compile(r"^(?P<kind>memo1p|memo|pitchbook)_(?P<issuer>.+)_(?P<lang>ko|en)\.(pdf|xlsx)$"),
    re.compile(r"^(?P<kind>mtm)_demo_book_(?P<lang>ko|en)\.xlsx$"),
    re.compile(r"^(?P<kind>mi)_dashboard_(?P<lang>ko|en)\.xlsx$"),
]
MIME = {".pdf": "application/pdf", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}


def sample_files() -> list[tuple[str, object]]:
    """(label, path) of every recognised sample file, sorted by name; unknown files are not offered."""
    out = []
    folder = D.samples_dir()
    if not folder.is_dir():
        return out
    for p in sorted(folder.iterdir()):
        for rx in SAMPLE_RE:
            m = rx.match(p.name)
            if m:
                g = m.groupdict()
                lang = t(f"a_sample_lang_{g['lang']}")
                iss = g.get("issuer")
                fmt = {"lang": lang} if iss is None else {"lang": lang, "issuer": t_or(f"a_iss_{iss}", iss)}
                out.append((t(f"a_sample_{g['kind']}", **fmt), p))
                break
    return out


def v(sc: dict, key: str) -> str:
    """Display text of one scorecard number."""
    return str(D.item(sc, key)["value"])


st.title(t("a_val_title"))
st.markdown(t("a_val_intro"))
try:
    sc = D.read_scorecard()
    st.subheader(t("a_val_bond_title"))
    st.markdown(t("a_val_bond_body", total=v(sc, "a1_total"), gate=v(sc, "a1_gate_n"), ref=v(sc, "a1_ref_n"),
                  mismatch=v(sc, "a1_mismatch"), tb=v(sc, "a1_textbook")))
    st.caption(t("a_sc_source", path=D.item(sc, "a1_gate_n").get("path", "?"), commit=D.item(sc, "a1_gate_n").get("commit", "?")))

    st.subheader(t("a_val_mtm_title"))
    st.caption(t("a_val_demo_label"))
    st.markdown(t("a_val_mtm_body", hand=v(sc, "a3_hand"), engine=v(sc, "a3_engine_diff")))
    st.caption(t("a_sc_source", path=D.item(sc, "a3_hand").get("path", "?"), commit=D.item(sc, "a3_hand").get("commit", "?")))

    st.subheader(t("a_val_ho_title"))
    st.markdown(t("a_val_ho_scope", n=v(sc, "ho_n")))
    st.markdown(t("a_val_ho_public", rule=v(sc, "ho_p_mae"), n0=v(sc, "ho_n0_mae"), diff=v(sc, "ho_p_diff"), ci=v(sc, "ho_p_ci")))
    st.markdown(t("a_val_ho_internal", i4=v(sc, "ho_i4_mae"), n0=v(sc, "ho_n0_mae"), diff=v(sc, "ho_i4_diff"),
                  ci=v(sc, "ho_i4_ci"), ci_c=v(sc, "ho_i4_ci_c")))
    st.caption(t("a_sc_source", path=D.item(sc, "ho_n0_mae").get("path", "?"), commit=D.item(sc, "ho_n0_mae").get("commit", "?")))

    st.subheader(t("a_val_out_title"))
    st.markdown(t("a_val_out_body", files=v(sc, "r3_mc_files"), cells=v(sc, "r3_mi_cells"), mismatch=v(sc, "r3_mismatch"),
                  pdf=v(sc, "r3_pdf_1p")))
    st.caption(t("a_sc_source", path=D.item(sc, "r3_mi_cells").get("path", "?"), commit=D.item(sc, "r3_mi_cells").get("commit", "?")))
    st.markdown(t("a_val_out_prev", files=v(sc, "a8_files"), cells=v(sc, "a8_cells"), mismatch=v(sc, "a8_mismatch")))
    st.caption(t("a_sc_source", path=D.item(sc, "a8_cells").get("path", "?"), commit=D.item(sc, "a8_cells").get("commit", "?")))
except D.DataError as e:
    ui.data_error(e)

st.subheader(t("a_val_samples_title"))
st.caption(t("a_val_samples_note"))
files = sample_files()
if not files:
    st.info(t("a_val_samples_none"))
for i, (label, p) in enumerate(files):
    st.download_button(label, data=p.read_bytes(), file_name=p.name, mime=MIME.get(p.suffix.lower()), key=f"dl_{i}")

st.subheader(t("a_doc_known"))
st.markdown(t("a_val_known_note"))
st.markdown(f"[{t('a_val_known')}]({ui.doc_url('a_doc_known')})")
