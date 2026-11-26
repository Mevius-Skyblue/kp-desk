"""Code lists of the pages and the i18n key families built from them (keys made at run time, e.g. f"a_type_{v}").

Tests check that every key of these families exists in app/i18n_strings.json (a value seen in the data without a label,
such as a new issuer type, falls back to its code through t_or).
"""

from __future__ import annotations

from app.i18n import LANGS
from src.bond.pricing import CONVENTIONS

ISSUER_TYPES = ("sovereign", "policy", "soe", "bank", "card_capital", "fin_other", "nonfin",  # config/p3.yaml type_group keys
                "guaranteed")  # deals of guaranteed issuers (audit A9-2; no type group, so no fair_spread value)
NATURES = ("senior", "sub_hybrid", "guaranteed", "covered")  # bond_nature codes (config/public.yaml fixes R3-8)
NATURE_DEFAULT = ("senior",)  # comps table default: senior unsecured only; the user can switch the others on
TIER_ORDER = ("A", "B", "S", "C")  # public sample tiers (config/public.yaml deals.csv)
TIER_DEFAULT = ("A", "B", "S")  # comps table default (fixes R3-10): C = estimated currency, switched on by the user
BUCKETS = (("a_tb_0_3", 0.0, 3.0), ("a_tb_3_5", 3.0, 5.0), ("a_tb_5_7", 5.0, 7.0), ("a_tb_7_10", 7.0, 10.0),
           ("a_tb_10p", 10.0, float("inf")))
BASES = ("reoffer", "news_final", "coupon")  # rep_spread_basis values (config/p1d.yaml)
LEVELS = (1, 2, 3)  # N0 fallback levels (src/predict/rules.rule_n0)
SAMPLE_KINDS = ("memo", "memo1p", "pitchbook", "mtm", "mi")
SAMPLE_ISSUERS = ("posco_holdings", "kb_bank", "kexim")  # config/public.yaml outputs.targets
DOC_KEYS = ("a_doc_readme", "a_doc_method", "a_doc_valid", "a_doc_known", "a_doc_data")


def dynamic_keys() -> list[str]:
    """Every key the pages build from a code."""
    ks = [f"a_conv_{c}" for c in CONVENTIONS] + [f"a_lang_{x}" for x in LANGS]
    ks += [f"a_type_{x}" for x in ISSUER_TYPES] + [f"a_tier_{x}" for x in TIER_ORDER] + [f"a_nature_{x}" for x in NATURES] + [b[0] for b in BUCKETS] + ["a_tb_na"]
    ks += [f"a_basis_{x}" for x in BASES] + [f"a_level_{x}" for x in LEVELS]
    ks += [f"a_sample_lang_{x}" for x in LANGS] + [f"a_iss_{x}" for x in SAMPLE_ISSUERS]
    ks += ["a_sg_memo", "a_sg_memo1p", "a_sg_pitchbook", "a_sg_book", "a_sb_mtm", "a_sb_mi"]  # sample groups (fixes U1-1)
    ks += ["a_anchor_bond", "a_anchor_mtm", "a_anchor_model", "a_anchor_out"]  # VALIDATION section anchors
    return ks + list(DOC_KEYS)
