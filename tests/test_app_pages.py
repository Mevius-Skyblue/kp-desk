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

import pandas as pd
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
    assert f"{clean:,.4f}" in shown.iloc[:, 1].tolist()  # price shown with 4 decimals (fixes R3-9)


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
    assert len(df) == 4  # defaults: senior unsecured only (fixes R3-8) and sample tiers A, B, S (fixes R3-10)
    assert set(df["Bond type"]) == {"Senior unsecured"} and "C" not in set(df["Sample tier"])
    at.multiselect(key="comps_tier_en").set_value(["A", "B", "S", "C"]).run()
    assert len(at.dataframe[0].value) == 5
    at.multiselect(key="comps_nature_en").set_value(["senior", "sub_hybrid", "guaranteed"]).run()
    df = at.dataframe[0].value
    assert len(df) == 7
    assert {"Subordinated / hybrid", "Guaranteed"} <= set(df["Bond type"])
    assert "Rating source to be confirmed" in df["Rating bucket"].tolist()  # check_source code is translated
    assert "zz_new_type" in df["Type"].tolist()  # unknown type falls back to its code
    assert "Guaranteed issuer" in df["Type"].tolist()  # audit A9-2
    at.multiselect(key="comps_tier_en").set_value(["A"]).run()
    assert len(at.dataframe[0].value) == 2


@pytest.mark.parametrize("lang", ["ko", "en"])
def test_comps_default_shows_every_senior_row(lang, data_env):
    """Audit A9-3 + fixes R3-8: the default filters show every senior unsecured row (rows without an issue date included);
    with every bond type switched on, every snapshot row."""
    from app.lib import data as D

    deals = D.read_deals()
    at = run_page("views/comps.py", lang)
    default = (deals["bond_nature"] == "senior") & deals["sample_tier"].isin(["A", "B", "S"])  # fixes R3-8, R3-10
    assert len(at.dataframe[0].value) == int(default.sum())
    at.multiselect(key=f"comps_nature_{lang}").set_value(sorted(set(deals["bond_nature"]))).run()
    at.multiselect(key=f"comps_tier_{lang}").set_value(sorted(set(deals["sample_tier"]))).run()
    assert len(at.dataframe[0].value) == len(deals)


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
    html = " ".join(m.value for m in at.markdown)
    assert ">222.2 bp<" in html  # point estimate in the U1 result card (fixes U1-1)


def test_validation_samples(monkeypatch):
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    monkeypatch.setenv("KPD_APP_SAMPLES", str(FIX / "samples"))
    at = run_page("views/validation.py", "ko")
    labels = [b.label for b in at.get("download_button")]
    assert len(labels) == 10
    # U1 (fixes U1-1): the current language's edition is open, the other edition (5 files) is folded in one expander
    assert len(at.expander) == 1 and "영문판" in at.expander[0].label
    assert len(at.expander[0].get("download_button")) == 5


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


# ---------------------------------------------------------------- R3c design (config/public.yaml fixes R3-9)

@pytest.mark.parametrize("lang", ["ko", "en"])
def test_home_glance_cards(lang, data_env):
    """U1 evidence cards (fixes U1-1): numbers only from scorecard.json and the deals.csv row count; four tiles with links."""
    from app.i18n import t
    from app.lib import data as D

    at = run_page(PAGES[0], lang)
    assert not at.exception
    sc = D.read_scorecard()
    html = " ".join(m.value for m in at.markdown)
    it = lambda k: D.item(sc, k)["value"]  # noqa: E731
    total = int(it("a1_total"))
    assert t("a_card_deals_value", _lang=lang, n=f"{len(D.read_deals()):,}") in html
    assert t("a_g_match", _lang=lang, n=f"{total - int(it('a1_mismatch')):,}", total=f"{total:,}") in html
    assert t("a_g_ho_title", _lang=lang, n=it("ho_n")) in html
    for k in ("ho_n0_mae", "ho_p_mae"):
        assert ">" + t("a_bp", _lang=lang, v=it(k)) + "<" in html
    assert len(at.get("page_link")) == 4


@pytest.mark.parametrize("lang", ["ko", "en"])
@pytest.mark.parametrize("page", PAGES)
def test_no_private_paths_on_screen(page, lang, data_env):
    """U1 (fixes U1-1): no private report paths or commit hashes on screen; links go to the public VALIDATION document."""
    at = run_page(page, lang)
    html = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert "reports/" not in html and ".md (" not in html


