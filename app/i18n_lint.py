"""i18n rules of the public app, as functions (config/public.yaml bundle_checks 6_i18n). No Streamlit needed.

Used by tests/test_app_i18n.py, tests/test_app_bundle.py (inside the public repository's CI) and
scripts/check_public_bundle.py. This file and app/i18n.py are the only app files allowed to hold words in strings.

    table_problems(table)          keys a_*, ko / en non-empty, same {placeholders}
    literal_hits(app_dir, allow)   string constants in app code (docstrings excluded) with Hangul or an English phrase
                                   (two or more alphabetic words separated by spaces)
    used_keys(app_dir)             keys passed as a literal to t(...) / t_or(...)
"""

from __future__ import annotations

import ast
import re
import string
from pathlib import Path

HANGUL_RE = re.compile(r"[ᄀ-ᇿ㄰-㆏가-힣]")
PHRASE_RE = re.compile(r"[A-Za-z]{2,}[ \t]+[A-Za-z]{2,}")
EXEMPT_FILES = re.compile(r"^i18n[^/]*\.py$")  # app/i18n.py, app/i18n_lint.py (top level of app/)


def placeholders(text: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(text) if f}


def table_problems(table: dict) -> list[str]:
    """Problems of a {key: {ko, en}} table; empty list = complete."""
    out = []
    for k, v in table.items():
        if not k.startswith("a_"):
            out.append(f"{k}: prefix")
        ko, en = (v or {}).get("ko"), (v or {}).get("en")
        if not isinstance(ko, str) or not ko.strip():
            out.append(f"{k}: ko empty")
        if not isinstance(en, str) or not en.strip():
            out.append(f"{k}: en empty")
        if isinstance(ko, str) and isinstance(en, str) and ko.strip() and en.strip():
            if placeholders(ko) != placeholders(en):
                out.append(f"{k}: placeholders differ")
    return out


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """ids of the Constant nodes that are docstrings (module / class / function first statement)."""
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                ids.add(id(first.value))
    return ids


def app_py_files(app_dir: Path) -> list[Path]:
    """All .py files under app/ except the i18n files at its top level."""
    out = []
    for p in sorted(app_dir.rglob("*.py")):
        rel = p.relative_to(app_dir).as_posix()
        if "__pycache__" in rel or EXEMPT_FILES.match(rel):
            continue
        out.append(p)
    return out


def literal_hits(app_dir: Path, allow: list[str] | tuple[str, ...] = ()) -> list[dict]:
    """[{file, line, kind}] for string constants with Hangul ('hangul') or an English phrase ('phrase'). The text itself is
    not returned (only where). `allow` = exact strings that may stay (e.g. a fixed technical phrase)."""
    hits = []
    for p in app_py_files(app_dir):
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        docs = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)) or id(node) in docs:
                continue
            s = node.value
            if s in allow:
                continue
            kind = "hangul" if HANGUL_RE.search(s) else ("phrase" if PHRASE_RE.search(s) else None)
            if kind:
                hits.append({"file": p.relative_to(app_dir.parent).as_posix(), "line": node.lineno, "kind": kind})
    return hits


def used_keys(app_dir: Path) -> set[str]:
    """Literal keys of t("...") / t_or("...") calls in app code (dynamic keys such as f"a_type_{v}" are not included)."""
    keys = set()
    for p in app_py_files(app_dir):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) in ("t", "t_or"):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    keys.add(node.args[0].value)
    return keys
