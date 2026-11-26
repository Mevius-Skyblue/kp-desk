"""Public app pages under Streamlit AppTest, Korean and English (config/public.yaml 6. bundle_checks 1_apptest).

Data: the SYNTHETIC fixtures in tests/fixtures/public_app (fake issuers, fake numbers; no real deal data), plus - inside the
public bundle only - the real as-of snapshot app/data when its four files exist. No database is used.
"""

from __future__ import annotations

import os
import re
import socket
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "app" / "Home.py").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
FIX = ROOT / "tests" / "fixtures" / "public_app"
SNAP = ROOT / "app" / "data"
SNAP_FILES = ("deals.csv", "curve.csv", "fair_spread.csv", "scorecard.json")
PAGES = ["views/home.py", "views/calculator.py", "views/comps.py", "views/fair_spread.py", "views/validation.py"]
HANGUL = re.compile(r"[가-힣]")


def _windows_socketpair():
    """Windows runners: IPv4 loopback socket pairs from several threads can fail (WinError 10014); build them on ::1.
    Adapted from KVI docs/ci/test_public_app.py (docs/provenance.md)."""
    if os.name != "nt":
        return
    orig = socket.socketpair

    def pair(family=None, type=socket.SOCK_STREAM, proto=0):
        if family not in (None, socket.AF_INET6):
            return orig(family, type, proto)
        ls = socket.socket(socket.AF_INET6, type, proto)
        try:
            ls.bind(("::1", 0))
            ls.listen(1)
            cs = socket.socket(socket.AF_INET6, type, proto)
            cs.connect(ls.getsockname()[:2])
            ss, _ = ls.accept()
        finally:
            ls.close()
        return ss, cs

    try:
        a, b = pair()
        a.close()
        b.close()
    except OSError:  # no IPv6 loopback: keep the original
        return
    socket.socketpair = pair


_windows_socketpair()

DATA_SETS = [("fixture", FIX / "data", FIX / "samples")]
if all((SNAP / f).is_file() for f in SNAP_FILES):  # public bundle: also the real snapshot
    DATA_SETS.append(("snapshot", SNAP, ROOT / "samples"))


@pytest.fixture(params=DATA_SETS, ids=[d[0] for d in DATA_SETS])
def data_env(request, monkeypatch):
    _, d, s = request.param
    monkeypatch.setenv("KPD_APP_DATA", str(d))
    monkeypatch.setenv("KPD_APP_SAMPLES", str(s))
    return request.param


def run_page(page: str, lang: str):
    """Run the entry script with a language and switch to a page; returns the AppTest after the run."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "app" / "Home.py"), default_timeout=120)
    at.session_state["lang"] = lang
    at.run()
    if page != PAGES[0]:
        at.switch_page(page)
        at.run()
    return at


def visible_text(at) -> str:
    """Text of the text elements (titles, markdown, captions, alerts, metric labels, button labels, table headers)."""
    parts = []
    for coll in (at.title, at.header, at.subheader, at.markdown, at.caption, at.info, at.warning, at.error, at.success):
        parts += [str(e.value) for e in coll]
    parts += [str(m.label) for m in at.metric]
    parts += [str(b.label) for b in at.get("download_button")] if hasattr(at, "get") else []
    for df in at.dataframe:
        parts += [str(c) for c in df.value.columns]
    return "\n".join(parts)


@pytest.mark.parametrize("lang", ["ko", "en"])
@pytest.mark.parametrize("page", PAGES)
def test_page_runs(page, lang, data_env):
    at = run_page(page, lang)
    assert not at.exception, [e.value for e in at.exception]
    txt = visible_text(at)
    from app.i18n import t

    assert t("a_disclaimer", _lang=lang) in txt
    if lang == "en" and data_env[0] == "fixture":
        # no Korean on English screens (data values such as Korean issuer names are inside tables, not checked here)
        assert not HANGUL.search(txt), [ln for ln in txt.splitlines() if HANGUL.search(ln)][:3]


def test_toggle_switches_language(data_env):
    at = run_page(PAGES[0], "ko")
    assert any("기준일" in c.value for c in at.caption)
    at.radio(key="lang").set_value("en").run()
    assert any(c.value.startswith("As of") for c in at.caption)
    assert at.session_state["lang"] == "en"


def test_calculator_equals_engine(monkeypatch):
    """Page ① shows the engine's numbers: defaults through the page == src/bond called directly."""
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    from app.lib import data as D
    from app.lib.calc import calculate, defaults
    from src.bond.curve import bootstrap, g_spread, z_spread
    from src.bond.pricing import Bond, accrued_interest, dv01, mod_duration, price_from_yield

    d = defaults(date.fromisoformat(D.asof()))
    pts = D.curve_points()
    r = calculate(d["conv"], d["coupon"], d["issue"], d["maturity"], d["settle"], d["face"], yield_pct=d["yield_pct"],
                  curve_points=pts)
    b = Bond(d["coupon"], d["issue"], d["maturity"], 2, "30/360")
    clean = price_from_yield(b, d["yield_pct"], d["settle"])
    assert r["clean"] == clean and r["accrued"] == accrued_interest(b, d["settle"])
    assert r["mod_duration"] == mod_duration(b, d["yield_pct"], d["settle"])
    assert r["dv01"] == dv01(b, d["yield_pct"], d["settle"], d["face"])
    assert r["g_spread_bp"] == g_spread(d["yield_pct"], pts, (d["maturity"] - d["settle"]).days / 365.25)
    assert r["z_spread_bp"] == z_spread(b, clean, d["settle"], bootstrap(pts, d["settle"], d["maturity"]))
    # price -> yield round trip through the same wrapper
    r2 = calculate(d["conv"], d["coupon"], d["issue"], d["maturity"], d["settle"], d["face"], clean_price=clean, curve_points=pts)
    assert abs(r2["yield_pct"] - d["yield_pct"]) < 1e-9

    at = run_page("views/calculator.py", "en")
    shown = at.dataframe[0].value
    assert f"{clean:.6f}" in shown.iloc[:, 1].tolist()


