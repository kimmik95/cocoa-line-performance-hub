# 00 - Answer Key: planted findings and data-quality issues

Purpose: validate the analysis against known ground truth. Keep this file in the repo and say so in the README
("analysis validated against a documented set of injected patterns"), or move it to a private folder if you prefer
the findings to be discovered fresh in an interview.

## Planted business findings (verified in the generated data)
| # | Finding | Where to look | Evidence |
|---|---|---|---|
| 1 | Changeover and allergen cleanout losses jump after peanut SKUs are added | Line 1030-LN02, from Mar 2026 | Changeover plus allergen minutes per shift 22.4 to 71.9; line OEE 72.4% to 62.6% |
| 2 | Packaging defect scrap spike after a packaging film change | Plant 1010, from 17 Aug 2026 | Scrap rate 3.6% to 3.7% (Jan to Jul) rising to 4.5% (Aug), 5.7% (Sep), 5.2% (Oct); reason SC04 |
| 3 | Best OEE but worst labor efficiency | Plant 1040 | OEE 78.3% (highest), labor efficiency 70.5% (lowest), overtime 9.5% of hours vs 3% to 5% elsewhere; crews two above standard |
| 4 | Summer cooling and bloom scrap | Plant 1040, Jun to Aug (both years) | Scrap 3.0% rising to 3.7%; reason SC05 |
| 5 | Equipment aging on the sugar-free line | Line 1030-LN03 | Speed performance falls from 82.7% (Q4 2024) to about 73% (2026), roughly 10 points |
| 6 | Night shift underperforms | Shift 3, all plants | OEE 70.2% vs 73.2% (shift 1) and 74.0% (shift 2); higher breakdown rate and lower speed |
| 7 | Strong seasonality | Network | Monthly good output 3.1M lbs (Mar 2025) to 6.3M lbs (Sep 2025) |

Trailing-12-month plant OEE: 1010 71.9%, 1020 74.0%, 1030 66.3%, 1040 78.3%.

## Injected data-quality issues
| # | Table | Issue | Plant | Rows | Detection and handling idea |
|---|---|---|---|---|---|
| 1 | AFRU | Duplicate confirmation postings | all | 55 | Same order, line, date, shift and quantities under different RUECK; dedupe on business key |
| 2 | AFRU | Posting date later than execution date | 1030 | 214 | Compare BUDAT to ISDD; report on ISDD |
| 3 | AFRU | Negative scrap quantity | all | 18 | Flag XMNGA < 0 as reversals without originals; exclude and log |
| 4 | MSEG | Quantities in KG instead of LB, Jan to Feb 2026 | 1020 | 2,166 | Check MEINS; convert at 0.45359 kg per lb |
| 5 | Labor | Missing timekeeping rows, 9 to 22 Jun 2025 | 1020 | 54 | Coverage check vs confirmations; exclude labor KPI for those shifts and annotate |
| 6 | Downtime | Reason left blank (DT999 Unclassified) | all | 989 | Track unclassified share as a data-quality KPI per plant |