def test_validation_cards_and_links(monkeypatch):
    """④ cards: n / total from the report cells; detail links point to VALIDATION section anchors in the current language."""
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    from app.i18n import t

    for lang, doc in (("ko", "docs/VALIDATION_ko.md#"), ("en", "docs/VALIDATION_en.md#")):
        at = run_page("views/validation.py", lang)
        html = " ".join(m.value for m in at.markdown)
        for anchor in ("a_anchor_bond", "a_anchor_mtm", "a_anchor_model", "a_anchor_out"):
            assert doc + t(anchor, _lang=lang) in html
        assert html.count('class="kpd-card"') == 4


@pytest.mark.parametrize("lang", ["ko", "en"])
def test_comps_chart_and_number_formats(lang, data_env):
    """② has one chart (altair, no wheel zoom, x fixed 0-30, legend below); tenor / coupon / yield / spread stay numeric
    (header sort by value, fixes R3-10); no 'None' / 'nan' text anywhere."""
    import json

    from app.i18n import t

    at = run_page("views/comps.py", lang)
    assert not at.exception
    charts = at.get("vega_lite_chart")
    assert len(charts) == 1
    spec = json.loads(charts[0].proto.spec)
    assert "params" not in spec  # no selection / zoom-pan interaction
    assert spec["encoding"]["x"]["scale"]["domain"] == [0, 30]
    # legend (fixes U1-2 B6): not drawn by the chart but as an HTML list under it, with the chart's own colour range
    assert spec["encoding"]["color"].get("legend", "absent") is None
    rng = spec["encoding"]["color"]["scale"]
    html = " ".join(m.value for m in at.markdown)
    assert 'class="kpd-legend"' in html
    for label, colour in zip(rng["domain"], rng["range"]):
        assert colour in html and label in html
    df = at.dataframe[0].value
    assert pd.api.types.is_float_dtype(df[t("a_col_spread", _lang=lang)])
    for col, nd in (("a_col_tenor", 2), ("a_col_coupon", 3), ("a_col_yield", 3)):
        vals = df[t(col, _lang=lang)].tolist()
        assert len({len(v) for v in vals}) <= 1, col  # equal width -> string sort = numeric sort
        for v in vals:
            assert v.strip() == "–" or re.fullmatch(rf"\d+\.\d{{{nd}}}", v.strip()), (col, v)
    text = df.drop(columns=[t("a_col_source", _lang=lang)])
    assert not any(c.strip() in ("None", "nan", "NaN", "<NA>", "NaT") for c in text.map(str).to_numpy().ravel().tolist())


def test_sortable_text_col_dash_and_numeric_order():
    """Empty -> '–'; equal-width text sorts like the numbers (ASCII space < digits; the browser collation was checked for
    en / ko / de / ja in R3-10)."""
    from app.lib import ui

    col = ui.sortable_text_col([4.125, None, 12.0, 0.5, 10.25], 3)
    assert [c.strip() for c in col] == ["4.125", "–", "12.000", "0.500", "10.250"]
    assert len({len(c) for c in col}) == 1
    nums = [c for c in col if c.strip() != "–"]
    assert sorted(nums) == sorted(nums, key=float)


def test_calculator_display_decimals(monkeypatch):
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    at = run_page("views/calculator.py", "en")
    rows = dict(zip(at.dataframe[0].value.iloc[:, 0], at.dataframe[0].value.iloc[:, 1]))
    assert re.fullmatch(r"[\d,]+\.\d{4}", rows["Clean price (per 100 face)"])
    assert re.fullmatch(r"\d+\.\d{3}", rows["Yield (%)"])
    assert re.fullmatch(r"-?\d+\.\d{1}", rows["G-spread (bp)"]) and re.fullmatch(r"-?\d+\.\d{1}", rows["Z-spread (bp)"])
    assert re.fullmatch(r"[\d,]+\.\d{2}", rows["Settlement amount (for the face amount)"]) and "," in rows[
        "Settlement amount (for the face amount)"]


# ---------------------------------------------------------------- U1b (config/public.yaml fixes U1-2)

