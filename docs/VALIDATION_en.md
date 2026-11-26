# Validation

> A model evaluation built from public data; not a price indication and not investment advice. Every number here is copied from a cell of an audit or evaluation report, with the report path and that report's commit (the reports themselves are in the private repository). The numbers of app page ④ (`app/data/scorecard.json`) come from the same cells. Internal stage names (audit numbers etc.) appear in this document only. 한국어: [VALIDATION_ko.md](VALIDATION_ko.md)

## Summary

| Check | Result | Source (commit) |
|---|---|---|
| Bond engine ↔ independent QuantLib recalculation | All 256 bonds (55 gate + 201 reference) within tolerance, 0 mismatches | `reports/audit_a1_bond.md` (3f84725) |
| Demo-book valuation ↔ hand calculation | 90/90 comparisons matched, engine re-pricing difference 0 | `reports/audit_a3_mtm.md` (633bc23) |
| One-time holdout evaluation (53 deals) | Public representative output N0. The public rule could not be shown to beat N0 (+1.19, [−4.16, +6.54]) | `reports/p3_holdout.md` (9c119da) |
| Published sample check (as-of edition) | 10 workbooks with MasterCheck TRUE after a real Excel recalculation, MI workbook ↔ engine comparison of 207 cells with 0 mismatches, one-page summary PDFs 6/6 one page | `reports/r3_outputs_asof.md` (4504348) |
| Earlier independent output audit (previous edition) | 10 workbooks with MasterCheck TRUE, workbook ↔ engine comparison of 586 cells with 0 mismatches, source-document check 7/7 | `reports/audit_a8_credit.md` (f3782df) |

## 1. Bond engine (audit A1, QuantLib)

An auditor who did not write the engine recalculated the same bonds with QuantLib. Tolerances for price (per 100 face) and Z-spread were fixed in the report before the run.

| Set | Bonds | Max price difference | Max Z-spread difference (bp) | Verdict |
|---|---|---|---|---|
| Tier A (gate) | 55 | 2.4e-13 | 3.9e-11 | Pass |
| Tiers B, S, C (reference) | 201 | 2.4e-13 | 3.9e-11 | No difference |
| Total | 256 | | | 0 mismatches |

The 5 textbook examples also matched their published answers. Source: `reports/audit_a1_bond.md` (3f84725).

## 2. Demo-book valuation (audit A3)

Demo book - not actual holdings. A separate hand-calculation script that imports nothing from `src/` matched in **90/90** comparisons; the engine re-pricing difference on the book positions was **0**. Source: `reports/audit_a3_mtm.md` (633bc23).

## 3. Fair spread model (development → one-time holdout)

Error = prediction − actual (bp). Decision = MAE below N0's and the upper end of the paired-bootstrap (2,000 draws, seed 20261113) 95% interval below 0.

### 3.1 Development period (rule selection, pricing dates up to 2025-06-30)

| Mode | Rule | Deals | MAE | Difference (rule − N0) | 95% interval | Verdict |
|---|---|---|---|---|---|---|
| (both) | N0 baseline | 56 | 25.2 | – | – | – |
| Public | Rule chosen in development (`P2`) | 56 | 24.4 | −0.75 | [−5.59, +4.42] | Not shown to beat N0 → public representative output N0 |

Source: `reports/r1_p3_revision.md` (905d06e).

### 3.2 Holdout (one run; no rule change after the results, no re-run)

| Mode | Rule | Deals | MAE rule | MAE N0 | Difference | 95% interval | Verdict |
|---|---|---|---|---|---|---|---|
| Public | Rule chosen in development (`P2`) | 53 | 20.9 | 19.7 | +1.19 | [−4.16, +6.54] | Not better → representative output stays N0 |
| Internal (uses ICE, values not published) | I4 | 53 | 15.9 | 19.7 | −3.81 | [−7.44, −0.09] | Passes the rule, borderline |
| Internal, tier C included (sensitivity) | I4 | 102 | – | – | −1.82 | [−4.40, +0.66] | Contains 0 |

- The **median N0 error in the holdout was +10.5bp**: N0 predictions were above the actual spreads in that period (a baseline without index moves in a period of tightening spreads)
- The internal mode uses ICE BofA indices, so its predictions and index values are not published; only error statistics are shown
- Source: `reports/p3_holdout.md` (9c119da)

## 4. Output checks

**Published samples (as-of edition, `samples/`)**: all 10 workbooks regenerated on the as-of date had MasterCheck TRUE after a real Excel recalculation (0 error cells), the MI dashboard workbook ↔ engine comparison of 207 cells found 0 mismatches, one-page summary PDFs 6/6 are one page, forbidden wording 0, ICE scan non-integer hits 0. Source: `reports/r3_outputs_asof.md` (4504348).

**Earlier independent audit (audit A8, previous edition)**: an auditor who did not write the code confirmed 10 regenerated workbooks with MasterCheck TRUE, a workbook ↔ engine comparison of 586 cells with 0 mismatches, and source-document matches 7/7 for the changed financial values. The one minor finding is [Known issues](KNOWN_ISSUES_en.md) KI-01. Source: `reports/audit_a8_credit.md` (f3782df).

Before going into the public bundle, every sample file went through the forbidden-wording, ICE and absolute-path checks again (public bundle check).

## 5. Known-issue numbers ↔ internal records

| Public number | Internal record |
|---|---|
| KI-01 | audit `A8-1` |
| KI-02 | audit `A8-4` |
| KI-03 | credit scorecard test `C4` |
| KI-04 | holdout verdict (`p3_holdout.md` sections 2 and 5) |
| KI-07 | N0 range width `R2-13` |
| KI-11 | covered-bond ratings `R2-12` |
| KI-14 | audit `A9-4` |
| KI-15 | audit `A9-2`, `A9-D5` |
| KI-16 | audit `A9-1` |
