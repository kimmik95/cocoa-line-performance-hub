# 01 - Company and Plant Design (fictional)

## Company profile
A Midwest confectionery manufacturer producing boxed assortments, bars, bite-size products, seasonal molded items and a
sugar-free range. Roughly 55M lbs of good output per year across four plants, serving retail and wholesale accounts.
Reporting sources: SAP S/4HANA (orders, confirmations, material documents), an MES (downtime events) and timekeeping (labor).

## Plants and lines
| Plant | Name | Lines |
|---|---|---|
| 1010 | Kansas City Hub Plant | LN01, LN02 enrobed boxed; LN03 molded seasonal; LN04 sugar-free |
| 1020 | Prairie Plant | LN01 enrobed boxed; LN02 bar; LN03 molded seasonal |
| 1030 | Mountain Plant | LN01 enrobed nut clusters; LN02 enrobed boxed; LN03 sugar-free |
| 1040 | Lone Star Plant | LN01 molded seasonal; LN02 bite-size; LN03 bar and enrobed |

Each line is an integrated make-and-pack line, so finished-good pounds are counted once. Ideal rates range from about
830 to 2,170 lbs/hr. Standard crews range from 7 to 11 operators.

## Shifts and calendar
- Three 8-hour shifts (06:00, 14:00, 22:00). Planned production time is 450 minutes (30-minute paid break excluded).
- Mon to Fri always scheduled for shift 1. Shifts 2 and 3 and Saturday work are added as seasonal load rises.
- US federal holidays and Sundays are not scheduled.
- Seasonality: Valentine's, Easter, Halloween and Christmas builds. Monthly network output ranges from about 3.1M lbs (March) to 6.4M lbs (September).

## KPI definitions (v0.1, to be formalized in the KPI dictionary)
| KPI | Definition |
|---|---|
| Availability | Run minutes / planned production minutes. All stops, planned or unplanned, reduce availability. |
| Performance | Gross lbs / (run hours x ideal rate) |
| Quality | Good lbs / gross lbs (gross = good + scrap) |
| OEE | Availability x Performance x Quality = good lbs / (planned hours x ideal rate) |
| Throughput | Good lbs per run hour |
| Scrap rate | Scrap lbs / gross lbs. Dollar value uses standard cost per lb (MARA STPRS). |
| Labor efficiency | Standard hours earned / actual hours. Standard hours = good lbs / 1000 x standard hours per 1000 lbs (engineered at 80% OEE). Actual hours include overtime. |
| Changeover time | Minutes of DT100 plus DT110 per production order start |

Targets by line form are in `data/reference/ref_kpi_targets.csv`.

## Modeling assumptions
- Downtime reasons are classed as planned (changeover, allergen cleanout, planned maintenance, scheduled sanitation) or unplanned.
- Allergen cleanout is triggered when a peanut or tree-nut product is followed by a different allergen profile.
- Standard costs are built from a simplified bill of materials (coating + fill + packaging) plus a conversion cost.
- Confirmations carry yield, scrap, setup hours, machine hours and labor hours, as in a simplified SAP AFRU.
