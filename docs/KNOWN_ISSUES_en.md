# Known issues

> Model results built from public data; not a price indication and not investment advice. The limits below are disclosed rather than fixed (fixing many of them would reuse an already used test set, or change a pre-registered rule after seeing results). The mapping to internal records is in [Validation](VALIDATION_en.md) section 5. 한국어: [KNOWN_ISSUES_ko.md](KNOWN_ISSUES_ko.md)

## Financial data (sample credit memos and MI dashboard)

**KI-01 Interest expense tagged with company-specific concepts.** The interest-expense rule reads standard XBRL concepts only. When a filing tags the interest expense of its finance-cost note with a company-specific concept, the rule falls back to interest paid from the cash-flow statement. Rows found: DI Dongil FY2024, FY2025 and the 2026 first-half LTM, Hanwha Aerospace FY2023. Only the industry interest-coverage comparison and the credit-scorecard inputs are affected; bond and spread numbers and the DSCR of the sample loan borrowers are not. Not fixed.

**KI-02 Asset-backed borrowings.** Korean Air's "asset-backed borrowings" line (FY2024, non-current) is not covered by the account-name rule and is left out of total borrowings (total borrowings about 1.9% too low). The 2026 first-half current liabilities have no such line, so the DSCR is not affected. Not fixed.

**KI-03 Credit scorecard test n=9.** The internal credit scorecard was tested once on a test set of 9. The sample is too small for any significance claim. Running it again would reuse the used test set, so it is not run again. The app has no scorecard page.

## Fair spread model

**KI-04 Borderline holdout verdict.** The upper end of the internal-mode (ICE) rule's 95% interval is −0.09, very close to 0, and with tier C included the interval [−4.40, +0.66] contains 0. In the holdout, other internal candidates did better than the chosen one, unlike the development ranking, but the choice was not changed (pre-registration). All public-mode candidates had a higher mean absolute error than N0 in the holdout (public representative output = N0).

**KI-05 N0 predicted high in the holdout period.** The median N0 error in the holdout period was +10.5bp (predictions above actual). A baseline without index moves lagged in a period of tightening spreads. There is no guarantee of the same result in another market regime.

**KI-06 Issuance-timing bias.** The sample holds only deals that were actually issued. Issuers tend to come to market when conditions are good, and withdrawn or postponed deals are absent, so spreads can look tighter than what an issuer would get on an arbitrary date. Coupon-based spreads also tend to be lower than reoffer-based ones (corrected by a development-period constant in the model evaluation only; the comparison table shows uncorrected values).

**KI-07 N0 range width and tenor.** The N0 range comes from the quartiles of development-period N0 errors, so its width is the same for every issuer. N0 does not use the tenor, so one issuer gets the same value at 3, 5, 7 and 10 years. Public rules that reflect tenor and issuer features showed no evidence of beating the baseline and are not published.

**KI-08 Small samples.** The holdout has 53 target deals from 26 issuers. Many type and rating cells hold fewer than 10 deals, so cell-level results are not interpreted.

## Bond calculation

**KI-09 Schedule and settlement rules.** The data has no first coupon date, so the schedule is an estimate built backwards from maturity. There is no long first period, business-day adjustment, end-of-month rule or holiday calendar. Settlement T+n counts Monday to Friday only (holidays ignored). Under 30/360, periods touching the end of February can give slightly different coupon amounts from other tools. The calculator uses the settlement date as entered and does not check holidays.

## Data

**KI-10 Coverage 50–79%.** Against market statistics, the main sample covers 50–79% depending on the source and year (sources define the market differently, so this is a rough comparison). State-owned enterprise deals depend heavily on press reports. DART notes rarely state the currency of each bond; deals whose currency is inferred from amounts are kept as tier C (reference only).

**KI-11 Covered-bond ratings and currency / amount.** Two KB Kookmin Bank covered bonds (issued 2025-09 and 2026-09) carry bond-level ratings (S&P and Fitch AAA), which are not used as the issuer rating. A third deal with the same rating pattern (issued 2023-10) could not be confirmed from a source and is shown as "rating source to be confirmed". For the first two, the currency and amount in the data also differ from the press (EUR). The currency rule is frozen by pre-registration, so they were left as they are; both are tier D (outside spread comparisons).

**KI-12 As-of snapshot.** Every number is a snapshot on one as-of date. Issues, filings and revisions after that date are not included, and press-reported numbers can change later. There are no daily updates.

## Sample files

**KI-13 Nature of the samples.** Credit memos, one-page summaries, pitch books and the MI dashboard are drafts generated automatically from public data, with hypothetical transactions and a demo book (not actual holdings). PDFs are converted from Word documents, and the text checks of PDFs depend on text extraction. Workbook formulas are live, but other spreadsheet programs may show recalculated values differently.

**KI-14 Internal reference numbers in the samples.** The source and table cells of the samples (memos, pitch books, demo book, MI dashboard) show internal reference numbers of the as-of build (K#####). They are row positions of the database build and change when it is rebuilt (even from the same input, the order inside one issuer-and-date group has changed). The app snapshot uses only the stable key (`deal_key`), so the sample numbers cannot be matched with the app keys directly.

**KI-15 Issuer type classification.** Incheon International Airport Corporation is not in the alias table and was classified by its industry code as a non-financial corporate (not a state-owned enterprise). Changing it would change its fair-spread comparison group, so it was left as is for this as-of edition. Guaranteed deals appear in the comparison table with the type "guaranteed issuer". The model has no type group for guaranteed bonds, so issuers with only guaranteed deals (4) get no fair-spread value (issuers that also have senior deals are computed with the type of those deals).

**KI-16 English issuer names.** Issuers without an English name in the alias table use the DART corporate English name (capitalisation as registered), the company's official English name, or the Latin-script name in the filing. One (Lotte Auto Lease) is a romanization not yet confirmed against an official source. The source is recorded for each name. Some Korean text remains in the English samples: the Korean-name field (Name (Korean)), source cells that quote account names from Korean filings verbatim, some internal issuer-code cells, and bilingual notices and labels (e.g. the demo-book tag).

**KI-17 Coupon of the Lotte Rental 2-year deal of 2023-12-08 (checked, not changed).** This deal in the comparison table (sample tier C, coupon-based representative spread −11.97bp) uses the 4.44% interest rate of the bond table in the DART annual report (receipt no. 20240315000897) as its coupon. A derivatives note of the same report shows a cross-currency swap with DBS Bank (USD 50,000,000, maturing 2025-12-08, receive SOFR+1.5%, pay 4.44%) described as paying a fixed KRW rate against the floating foreign-currency interest of a foreign-currency bond. The bond is therefore most likely a USD floating-rate note (SOFR+1.5%) and 4.44% the fixed KRW swap rate (no evidence of a guarantee was found). If so, the coupon-based spread is not meaningful and the floating-rate note should leave the sample. Data values were not changed in this as-of edition (tier C is not shown in the default view of the table). Other privately placed foreign-currency bonds may also show a post-swap rate in the DART bond table.
