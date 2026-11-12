# 02 - Data Dictionary

Field names follow SAP conventions in simplified, representative form. Verify exact standard-table fields against a
real system before reusing them elsewhere.

| File | Source | Grain | Key fields |
|---|---|---|---|
| sap_afko_afpo_production_orders | SAP AFKO/AFPO | one row per production order | AUFNR, WERKS, ARBPL, MATNR, PSMNG (planned), WEMNG (goods receipt), IASMG (scrap), GSTRP, GLTRP, STTXT (REL/TECO) |
| sap_afru_confirmations | SAP AFRU | one row per line-shift confirmation | RUECK, AUFNR, WERKS, ARBPL, ISDD (actual date), BUDAT (posting date), SCHICHT, LMNGA (yield), XMNGA (scrap), ISM01 setup/downtime hrs, ISM02 machine hrs, ISM03 labor hrs |
| sap_mseg_material_documents | SAP MKPF/MSEG | one row per material document line | MBLNR, ZEILE, BWART (101 receipt, 261 consumption, 551 scrap), MATNR, MENGE, MEINS, DMBTR (value), AUFNR, GRUND (scrap reason) |
| mes_downtime_events | MES | one row per stop event | EVENT_ID, WERKS, ARBPL, ISDD, SHIFT, AUFNR, REASON_CODE, START_TS, DURATION_MIN |
| hr_labor_by_shift | Timekeeping | one row per line-shift | WERKS, ARBPL, ISDD, SHIFT, HEADCOUNT, REG_HOURS, OT_HOURS |
| sap_crhd_work_centers | SAP CRHD | one row per line | WERKS, ARBPL, KTEXT, LINE_FORM, IDEAL_RATE_LBHR, STD_CREW, STD_HRS_PER_1000LB |
| sap_mara_makt_materials | SAP MARA/MAKT | one row per material | MATNR, MAKTX, MTART (FERT/ROH/VERP), MATKL, ZSEASON, ZALLERGEN, STPRS (standard price per lb) |
| ref_* | Reference | lookups | plants, downtime reasons, scrap reasons, KPI targets, calendar |

## Join keys
- Line key: WERKS + ARBPL. Order: AUFNR. Material: MATNR. Calendar: ISDD to ref_calendar.DATE.
- Use **ISDD** (actual execution date) for performance reporting, not BUDAT (posting date).
- Production orders can span multiple shifts. Confirmations are the shift-level source of truth.

## Known data caveats
The extracts contain realistic quality problems that the pipeline must detect and handle. They are logged in
`data/ground_truth/dq_injection_log.csv` and explained in `analysis/00_answer_key.md`.