def test_calculator_bad_dates_message(monkeypatch):
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    at = run_page("views/calculator.py", "en")
    at.date_input(key="calc_settle").set_value(date(2100, 1, 1)).run()
    assert not at.exception
    from app.i18n import t

    assert [e.value for e in at.error] == [t("a_calc_err_dates", _lang="en")]


def test_comps_filters_and_labels(monkeypatch):
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    at = run_page("views/comps.py", "en")
    df = at.dataframe[0].value
    assert len(df) == 7
    assert "Rating source to be confirmed" in df["Rating bucket"].tolist()  # check_source code is translated
    assert "zz_new_type" in df["Type"].tolist()  # unknown type falls back to its code
    assert "Guaranteed issuer" in df["Type"].tolist()  # audit A9-2
    at.multiselect(key="comps_tier_en").set_value(["A"]).run()
    assert len(at.dataframe[0].value) == 2


@pytest.mark.parametrize("lang", ["ko", "en"])
def test_comps_default_shows_every_snapshot_row(lang, data_env):
    """Audit A9-3: with the default filters every snapshot row is shown (rows without an issue date included)."""
    from app.lib import data as D

    at = run_page("views/comps.py", lang)
    assert len(at.dataframe[0].value) == len(D.read_deals())


def _hangul_cells(at) -> list[str]:
    """Hangul anywhere in the data shown: table cells and headers, widget options (the language switch excepted)."""
    out = []
    for df in at.dataframe:
        for c in df.value.columns:
            out += [f"{c}: {v}" for v in df.value[c].map(str) if HANGUL.search(v)]
        out += [str(c) for c in df.value.columns if HANGUL.search(str(c))]
    for w in list(at.selectbox) + list(at.multiselect):
        out += [str(o) for o in w.options if HANGUL.search(str(o))]
    return out


@pytest.mark.parametrize("page", PAGES)
def test_english_screens_show_no_hangul_data(page, data_env):
    """Audit A9-1: EN screens show no Korean in any data cell or option (issuer_name_ko is not shown in EN)."""
    at = run_page(page, "en")
    assert _hangul_cells(at) == []


def test_fair_spread_none_and_value(monkeypatch):
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    at = run_page("views/fair_spread.py", "en")
    at.selectbox(key="fair_issuer_en").set_value("zz_fake_b").run()
    at.selectbox(key="fair_tenor").set_value(5.0).run()
    from app.i18n import t

    assert t("a_fair_none", _lang="en") in [i.value for i in at.info]
    at.selectbox(key="fair_tenor").set_value(3.0).run()
    assert [m.value for m in at.metric][0] == "222.2 bp"


def test_validation_samples(monkeypatch):
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    monkeypatch.setenv("KPD_APP_SAMPLES", str(FIX / "samples"))
    at = run_page("views/validation.py", "ko")
    labels = [b.label for b in at.get("download_button")]
    assert len(labels) == 10 and any("영문판" in x for x in labels)


def test_missing_data_message(monkeypatch, tmp_path):
    """No snapshot files: every page still runs and the data pages show the translated file-missing message."""
    monkeypatch.setenv("KPD_APP_DATA", str(tmp_path))
    monkeypatch.setenv("KPD_APP_SAMPLES", str(tmp_path))
    for page in PAGES:
        at = run_page(page, "en")
        assert not at.exception, (page, [e.value for e in at.exception])
    at = run_page("views/comps.py", "en")
    assert any("deals.csv" in w.value for w in at.warning)


def test_hangul_check_catches_korean_name(monkeypatch, tmp_path):
    """Positive control for the check above: an empty English name falls back to the Korean one and is caught."""
    import shutil

    d = tmp_path / "data"
    shutil.copytree(FIX / "data", d)
    p = d / "deals.csv"
    p.write_text(p.read_text(encoding="utf-8").replace("Fake Issuer B", ""), encoding="utf-8")
    monkeypatch.setenv("KPD_APP_DATA", str(d))
    at = run_page("views/comps.py", "en")
    assert any("가상발행사 B" in x for x in _hangul_cells(at))


def test_option_labels_follow_language_switch(monkeypatch):
    """After switching KO -> EN the issuer list and the selected issuer show English labels (language-scoped widget key)."""
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    at = run_page("views/fair_spread.py", "ko")
    assert any(HANGUL.search(str(o)) for o in at.selectbox(key="fair_issuer_ko").options)
    at.radio(key="lang").set_value("en").run()
    sb = at.selectbox(key="fair_issuer_en")
    assert not any(HANGUL.search(str(o)) for o in sb.options) and not HANGUL.search(str(sb.format_func(sb.value)))
