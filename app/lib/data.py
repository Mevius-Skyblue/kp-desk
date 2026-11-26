"""Readers of the as-of snapshot files in app/data (config/public.yaml bundle.snapshot). No database is used.

The files are written by scripts/export_public_data.py in the private repository. Readers keep only the whitelisted
columns, tolerate empty / missing optional columns (filled with NA) and unknown category values, and raise DataError
(file name only) when a file or a required column is missing, so a page can show a translated message instead of a crash.
Set KPD_APP_DATA / KPD_APP_SAMPLES to point the app at other folders (tests use synthetic fixtures).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parents[1]
ROOT = APP_DIR.parent
DATA_ENV = "KPD_APP_DATA"
SAMPLES_ENV = "KPD_APP_SAMPLES"

# column whitelists = config/public.yaml bundle.snapshot (deals_columns) and the export script
DEALS_COLUMNS = ["deal_key", "issuer_name_ko", "issuer_name_en", "issuer_type", "issue_date", "maturity", "tenor_years",
                 "currency", "coupon_pct", "reoffer_yield_pct", "rep_spread_bp", "rep_spread_basis", "sample_tier",
                 "rating_bucket", "source_url", "bond_nature"]  # bond_nature: config/public.yaml fixes R3-8
DEALS_REQUIRED = ["deal_key", "issuer_name_ko", "issuer_type", "issue_date", "tenor_years", "rep_spread_bp", "sample_tier",
                  "bond_nature"]
CURVE_COLUMNS = ["tenor", "tenor_years", "yield_pct"]
FAIR_COLUMNS = ["issuer_id", "issuer_name_ko", "issuer_name_en", "tenor_years", "point_bp", "low_bp", "high_bp", "level",
                "n_comps", "rule", "range_n"]
FAIR_REQUIRED = ["issuer_id", "issuer_name_ko", "tenor_years", "point_bp", "low_bp", "high_bp"]
NUMERIC = {"tenor_years", "coupon_pct", "reoffer_yield_pct", "rep_spread_bp", "yield_pct", "point_bp", "low_bp", "high_bp",
           "level", "n_comps", "range_n"}


class DataError(Exception):
    """A snapshot file is missing or unreadable. args[0] = file name (shown on screen through i18n)."""


def data_dir() -> Path:
    """Folder of the snapshot files: $KPD_APP_DATA or app/data."""
    return Path(os.environ.get(DATA_ENV) or APP_DIR / "data")


def samples_dir() -> Path:
    """Folder of the downloadable samples: $KPD_APP_SAMPLES or samples/ at the repository root."""
    return Path(os.environ.get(SAMPLES_ENV) or ROOT / "samples")


def _csv(name: str, columns: list[str], required: list[str], folder: Path | None) -> pd.DataFrame:
    """Read one snapshot CSV: whitelist columns only, missing optional columns -> NA, numbers coerced."""
    path = (folder or data_dir()) / name
    if not path.is_file():
        raise DataError(name)
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8")
    except Exception as e:  # malformed file
        raise DataError(name) from e
    if any(c not in df.columns for c in required):
        raise DataError(name)
    for c in columns:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[columns].copy()
    for c in columns:
        if c in NUMERIC:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def read_deals(folder: Path | None = None) -> pd.DataFrame:
    """deals.csv (1 row = 1 tranche) with issue_date / maturity as dates."""
    df = _csv("deals.csv", DEALS_COLUMNS, DEALS_REQUIRED, folder)
    for c in ("issue_date", "maturity"):
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    for c in ("issuer_name_en", "rating_bucket", "rep_spread_basis", "source_url", "currency"):
        df[c] = df[c].astype("string")
    df["issuer_name_en"] = df["issuer_name_en"].fillna(df["issuer_name_ko"])
    return df


def read_curve(folder: Path | None = None) -> pd.DataFrame:
    """curve.csv: the as-of US Treasury par curve (tenor label, tenor in years, yield in %)."""
    df = _csv("curve.csv", CURVE_COLUMNS, ["tenor_years", "yield_pct"], folder)
    return df.dropna(subset=["tenor_years", "yield_pct"]).sort_values("tenor_years").reset_index(drop=True)


def curve_points(folder: Path | None = None) -> dict[float, float]:
    """{tenor years: par yield %} for the bond engine."""
    df = read_curve(folder)
    return dict(zip(df["tenor_years"].astype(float), df["yield_pct"].astype(float)))


def read_fair(folder: Path | None = None) -> pd.DataFrame:
    """fair_spread.csv: public-mode N0 point / low / high per issuer and tenor (rows of other rules are dropped)."""
    df = _csv("fair_spread.csv", FAIR_COLUMNS, FAIR_REQUIRED, folder)
    if df["rule"].notna().any():
        df = df[df["rule"].fillna("N0") == "N0"]
    df["issuer_name_en"] = df["issuer_name_en"].fillna(df["issuer_name_ko"])
    return df.reset_index(drop=True)


def read_scorecard(folder: Path | None = None) -> dict:
    """scorecard.json: {asof, items: {id: {value, path, commit}}}."""
    path = (folder or data_dir()) / "scorecard.json"
    if not path.is_file():
        raise DataError("scorecard.json")
    try:
        sc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise DataError("scorecard.json") from e
    if not isinstance(sc.get("items"), dict):
        raise DataError("scorecard.json")
    return sc


def asof(folder: Path | None = None) -> str | None:
    """The one as-of date of the snapshot (scorecard.json `asof`), or None when unavailable."""
    try:
        return read_scorecard(folder).get("asof")
    except DataError:
        return None


def item(sc: dict, key: str) -> dict:
    """One scorecard number {value, path, commit}; a missing id is a DataError (the page then shows the message)."""
    it = sc["items"].get(key)
    if not isinstance(it, dict) or "value" not in it:
        raise DataError("scorecard.json")
    return it
