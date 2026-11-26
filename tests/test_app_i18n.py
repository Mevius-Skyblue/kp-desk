"""Public app i18n (config/public.yaml 5. app.i18n, bundle check 6). Runs in the private repo and in the public bundle.

- the generated table app/i18n_strings.json is complete (a_* keys, ko / en non-empty, same placeholders)
- in the private repo: the table equals what scripts/gen_i18n.py makes from the glossary (no stale file)
- t() fails loudly on a missing key; every literal key used by the app exists; dynamic key families exist
- app code (outside app/i18n*.py) holds no Korean text and no English phrase in string constants
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "app" / "Home.py").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import i18n  # noqa: E402
from app.i18n_lint import literal_hits, table_problems, used_keys  # noqa: E402

TABLE = i18n.strings()


def test_table_complete():
    assert TABLE, "empty table"
    assert table_problems(TABLE) == []


@pytest.mark.skipif(not (ROOT / "scripts" / "gen_i18n.py").exists(), reason="private repository only")
def test_generated_table_is_current():
    from scripts.gen_i18n import build, load_app_block, validate

    block, src = load_app_block()
    assert validate(block) == []
    assert json.loads((ROOT / "app" / "i18n_strings.json").read_text(encoding="utf-8")) == build(block, src)


def test_t_missing_key_raises_and_languages():
    with pytest.raises(i18n.I18nKeyError):
        i18n.t("a_no_such_key_xyz")
    assert i18n.t("a_asof", _lang="ko", asof="2030-01-01") == "기준일 2030-01-01"
    assert i18n.t("a_asof", _lang="en", asof="2030-01-01") == "As of 2030-01-01"
    assert i18n.current_lang() == "ko"  # default outside Streamlit


def test_missing_language_value_raises(tmp_path, monkeypatch):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"strings": {"a_x": {"ko": "가", "en": ""}}}), encoding="utf-8")
    monkeypatch.setattr(i18n, "STRINGS_PATH", p)
    i18n._load.cache_clear()
    try:
        with pytest.raises(i18n.I18nKeyError):
            i18n.t("a_x", _lang="en")
        assert i18n.t("a_x", _lang="ko") == "가"
    finally:
        i18n._load.cache_clear()


def test_used_literal_keys_exist():
    missing = sorted(used_keys(ROOT / "app") - set(TABLE))
    assert missing == []


def test_dynamic_key_families_exist():
    from app.lib.keys import dynamic_keys

    missing = sorted(k for k in dynamic_keys() if k not in TABLE)
    assert missing == []


def test_no_words_in_app_code():
    assert literal_hits(ROOT / "app") == []


def test_lint_catches_planted_literals(tmp_path):
    """Positive control: a Korean literal and an English phrase are caught; docstrings and single tokens are not."""
    app = tmp_path / "app"
    (app / "views").mkdir(parents=True)
    (app / "views" / "bad.py").write_text('"""Docstring with many words is fine."""\nx = "발행사"\ny = "Bond calculator"\nz = "a_key"\n',
                                         encoding="utf-8")
    (app / "i18n.py").write_text('w = "exempt words here"\n', encoding="utf-8")
    hits = literal_hits(app)
    assert sorted(h["kind"] for h in hits) == ["hangul", "phrase"]
    assert all(h["file"] == "app/views/bad.py" for h in hits)


@pytest.mark.skipif(not (ROOT / "scripts" / "gen_i18n.py").exists(), reason="private repository only")
def test_merge_draft_into_glossary_copy(tmp_path):
    """Phase-2 merge on copies: the app block lands in the glossary once, unchanged; a second merge does nothing."""
    import shutil

    from scripts.gen_i18n import DRAFT, GLOSSARY, load_app_block, merge_draft

    g, d = tmp_path / "glossary.yaml", tmp_path / "draft.yaml"
    shutil.copy2(GLOSSARY, g)
    shutil.copy2(DRAFT, d)
    import yaml

    before = yaml.safe_load(g.read_text(encoding="utf-8"))
    if "app" in before:
        pytest.skip("glossary already merged")
    assert merge_draft(g, d) is True
    after = yaml.safe_load(g.read_text(encoding="utf-8"))
    assert after["app"] == yaml.safe_load(d.read_text(encoding="utf-8"))["app"]
    assert {k: v for k, v in after.items() if k != "app"} == before  # nothing else changed
    assert merge_draft(g, d) is False
    block, src = load_app_block(g, d)
    assert src == g and block == after["app"]
