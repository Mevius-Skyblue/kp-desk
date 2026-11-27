"""Bundle self-check of the public repository kp-desk (config/public.yaml bundle_checks 5_files and 6_i18n).

Source: docs/ci/test_app_bundle.py of the private repository; scripts/build_public_bundle_r3.py copies it to
tests/test_app_bundle.py of the bundle, where CI runs it on every push. scripts/check_public_bundle.py imports the same
functions (one rule set). In the private repository the tests are skipped (it is not a bundle).

    5 files   only allow-listed paths, no data / DB / key files, size limit, no tracked file that .gitignore ignores
    6 i18n    string table complete, no Korean text / English phrase in app code outside app/i18n*.py,
              every document and sample has its KO / EN pair
"""

from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "app" / "Home.py").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
IS_BUNDLE = not (ROOT / "config" / "public.yaml").exists()  # the private repository has config/; the bundle has none

# ---------------------------------------------------------------- rules (bundle paths; config/public.yaml bundle.allow_list)
ALLOW = [
    "app/*.py", "app/i18n_strings.json", "app/lib/*.py", "app/views/*.py",
    "app/data/deals.csv", "app/data/curve.csv", "app/data/fair_spread.csv", "app/data/scorecard.json",
    "app/data/fair_spread_comps.csv",  # comparison deals per fair_spread row (config/public.yaml fixes U1-2)
    "src/__init__.py", "src/bond/__init__.py", "src/bond/pricing.py", "src/bond/curve.py", "src/bond/daycount.py",
    "src/bond/interp.py",
    "tests/test_app_*.py", "tests/test_bond_textbook.py", "tests/test_b4_bond_edges.py",
    "tests/fixtures/public_app/data/*", "tests/fixtures/public_app/samples/*",
    "samples/*.pdf", "samples/*.xlsx",
    "docs/METHODOLOGY_ko.md", "docs/METHODOLOGY_en.md", "docs/VALIDATION_ko.md", "docs/VALIDATION_en.md",
    "docs/KNOWN_ISSUES_ko.md", "docs/KNOWN_ISSUES_en.md", "docs/DATA_NOTICE_ko.md", "docs/DATA_NOTICE_en.md",
    "docs/screenshot_home_ko.png", "docs/screenshot_home_en.png", "docs/screenshot_comps_ko.png", "docs/screenshot_comps_en.png",
    "docs/usage_ko.gif", "docs/usage_en.gif",  # README usage scenes (config/public.yaml fixes U3-1 D), checked by gif_problems
    "app/static/OFL.txt", "app/static/Pretendard-*.subset.woff",
    "README.md", "README_en.md", "LICENSE", "requirements.txt", ".gitignore", ".gitattributes", ".github/workflows/ci.yml",
    ".streamlit/config.toml",
]
DENY = ["data/*", "logs/*", "*.duckdb", "*.db", "*.sqlite", "*.parquet", "*.gz", "*.pyc", ".env", ".env.*", "*/.env",
        "*/.env.*", "*__pycache__*", "outputs/*", "venv/*", ".venv/*", "config/*", "reports/*", "CLAUDE.md"]
MAX_BYTES = 1_048_576
SIZE_ALLOW: list[str] = ["docs/usage_*.gif"]  # bundle paths allowed above MAX_BYTES: the two usage GIFs, which have
#                                            their own limit GIF_MAX_BYTES (fixes U3-1 D)
GIF_MAX_BYTES = 5_000_000
LITERAL_ALLOW: list[str] = []  # exact app string constants that may hold a phrase (none so far)
PAIRED_DOCS = ["docs/METHODOLOGY", "docs/VALIDATION", "docs/KNOWN_ISSUES", "docs/DATA_NOTICE"]


RUNTIME_DIRS = {".git", "__pycache__", ".pytest_cache"}  # created by git / Python / pytest while the checks run, never published


def bundle_files(root: Path) -> list[str]:
    """Files of the bundle as posix paths.

    In a git checkout (the bundle repository, CI) = the files git tracks, i.e. exactly what is published; runtime files
    that CI steps or pytest create in the work tree are not part of the bundle. Without git = every file except runtime dirs.
    (R3 CI fix: the first staging CI failed because .pytest_cache and other run-time files were counted.)
    """
    if (root / ".git").exists():
        r = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            return sorted(x for x in r.stdout.split("\0") if x)
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file() and not (RUNTIME_DIRS & set(p.relative_to(root).parts)))


def _m(rel: str, pats: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(rel, p) for p in pats)


def files_problems(root: Path) -> list[str]:
    """Check 5a: paths outside the allow-list or on the deny list."""
    return [r for r in bundle_files(root) if _m(r, DENY) or not _m(r, ALLOW)]


def size_problems(root: Path, max_bytes: int = MAX_BYTES, allow: list[str] | None = None) -> list[str]:
    """Check 5b: files above the size limit that are not listed in SIZE_ALLOW."""
    allow = SIZE_ALLOW if allow is None else allow
    return [r for r in bundle_files(root) if (root / r).stat().st_size > max_bytes and not _m(r, allow)]