def test_fair_comps_dots_and_table(monkeypatch):
    """③ comparable deals (fixes U1-2 A): one hollow dot and one table row per listed deal, values from deals.csv, blank issue
    date shown as '–', axis end covers the comparable spreads; EN screen uses English issuer names."""
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    from app.i18n import t

    for lang in ("ko", "en"):
        at = run_page("views/fair_spread.py", lang)  # default: first issuer by name = zz_fake_a, tenor 3 (3 listed deals)
        assert not at.exception
        html = " ".join(m.value for m in at.markdown)
        assert html.count('class="kpd-dot"') == 3
        assert t("a_fair_comps_title", _lang=lang) in html and html.count("<tr>") == 1 + 3
        name = "Fake Issuer F" if lang == "en" else "가상발행사 F"
        assert t("a_fair_dot_tip", _lang=lang, issuer=name, date="–", v="66.6") in html  # hover text of the dot
        for v in ("99.9", "111.1", "66.6"):
            assert ">" + v + "<" in html
        assert t("a_bp", _lang=lang, v="250") in html  # axis end: highest high_bp / comparable spread of the files, up to 50bp
        assert html.count('href="https://example.com/fake/') == 3  # source badges link to deals.csv source_url
        if lang == "en":
            assert not HANGUL.search(re.sub(r"<[^>]+>", " ", html))


def test_fair_comps_file_missing_hides_dots(monkeypatch, tmp_path):
    """Without fair_spread_comps.csv the page still runs: range bar without dots, no table, the old legend line."""
    import shutil

    d = tmp_path / "data"
    shutil.copytree(FIX / "data", d)
    (d / "fair_spread_comps.csv").unlink()
    monkeypatch.setenv("KPD_APP_DATA", str(d))
    from app.i18n import t

    at = run_page("views/fair_spread.py", "en")
    assert not at.exception
    html = " ".join(m.value for m in at.markdown)
    assert "kpd-dot" not in html and t("a_fair_comps_title", _lang="en") not in html
    assert t("a_fair_bar_legend", _lang="en") in html


def test_fair_comps_snapshot_rules():
    """The four pre-registered tests of the published list (fixes U1-2 A), on the real snapshot (public bundle / CI):
    every key is a deals.csv row, median of the listed spreads = point, count = n_comps (the chip), key columns only."""
    import statistics

    if not all((SNAP / f).is_file() for f in SNAP_FILES + ("fair_spread_comps.csv",)):
        pytest.skip("real snapshot not present (private repository)")
    comps = pd.read_csv(SNAP / "fair_spread_comps.csv", dtype=str)
    deals = pd.read_csv(SNAP / "deals.csv", dtype={"deal_key": str})
    fair = pd.read_csv(SNAP / "fair_spread.csv")
    assert list(comps.columns) == ["issuer_id", "tenor_years", "deal_key"]
    spread = dict(zip(deals["deal_key"], deals["rep_spread_bp"].astype(float)))
    groups = {(i, int(tn)): g["deal_key"].tolist() for (i, tn), g in comps.groupby(["issuer_id", "tenor_years"])}
    assert set(groups) <= set(zip(fair["issuer_id"], fair["tenor_years"].astype(int)))
    for r in fair.to_dict("records"):
        keys = groups.get((r["issuer_id"], int(r["tenor_years"])), [])
        assert keys and all(k in spread for k in keys), r["issuer_id"]
        assert len(keys) == int(r["n_comps"])
        assert abs(statistics.median(spread[k] for k in keys) - float(r["point_bp"])) <= 0.01 + 1e-9


def test_source_kind_and_dot_lanes():
    from app.lib import look, ui

    assert ui.source_kind("https://www.sec.gov/Archives/x") == "sec"
    assert ui.source_kind("https://dart.fss.or.kr/dsaf001/main.do?rcpNo=1") == "dart"
    assert ui.source_kind("https://news.example.com/a") == "news"
    assert ui.source_kind(None) is None and ui.source_kind(float("nan")) is None and ui.source_kind(pd.NA) is None
    assert ui.source_kind("") is None
    # overlapping dots take other lanes; distant dots stay on the axis lane; the order of the input is kept
    assert look.dot_lanes([50.0, 50.5, 51.0, 90.0]) == [0, -1, 1, 0]
    assert look.dot_lanes([10.0, 10.0, 10.0, 10.0, 10.0, 10.0]) == [0, -1, 1, -2, 2, 0]
    assert look.dot_lanes([]) == []


