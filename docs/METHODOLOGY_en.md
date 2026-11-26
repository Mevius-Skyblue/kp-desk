# Methodology

> Model results built from public data; not a price indication and not investment advice. Numbers are a snapshot on one as-of date (shown at the top of the app and in the first block of every sample). 한국어: [METHODOLOGY_ko.md](METHODOLOGY_ko.md)

## 1. Data

| Item | Content |
|---|---|
| Sources | DART (Korean electronic disclosure: debt issuance tables, bond notes, material-event reports), SEC EDGAR (English filings of policy institutions and the sovereign), US Treasury par yield curve, and **numbers and URLs only** from press reports (no article text is stored). Terms: [Data notice](DATA_NOTICE_en.md) |
| Unit | One row = one tranche. A bond found in several sources is merged into one row, with a source priority per field (SEC → DART → press) |
| Issuers | An alias table groups names of the same issuing entity (a branch counts as its bank). Types: sovereign, policy institution, state-owned enterprise, bank, card and capital company, other financial, non-financial corporate, guaranteed issuer. English names come from the alias table, else the DART corporate English name or the company's official English name (source recorded per name) |
| Key | The app snapshot uses only a stable key from issuer code, currency, issue date and maturity (`deal_key`, ASCII only; when keys coincide, `n1`, `n2` … in source-key order). The samples (memos, pitch books, demo book etc.) show internal reference numbers of the as-of build (K#####); they are build positions that change between rebuilds, so they cannot be matched with the app keys directly ([Known issues](KNOWN_ISSUES_en.md) KI-14) |

### Sample tiers

| Tier | Definition | Use |
|---|---|---|
| A | Confirmed currency (SEC, press or DART original text) + reoffer yield | Main sample |
| B | Confirmed currency + coupon only (no reoffer yield) | Main sample (coupon-basis correction) |
| S | Confirmed currency + press-reported final spread over Treasuries, no yield and no coupon | Main sample |
| C | Currency inferred from DART amounts (passed a consistency check) | Reference and sensitivity only |
| D | Excluded: kimchi and digital bonds, equity-linked, non-USD, floating rate, under 1 year, no spread, etc. | Not in the comparison table |

### Representative spread
In bp over US Treasuries. From the reoffer yield when available (minus the interpolated Treasury par yield at the same tenor), else the press-reported final spread, else the coupon. Coupon-based spreads tend to be lower than reoffer-based ones, so the model evaluation corrected coupon-based values by a constant fixed in the development period (−7.59bp, median of 35 development deals). The comparison table shows the representative spread before that correction.

## 2. Bond engine (`src/bond/`)

| Item | Rule |
|---|---|
| Conventions | USD: 30/360 (US bond basis), semi-annual coupon. EUR: Act/Act (ICMA), annual. US Treasury: Act/Act (ICMA), semi-annual |
| Yield | Street-convention yield compounded at the coupon frequency: dirty price = Σ cash flow / (1 + y/f)^(periods) |
| Schedule | Built backwards from maturity in steps of 12/f months; the first period may be short. No business-day adjustment, holiday calendar or end-of-month rule ([Known issues](KNOWN_ISSUES_en.md)) |
| Accrued, settlement amount | From the previous coupon date (or the issue date in the first period) to settlement. Settlement amount = (clean price + accrued) × face / 100 |
| Risk measures | Macaulay and modified duration, convexity, DV01 (price fall for a 1bp yield rise) |
| Curve | Treasury par yields interpolated linearly between tenors (flat beyond the ends). Discount factors are bootstrapped on a 6-month grid anchored at settlement (at least 30 years) from "par bond price = 100", with log-linear discount factors between nodes |
| G-spread | Bond yield − interpolated par yield at the same remaining tenor |
| Z-spread | The constant added to every zero rate (semi-annual compounding) so that the discounted cash flows equal the market dirty price |

The engine is a set of pure functions without database or network access; calculator ① calls them as is (no new formula). Independent check: [Validation](VALIDATION_en.md).

## 3. Fair spread range (public mode, app page ③)

Only the **public mode's representative output, the N0 baseline,** is published.

1. **Comparison pool**: main-sample deals (A, B, S) priced before the as-of date (market data up to the day before). Coupon-based values carry the constant above
2. **Issuer profile**: type and rating bucket come from the issuer's latest "senior unsecured, not guaranteed" deal before the as-of date (ratings of covered, subordinated or guaranteed bonds are not used)
3. **Point estimate**: median spread of pool deals in the same type group (sovereign and policy / state-owned / bank / financial / non-financial) and the same rating bucket (AAA, AA, A, BBB, BB, none) priced in the 18 months before the as-of date; if none, the same type at any rating; then the whole pool (the app's "comparison group" shows this level)
4. **Range**: point − Q3(e) to point − Q1(e), with e = development-period N0 errors (prediction − actual, main sample). The width is therefore the same for every issuer, and because N0 does not use the tenor, one issuer gets the same value at 3, 5, 7 and 10 years

The app table (`app/data/fair_spread.csv`) is the engine function called as is on the as-of date, not a new calculation.

## 4. Rule selection and validation

- **Pre-registration**: rules, samples and decision criteria were committed in configuration files before results were produced; anything changed after seeing results is appended to the same file with the reason
- **Period split**: candidate rules were compared and chosen in the development period only (pricing dates up to 2025-06-30). The later period (holdout) was locked and evaluated **once**; it is not run again
- **Candidates**: public-mode candidates use a KPD own index (moving median of public deal spreads) and the issuer's history or comparable deals. Internal-mode candidates use ICE BofA indices and are for internal analysis only (values are not published, only error statistics)
- **Decision**: a candidate beats the baseline only if its mean absolute error (MAE) is lower than N0's and the upper end of the paired-bootstrap (2,000 draws) 95% interval is below 0. The public candidates did not pass in development and could not be shown to beat N0 in the holdout either → public representative output = N0
- **Audits**: separate audits by agents that did not write the code checked the bond engine (QuantLib recalculation), the demo-book valuation (hand calculation), the holdout run record and the outputs (workbook ↔ engine)

## 5. Demo book and samples

- **Demo book - not actual holdings**: an example book drawn from public deals by a fixed rule and random seed. It is revalued on the as-of curve and its profit and loss is split into carry, rates, spread and residual
- **Samples**: credit memo and one-page summary (PDF), pitch book, demo-book valuation and MI dashboard (Excel), KO / EN. They are drafts generated automatically from public data with hypothetical transactions. Workbooks keep live formulas and a MasterCheck cell shows their self-checks
- Not in the app: internal-mode (ICE) values, daily updates, document generation, loan pages, scorecard pages
