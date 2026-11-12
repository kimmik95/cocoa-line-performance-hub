# Cocoa Line Performance Hub

**An end-to-end manufacturing performance analytics project** that simulates the first month of an
*Industrial Performance Analyst* role at a multi-plant confectionery manufacturer: requirements, SAP-style data,
SQL modeling, Power BI semantic model and dashboards, SAP Analytics Cloud design, KPI governance, data quality,
training material and executive insights.

> **All data is synthetic.** The company, plants, lines, materials and numbers are fictional. The data is calibrated to the
> scale of a ~55M lbs/year chocolate manufacturer and follows SAP S/4HANA table and field conventions
> (AFKO/AFPO, AFRU, MKPF/MSEG, CRHD, MARA/MAKT) in simplified form. It is not data from any real company.

## The business problem
Four plants and 13 production lines report OEE, throughput, labor efficiency and scrap in different ways, from different
systems, on different calendars. Leadership cannot compare plants, see where losses come from, or trust the numbers.
This project builds one governed reporting layer and the dashboards on top of it.

## Network at a glance (trailing 12 months)
| Item | Value |
|---|---|
| Plants / lines | 4 / 13 (enrobed, molded, bar, bite-size, sugar-free) |
| Good output | ~55.0M lbs |
| History | 24 months (Nov 2024 to Oct 2026), 3 shifts, seasonal peaks |
| Records | 13.9K shift records, 5.9K production orders, 13.9K confirmations, 131K material document lines, 31.7K downtime events |
| Plant OEE | 66% to 78% |

## Architecture
```
SAP-style extracts (CSV)  ->  SQL staging / clean / reporting layers  ->  Power BI semantic model + DAX
 AFRU, AFKO/AFPO, MSEG,        data quality checks, star schema          SAP Analytics Cloud story or design spec
 CRHD, MARA, MES, HR labor
```

## Build status
- [x] Day 1: company and plant design, KPI definitions, synthetic data generator, data dictionary, answer key
- [ ] Day 2: SQL pipeline and data quality checks
- [ ] Day 3: Power BI semantic model and DAX library
- [ ] Day 4: dashboard pages (Executive, Plant OEE, Line drill-through, Waste and Scrap, Labor)
- [ ] Day 5: insight memo and CI tracker
- [ ] Day 6: SAC story/spec, user guide, training deck
- [ ] Day 7: polish, walkthrough video, one-page summary

## Quick start
```bash
pip install -r requirements.txt
python scripts/generate_data.py          # regenerates everything in ./data (seed 42)
```

## Repo structure
```
data/sap_extracts/   SAP-style and MES/HR extracts (what an analyst receives)
data/reference/      master data, reason codes, KPI targets, calendar
data/ground_truth/   clean shift fact and data-quality injection log (validation only)
scripts/             data generator
sql/  powerbi/  sac/  docs/  analysis/  plan/
```