def test_language_switch_keeps_selection(monkeypatch):
    """A9-R17 / fixes U1-2 C: switching KO <-> EN keeps ③ issuer and tenor, ② filters and ① choices (as ids)."""
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    at = run_page("views/fair_spread.py", "ko")
    at.selectbox(key="fair_issuer_ko").set_value("zz_fake_b").run()
    at.selectbox(key="fair_tenor").set_value(7.0).run()
    html_ko = " ".join(m.value for m in at.markdown)
    at.radio(key="lang").set_value("en").run()
    assert at.selectbox(key="fair_issuer_en").value == "zz_fake_b" and at.selectbox(key="fair_tenor").value == 7.0
    html_en = " ".join(m.value for m in at.markdown)
    assert ">222.2 bp<" in html_ko and ">222.2 bp<" in html_en
    at.radio(key="lang").set_value("ko").run()
    assert at.selectbox(key="fair_issuer_ko").value == "zz_fake_b"

    at = run_page("views/comps.py", "en")
    at.multiselect(key="comps_tier_en").set_value(["A"]).run()
    at.multiselect(key="comps_nature_en").set_value(["senior", "guaranteed"]).run()
    n_en = len(at.dataframe[0].value)
    at.radio(key="lang").set_value("ko").run()
    assert at.multiselect(key="comps_tier_ko").value == ["A"]
    assert at.multiselect(key="comps_nature_ko").value == ["senior", "guaranteed"]
    assert len(at.dataframe[0].value) == n_en == 2

    at = run_page("views/calculator.py", "ko")
    at.radio(key="calc_mode_ko").set_value("price").run()
    at.radio(key="lang").set_value("en").run()
    assert at.radio(key="calc_mode_en").value == "price"


def _scorecard_copy(tmp_path, changes: dict):
    import json
    import shutil

    d = tmp_path / "data"
    shutil.copytree(FIX / "data", d)
    p = d / "scorecard.json"
    sc = json.loads(p.read_text(encoding="utf-8"))
    for k, v in changes.items():
        sc["items"][k]["value"] = v
    p.write_text(json.dumps(sc, ensure_ascii=False), encoding="utf-8")
    return d


@pytest.mark.parametrize("bad", [False, True])
def test_validation_status_follows_values(bad, monkeypatch, tmp_path):
    """fixes U1-2 B5 (A10-R3): the three check cards show the green check + green bar only when nothing mismatched;
    with a mismatch (synthetic scorecard) the grey info icon + grey bar. The fair-spread card is always the info icon."""
    changes = {"a1_mismatch": "1", "a3_hand": "10/11", "r3_mismatch": "1"} if bad else {}
    monkeypatch.setenv("KPD_APP_DATA", str(_scorecard_copy(tmp_path, changes)))
    from app.i18n import t

    at = run_page("views/validation.py", "en")
    assert not at.exception
    html = " ".join(m.value for m in at.markdown)
    n_pass = html.count('aria-label="' + t("a_ico_pass", _lang="en") + '"')
    n_info = html.count('aria-label="' + t("a_ico_info", _lang="en") + '"')
    assert (n_pass, n_info) == ((0, 4) if bad else (3, 1))
    assert html.count("kpd-fill-pass") == (0 if bad else 3)
    assert html.count("kpd-fill-base") == (3 if bad else 0) + 1  # + the baseline bar of the fair-spread card


def test_validation_layout_links_and_notes(monkeypatch):
    """fixes U1-2 B1-B3: four cards in the two-column grid, one 'details' link per card (none under the title), the
    public-mode sentence with its 95% interval below the cards as a grey note (not inside the card)."""
    monkeypatch.setenv("KPD_APP_DATA", str(FIX / "data"))
    from app.i18n import t

    at = run_page("views/validation.py", "ko")
    html = " ".join(m.value for m in at.markdown)
    assert html.count(">" + t("a_more", _lang="ko") + "<") == 4
    assert 'class="kpd-grid2"' in html
    assert "95%" not in html  # the interval sentence is no longer inside a card
    assert any("95%" in c.value and "N0" in c.value for c in at.caption)


def test_grid2_never_three_columns():
    """B1: the two-column grid's minimum column width is at least 40% of the row, so a third column cannot fit."""
    from app.lib import look

    rule = ";".join(look.CSS[".kpd-grid2"])
    assert "minmax(max(min(100%,340px),40%),1fr)" in rule