def gif_blocks(data: bytes) -> list[tuple[str, bytes]]:
    """Extension blocks of a GIF file as (kind, payload): 'comment' / 'text' (plain-text) / 'app:<identifier>' / 'gce';
    raises ValueError when the file is not a well-formed GIF. Image data is skipped."""
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError("not a GIF")
    i = 13
    if data[10] & 0x80:  # global colour table
        i += 3 * (2 ** ((data[10] & 7) + 1))

    def sub_blocks(j: int) -> tuple[bytes, int]:
        out = b""
        while data[j] != 0:
            out += data[j + 1:j + 1 + data[j]]
            j += 1 + data[j]
        return out, j + 1

    blocks = []
    while i < len(data):
        b = data[i]
        if b == 0x3B:  # trailer
            return blocks
        if b == 0x21:
            label = data[i + 1]
            if label == 0xFF:  # application: fixed 11-byte identifier block, then data sub-blocks
                ident = data[i + 3:i + 3 + data[i + 2]]
                payload, i = sub_blocks(i + 3 + data[i + 2])
                blocks.append(("app:" + ident.decode("latin-1"), payload))
                continue
            payload, i = sub_blocks(i + 2)
            blocks.append(({0xFE: "comment", 0x01: "text", 0xF9: "gce"}.get(label, f"ext:{label:#x}"), payload))
        elif b == 0x2C:  # image descriptor (+ local colour table), LZW code size, image data
            flags = data[i + 9]
            i += 10 + (3 * (2 ** ((flags & 7) + 1)) if flags & 0x80 else 0)
            _, i = sub_blocks(i + 1)
        else:
            raise ValueError(f"bad block {b:#x} at {i}")
    raise ValueError("no trailer")


def gif_problems(root: Path, max_bytes: int = GIF_MAX_BYTES) -> list[str]:
    """Check 5d (fixes U3-1 D): every GIF of the bundle is at most max_bytes and carries no text metadata - no comment or
    plain-text block, and no application block other than the NETSCAPE2.0 loop block (e.g. no XMP)."""
    out = []
    for r in bundle_files(root):
        if not r.lower().endswith(".gif"):
            continue
        data = (root / r).read_bytes()
        if len(data) > max_bytes:
            out.append(f"{r}: {len(data)} bytes > {max_bytes}")
        try:
            kinds = [k for k, _ in gif_blocks(data)]
        except (ValueError, IndexError) as e:
            out.append(f"{r}: unreadable ({e})")
            continue
        out += [f"{r}: {k} block" for k in dict.fromkeys(kinds) if k in ("comment", "text")
                or (k.startswith("app:") and k != "app:NETSCAPE2.0")]
    return out


def tracked_ignored(root: Path) -> list[str] | None:
    """Check 5c: files tracked by the bundle's git that its .gitignore ignores. None = the bundle is not a git repository."""
    if not (root / ".git").exists():
        return None
    r = subprocess.run(["git", "ls-files", "-ci", "--exclude-standard"], cwd=root, capture_output=True, text=True, encoding="utf-8")
    return [x for x in r.stdout.splitlines() if x.strip()]


def i18n_problems(root: Path) -> list[str]:
    """Check 6a: the generated string table is complete (a_* keys, ko / en non-empty, same placeholders)."""
    from app.i18n_lint import table_problems

    p = root / "app" / "i18n_strings.json"
    if not p.is_file():
        return ["app/i18n_strings.json missing"]
    return table_problems(json.loads(p.read_text(encoding="utf-8"))["strings"])


def literal_problems(root: Path) -> list[dict]:
    """Check 6b: Korean text / English phrases in app string constants outside app/i18n*.py (file and line only)."""
    from app.i18n_lint import literal_hits

    return literal_hits(root / "app", LITERAL_ALLOW)


def pair_problems(root: Path) -> list[str]:
    """Check 6c: every public document and sample has its KO / EN pair."""
    files = set(bundle_files(root))
    out = [f"{d}_{lang}.md" for d in PAIRED_DOCS for lang in ("ko", "en") if f"{d}_{lang}.md" not in files]
    if "README.md" not in files or "README_en.md" not in files:
        out.append("README.md / README_en.md")
    for f in sorted(files):
        m = re.match(r"^(samples/.+)_(ko|en)(\.[a-z]+)$", f)
        if m:
            other = f"{m.group(1)}_{'en' if m.group(2) == 'ko' else 'ko'}{m.group(3)}"
            if other not in files:
                out.append(other)
        elif f.startswith("samples/"):
            out.append(f"{f} (no _ko / _en suffix)")
    return out


pytestmark = pytest.mark.skipif(not IS_BUNDLE, reason="runs inside the public bundle only")


def test_files_allowed():
    assert files_problems(ROOT) == []


def test_sizes():
    assert size_problems(ROOT) == []


def test_gif_files():
    assert gif_problems(ROOT) == []


def test_no_tracked_ignored_files():
    assert tracked_ignored(ROOT) in (None, [])


def test_i18n_table_complete():
    assert i18n_problems(ROOT) == []


def test_no_words_in_app_code():
    assert literal_problems(ROOT) == []


def test_ko_en_pairs():
    assert pair_problems(ROOT) == []
