# Data notice

> Model results built from public data; not a price indication and not investment advice. Every number is a snapshot on one as-of date (shown at the top of the app and in the first block of every sample). 한국어: [DATA_NOTICE_ko.md](DATA_NOTICE_ko.md)

## Data used

| Source | What was used | Form in this repository |
|---|---|---|
| DART (Financial Supervisory Service electronic disclosure, OpenDART) | Debt issuance tables, bond notes, material-event reports, financial statements | Issue-term numbers and links to the filing (`https://dart.fss.or.kr/dsaf001/main.do?rcpNo=…`); financial numbers in the sample credit memos |
| SEC EDGAR (US Securities and Exchange Commission) | English filings of policy institutions and the sovereign (issue terms) | Issue-term numbers and filing URLs |
| US Treasury (Daily Treasury Par Yield Curve Rates) | Par yield curve on the as-of date | `app/data/curve.csv` (one day) |
| Bank of Korea ECOS | Industry statistics (industry comparison in the sample credit memos) | Aggregated numbers inside the sample files |
| Press reports | **Numeric facts** such as size, coupon, final spread | Numbers and article URLs only. **No article text is stored or reproduced.** Copyright of the articles stays with their publishers |

## Data not used

- **ICE BofA indices (via FRED)**: **not** in this repository, the app or the samples. No index value, level or change is published. They were used only in private internal analysis (internal mode); public documents show only that mode's error statistics
- Non-public information: no internal document of any institution and no undisclosed information was used
- Market-data terminals or paid databases

## Labels

- **Demo book - not actual holdings**: the book in the samples is an example drawn from public deals by a rule; it is not the holdings or valuation of any institution
- Sample credit memos, one-page summaries, pitch books and the MI dashboard are drafts generated automatically from public data with hypothetical transactions
- Model estimate ranges are model results built from public data; not a price indication and not investment advice

## Paths of the private source repository

File paths (`config/…`, `data/…`, `reports/…`, `scripts/…`) and stage names in the source cells and version lines of the samples refer to the private source repository this public package was built from; those files are not in this repository.

## Accuracy

Errors can come from transcribing public data, from corrections of the sources themselves, and from the limits of currency and amount inference (details: [Known issues](KNOWN_ISSUES_en.md)). Each row's source link leads to the original. Please report an error as an issue of the repository.
