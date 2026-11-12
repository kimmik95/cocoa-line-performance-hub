#!/usr/bin/env python3
"""
Cocoa Line Performance Hub - synthetic data generator
=====================================================
Generates 24 months of SAP-style manufacturing extracts for a FICTIONAL
multi-plant confectionery network (~55M lbs/year good output).

ALL DATA IS SYNTHETIC. Plant names, lines, materials and numbers are invented.
Table/field names follow SAP S/4HANA conventions (AFKO/AFPO, AFRU, MKPF/MSEG,
CRHD, MARA/MAKT) in simplified, representative form.

Usage:
    python scripts/generate_data.py                # writes into ./data
    python scripts/generate_data.py --seed 7       # different random draw
"""
import argparse
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

START_DATE = date(2024, 11, 1)
END_DATE = date(2026, 10, 31)
PLANNED_MIN = 450                       # 8h shift minus 30 min paid break
SHIFT_START_HOUR = {1: 6, 2: 14, 3: 22}
STD_OEE_ALLOWANCE = 0.80                # engineered standard assumes 80% OEE
DEFAULT_RATE_SCALE = 1.2733                # calibrated so trailing 12M ~ 55M lbs

# ---------------------------------------------------------------- plants
PLANTS = {
    "1010": dict(name="Kansas City Hub Plant", city="Kansas City", state="MO",
                 perf=0.90, bd=1.00, crew_extra=0, ot_mult=1.0, load_adj=1.00),
    "1020": dict(name="Prairie Plant", city="Prairie City", state="KS",
                 perf=0.89, bd=1.10, crew_extra=0, ot_mult=1.0, load_adj=0.95),
    "1030": dict(name="Mountain Plant", city="Mountain City", state="CO",
                 perf=0.88, bd=1.15, crew_extra=0, ot_mult=1.0, load_adj=0.92),
    "1040": dict(name="Lone Star Plant", city="Lone Star City", state="TX",
                 perf=0.94, bd=0.70, crew_extra=2, ot_mult=2.0, load_adj=1.05),
}

# werks, arbpl, description, form, ideal lbs/hr, standard crew
LINES = [
    ("1010", "LN01", "Enrobing Line 1 - Boxed Assortments", "ENROBED", 1450, 9),
    ("1010", "LN02", "Enrobing Line 2 - Boxed Assortments", "ENROBED", 1300, 8),
    ("1010", "LN03", "Molding Line 3 - Seasonal Shells", "MOLDED", 950, 11),
    ("1010", "LN04", "Sugar-Free Molding Line 4", "SUGARFREE", 700, 7),
    ("1020", "LN01", "Enrobing Line 1 - Boxed", "ENROBED", 1350, 9),
    ("1020", "LN02", "Bar Line 2", "BAR", 1700, 8),
    ("1020", "LN03", "Molding Line 3 - Seasonal", "MOLDED", 1000, 11),
    ("1030", "LN01", "Enrobing Line 1 - Nut Clusters", "ENROBED", 800, 8),
    ("1030", "LN02", "Enrobing Line 2 - Boxed", "ENROBED", 1200, 8),
    ("1030", "LN03", "Sugar-Free Line 3", "SUGARFREE", 650, 7),
    ("1040", "LN01", "Molding Line 1 - Seasonal", "MOLDED", 1100, 10),
    ("1040", "LN02", "Bite-Size Line 2", "BITE", 950, 8),
    ("1040", "LN03", "Bar and Enrobed Line 3", "BAR", 1500, 9),
]
LINE_FORMS = {"ENROBED": {"ENROBED"}, "MOLDED": {"MOLDED"}, "BAR": {"BAR", "BITE"},
              "BITE": {"BITE", "BAR"}, "SUGARFREE": {"SUGARFREE"}}
LINE_FORMS_OVERRIDE = {("1040", "LN03"): {"BAR", "ENROBED"}}
LINE_PERF_ADJ = {"SUGARFREE": -0.05, "MOLDED": -0.02, "BAR": 0.03, "BITE": 0.0, "ENROBED": 0.0}
CHANGEOVER_MEAN = {"ENROBED": 45, "MOLDED": 65, "BAR": 30, "BITE": 35, "SUGARFREE": 55}
BASE_SCRAP = {"ENROBED": 0.030, "MOLDED": 0.035, "BAR": 0.022, "BITE": 0.026, "SUGARFREE": 0.045}

# --------------------------------------------------------------- materials
# matnr, description, form, season, allergen
FG = [
    ("FG-1001", "Assorted Chocolates 12oz Box", "ENROBED", "ALL", "TREENUT"),
    ("FG-1002", "Assorted Chocolates 18oz Box", "ENROBED", "ALL", "TREENUT"),
    ("FG-1003", "Caramel Collection 9oz Box", "ENROBED", "ALL", "NONE"),
    ("FG-1004", "Nut Cluster Assortment 10oz", "ENROBED", "ALL", "TREENUT"),
    ("FG-1005", "Dark Chocolate Truffle Box 8oz", "ENROBED", "ALL", "NONE"),
    ("FG-1006", "Valentine Heart Box 8oz", "ENROBED", "VAL", "NONE"),
    ("FG-1007", "Valentine Heart Box 14oz", "ENROBED", "VAL", "TREENUT"),
    ("FG-1008", "Holiday Truffle Box 8oz", "ENROBED", "XMS", "NONE"),
    ("FG-2001", "Milk Chocolate Bar Variety 8ct", "BAR", "ALL", "NONE"),
    ("FG-2002", "Peanut Butter Bar 6ct", "BAR", "ALL", "PEANUT"),
    ("FG-2003", "Caramel Crunch Bar 6ct", "BAR", "ALL", "NONE"),
    ("FG-3001", "Mini Bars Bag 16oz", "BITE", "ALL", "NONE"),
    ("FG-3002", "Peanut Butter Cups 12ct", "BITE", "ALL", "PEANUT"),
    ("FG-3003", "Halloween Fun Size Bag 20oz", "BITE", "HAL", "PEANUT"),
    ("FG-3004", "Halloween Candy Mix 24oz", "BITE", "HAL", "NONE"),
    ("FG-4001", "Cream-Filled Shells Box 8oz", "MOLDED", "ALL", "NONE"),
    ("FG-4002", "Easter Solid Bunny 5oz", "MOLDED", "EAS", "NONE"),
    ("FG-4003", "Easter Egg Assortment 10oz", "MOLDED", "EAS", "TREENUT"),
    ("FG-4004", "Easter Basket Bag 14oz", "MOLDED", "EAS", "NONE"),
    ("FG-4005", "Halloween Pumpkin Treats 6oz", "MOLDED", "HAL", "NONE"),
    ("FG-4006", "Holiday Santa Solid 5oz", "MOLDED", "XMS", "NONE"),
    ("FG-4007", "Holiday Assortment Tin 14oz", "MOLDED", "XMS", "TREENUT"),
    ("FG-4008", "Valentine Solid Heart 6oz", "MOLDED", "VAL", "NONE"),
    ("FG-5001", "Sugar-Free Assorted 8oz", "SUGARFREE", "ALL", "TREENUT"),
    ("FG-5002", "Sugar-Free Caramel Bar 6ct", "SUGARFREE", "ALL", "NONE"),
    ("FG-5003", "Sugar-Free Peanut Butter Cups 6ct", "SUGARFREE", "ALL", "PEANUT"),
    ("FG-5004", "Sugar-Free Pecan Delight 8oz", "SUGARFREE", "ALL", "TREENUT"),
    ("FG-5005", "Sugar-Free Easter Bunny 4oz", "SUGARFREE", "EAS", "NONE"),
]
RAW = {  # matnr: (description, type, std price per lb)
    "RM-1001": ("Milk Chocolate Coating", "ROH", 2.15),
    "RM-1003": ("Sugar-Free Chocolate Coating", "ROH", 3.05),
    "RM-2001": ("Cream and Fondant Fill", "ROH", 1.10),
    "RM-2002": ("Caramel and Peanut Butter Fill", "ROH", 1.35),
    "RM-3001": ("Sugar-Free Fill Base", "ROH", 2.10),
    "PK-1001": ("Film and Carton Set", "VERP", 1.80),
    "PK-1002": ("Bag Film", "VERP", 1.60),
}
COMPS = {  # lbs of component per lb of finished good
    "ENROBED": [("RM-1001", 0.50), ("RM-2001", 0.40), ("PK-1001", 0.10)],
    "MOLDED": [("RM-1001", 0.84), ("RM-2001", 0.08), ("PK-1001", 0.08)],
    "BAR": [("RM-1001", 0.54), ("RM-2002", 0.36), ("PK-1001", 0.10)],
    "BITE": [("RM-1001", 0.54), ("RM-2002", 0.36), ("PK-1002", 0.10)],
    "SUGARFREE": [("RM-1003", 0.52), ("RM-3001", 0.38), ("PK-1001", 0.10)],
}
CONVERSION_COST = 0.60
SEASON_W = {"VAL": {10: 2, 11: 3, 12: 2, 1: 0.5}, "EAS": {12: 1, 1: 3, 2: 3, 3: 1},
            "HAL": {6: 1, 7: 3, 8: 3, 9: 1}, "XMS": {8: 1, 9: 3, 10: 3, 11: 1}}
MONTH_LOAD = {1: 0.95, 2: 0.90, 3: 0.80, 4: 0.78, 5: 0.82, 6: 0.95,
              7: 1.05, 8: 1.12, 9: 1.15, 10: 1.05, 11: 1.00, 12: 0.92}

DOWNTIME_REASONS = [  # code, description, category, group
    ("DT100", "Product Changeover", "PLANNED", "Changeover"),
    ("DT110", "Allergen Cleanout", "PLANNED", "Sanitation"),
    ("DT200", "Mechanical Breakdown", "UNPLANNED", "Equipment"),
    ("DT210", "Electrical / Controls Fault", "UNPLANNED", "Equipment"),
    ("DT300", "Raw Material Shortage", "UNPLANNED", "Supply"),
    ("DT310", "Packaging Shortage", "UNPLANNED", "Supply"),
    ("DT400", "Quality Hold", "UNPLANNED", "Quality"),
    ("DT500", "Minor Stoppages", "UNPLANNED", "Equipment"),
    ("DT600", "Planned Maintenance", "PLANNED", "Maintenance"),
    ("DT700", "Scheduled Sanitation", "PLANNED", "Sanitation"),
    ("DT999", "Unclassified", "UNPLANNED", "Unclassified"),
]
SCRAP_REASONS = [
    ("SC01", "Start-up Waste"), ("SC02", "Weight Variance"), ("SC03", "Coating Defect"),
    ("SC04", "Packaging Defect"), ("SC05", "Cooling / Bloom"), ("SC06", "Foreign Material"),
]
SCRAP_SHARE = {
    "ENROBED": [0.25, 0.40, 0.20, 0.10, 0.05],
    "MOLDED": [0.20, 0.15, 0.15, 0.40, 0.10],
    "BAR": [0.30, 0.20, 0.25, 0.15, 0.10],
    "BITE": [0.30, 0.25, 0.25, 0.12, 0.08],
    "SUGARFREE": [0.25, 0.20, 0.20, 0.30, 0.05],
}  # shares for SC02..SC06

KPI_TARGETS = {  # form: OEE, availability, performance, quality, scrap, labor efficiency
    "ENROBED": (0.70, 0.84, 0.90, 0.975, 0.030, 0.85),
    "MOLDED": (0.64, 0.80, 0.88, 0.970, 0.035, 0.80),
    "BAR": (0.74, 0.86, 0.92, 0.980, 0.025, 0.85),
    "BITE": (0.70, 0.84, 0.90, 0.975, 0.028, 0.85),
    "SUGARFREE": (0.58, 0.78, 0.84, 0.955, 0.045, 0.78),
}


def lnorm_mean(rng, mean, sigma=0.5):
    return rng.lognormal(np.log(mean) - sigma ** 2 / 2, sigma)


def month_weights(mat, month):
    season = mat[3]
    if season == "ALL":
        return 2.0
    return SEASON_W[season].get(month, 0.05)


def build_calendar():
    days = pd.date_range(START_DATE, END_DATE, freq="D")
    hol = USFederalHolidayCalendar().holidays(START_DATE, END_DATE)
    return days, set(hol)


def simulate(rate_scale, seed):
    rng = np.random.default_rng(seed)
    days, holidays = build_calendar()
    std_price = {m: p for m, (_, _, p) in RAW.items()}
    fg_cost = {}
    for matnr, desc, form, season, allergen in FG:
        fg_cost[matnr] = round(sum(r * std_price[c] for c, r in COMPS[form]) + CONVERSION_COST, 4)

    shifts, orders, dts, confs, msegs = [], {}, [], [], []
    order_seq, rueck_seq, mblnr_seq, dt_seq = 1000000000, 10000000, 5000000000, 1

    for werks, arbpl, ldesc, form, base_rate, crew in LINES:
        pl = PLANTS[werks]
        rate = base_rate * rate_scale
        forms = LINE_FORMS_OVERRIDE.get((werks, arbpl), LINE_FORMS[form])
        elig = [m for m in FG if m[2] in forms]
        std_hrs_1000 = crew / (rate * STD_OEE_ALLOWANCE) * 1000
        cur, prev_allergen = None, "NONE"
        first_run_date = None

        for ts in days:
            d = ts.date()
            if d in holidays or ts.dayofweek == 6:
                continue
            load = MONTH_LOAD[d.month] * pl["load_adj"]
            if ts.dayofweek == 5:
                probs = {1: np.clip((load - 0.95) / 0.2, 0, 1),
                         2: np.clip((load - 1.05) / 0.2, 0, 1) * 0.5, 3: 0.0}
            else:
                probs = {1: 0.97, 2: np.clip((load - 0.6) / 0.35, 0, 1),
                         3: np.clip((load - 0.95) / 0.25, 0, 1)}
            for s in (1, 2, 3):
                if rng.random() > probs[s]:
                    continue
                if first_run_date is None:
                    first_run_date = d
                is_sat = ts.dayofweek == 5
                # ---- order management
                new_order = cur is None or cur["remaining"] == 0
                co_min = al_min = 0.0
                if new_order:
                    w = np.array([month_weights(m, d.month) for m in elig])
                    if (werks, arbpl) == ("1030", "LN02") and d >= date(2026, 3, 1):
                        w = w * np.array([3.0 if m[4] == "PEANUT" else 1.0 for m in elig])
                    mat = elig[rng.choice(len(elig), p=w / w.sum())]
                    if (werks, arbpl) == ("1030", "LN02") and d >= date(2026, 3, 1):
                        n_sh = int(rng.choice([1, 2], p=[0.6, 0.4]))
                    else:
                        n_sh = int(rng.choice([1, 2, 3, 4], p=[0.20, 0.35, 0.30, 0.15]))
                    order_seq += 1
                    cur = dict(aufnr=str(order_seq), mat=mat, remaining=n_sh, n_planned=n_sh, start=d, end=d,
                               good=0.0, scrap=0.0)
                    orders[cur["aufnr"]] = cur
                    mult = 2.0 if (werks, arbpl) == ("1030", "LN02") and d >= date(2026, 3, 1) else 1.0
                    co_min = lnorm_mean(rng, CHANGEOVER_MEAN[form] * mult, 0.35)
                    if prev_allergen in ("PEANUT", "TREENUT") and mat[4] != prev_allergen:
                        al_min = lnorm_mean(rng, 55 if mult > 1 else 45, 0.3)
                    prev_allergen = mat[4]
                mat = cur["mat"]
                cur["end"] = d
                # ---- downtime events
                ev = []
                if co_min:
                    ev.append(("DT100", co_min))
                if al_min:
                    ev.append(("DT110", al_min))
                bd_mult = pl["bd"] * (1.25 if s == 3 else 1.0)
                lam_bd = (0.45 if form == "SUGARFREE" else 0.40) * bd_mult
                for _ in range(rng.poisson(lam_bd)):
                    code = "DT200" if rng.random() < 0.7 else "DT210"
                    ev.append((code, lnorm_mean(rng, 30, 0.7)))
                for _ in range(rng.poisson(0.12)):
                    ev.append(("DT300" if rng.random() < 0.6 else "DT310", lnorm_mean(rng, 25, 0.6)))
                for _ in range(rng.poisson(0.08)):
                    ev.append(("DT400", lnorm_mean(rng, 35, 0.6)))
                minor = max(0.0, rng.normal(16, 6))
                if minor > 1:
                    ev.append(("DT500", minor))
                if rng.random() < (0.25 if is_sat else 0.04):
                    ev.append(("DT600", lnorm_mean(rng, 90, 0.4)))
                if rng.random() < 0.10:
                    ev.append(("DT700", lnorm_mean(rng, 40, 0.3)))
                tot = sum(m for _, m in ev)
                cap = 0.70 * PLANNED_MIN
                if tot > cap:
                    ev = [(c, m * cap / tot) for c, m in ev]
                    tot = cap
                run_min = PLANNED_MIN - tot
                # ---- speed & output
                trend = 0.0
                if (werks, arbpl) == ("1030", "LN03"):
                    trend = 0.10 * (d - START_DATE).days / 730.0
                shift_f = 0.96 if s == 3 else 1.0
                perf = float(np.clip(rng.normal(pl["perf"] + LINE_PERF_ADJ[form] - trend, 0.035) * shift_f, 0.60, 1.0))
                gross = run_min / 60 * rate * perf
                # ---- scrap by reason
                sh = SCRAP_SHARE[form]
                base = BASE_SCRAP[form] * float(rng.lognormal(-0.03, 0.25))
                rr = {"SC01": 0.008 if (cur["remaining"] == cur["n_planned"]) else 0.0}
                for code, share in zip(["SC02", "SC03", "SC04", "SC05", "SC06"], sh):
                    rr[code] = base * share
                if werks == "1010":
                    if date(2026, 8, 17) <= d <= date(2026, 10, 25):
                        rr["SC04"] *= 4.0
                    elif d > date(2026, 10, 25):
                        rr["SC04"] *= 1.5
                if werks == "1040" and d.month in (6, 7, 8):
                    rr["SC05"] *= 2.2
                scrap_rate = min(sum(rr.values()), 0.20)
                scrap = gross * scrap_rate
                good = gross - scrap
                reason_lbs = {k: gross * v for k, v in rr.items()}
                # ---- labor
                crew_act = crew + pl["crew_extra"] + int(rng.choice([-1, 0, 0, 0, 0, 1]))
                if is_sat:
                    reg_h, ot_h = 0.0, crew_act * 8.0
                else:
                    reg_h = crew_act * 8.0
                    p_ot = float(np.clip(0.08 + (load - 0.8) * 0.5, 0.02, 0.6)) * pl["ot_mult"]
                    ot_h = crew_act * float(rng.choice([0.5, 1, 1.5, 2])) if rng.random() < p_ot else 0.0
                act_h = reg_h + ot_h
                earned = good / 1000 * std_hrs_1000
                shifts.append(dict(WERKS=werks, ARBPL=arbpl, ISDD=d, SHIFT=s, AUFNR=cur["aufnr"], MATNR=mat[0],
                                   FORM=form, IDEAL_RATE=round(rate, 1), PLANNED_MIN=PLANNED_MIN,
                                   DOWNTIME_MIN=round(tot, 2), RUN_MIN=round(run_min, 2),
                                   GROSS_LBS=round(gross, 1), GOOD_LBS=round(good, 1), SCRAP_LBS=round(scrap, 1),
                                   HEADCOUNT=crew_act, REG_HOURS=reg_h, OT_HOURS=round(ot_h, 2),
                                   ACTUAL_HOURS=round(act_h, 2), STD_HOURS_EARNED=round(earned, 2),
                                   NEW_ORDER=int(new_order), SATURDAY=int(is_sat)))
                # ---- downtime event rows (laid out sequentially in the shift)
                n = len(ev)
                gap = (PLANNED_MIN - tot) / (n + 1) if n else 0
                t = 0.0
                for code, mins in ev:
                    t += gap * float(rng.uniform(0.3, 1.0))
                    start = pd.Timestamp(d) + pd.Timedelta(hours=SHIFT_START_HOUR[s], minutes=t)
                    dts.append(dict(EVENT_ID=f"DT{dt_seq:08d}", WERKS=werks, ARBPL=arbpl, ISDD=d, SHIFT=s,
                                    AUFNR=cur["aufnr"], REASON_CODE=code, START_TS=start.strftime("%Y-%m-%d %H:%M"),
                                    DURATION_MIN=round(mins, 1), SOURCE="MES"))
                    dt_seq += 1
                    t += mins
                # ---- SAP confirmation + material documents
                rueck_seq += 1
                confs.append(dict(RUECK=str(rueck_seq), AUFNR=cur["aufnr"], VORNR="0010", WERKS=werks, ARBPL=arbpl,
                                  ISDD=d, BUDAT=d, ERDAT=d + timedelta(days=1 if s == 3 else 0), SCHICHT=s,
                                  LMNGA=round(good, 1), XMNGA=round(scrap, 1), MEINH="LB",
                                  ISM01=round(tot / 60, 2), ISM02=round(run_min / 60, 2), ISM03=round(act_h, 2)))
                mblnr_seq += 1
                zeile = 1
                price = fg_cost[mat[0]]
                rows = [("101", mat[0], good, "", "S")]
                for comp, ratio in COMPS[form]:
                    q = (good + scrap) * ratio * float(rng.lognormal(0, 0.02))
                    rows.append(("261", comp, q, "", "H"))
                gmap = {r[0]: f"{i + 1:04d}" for i, r in enumerate(SCRAP_REASONS)}
                for code, lbs in reason_lbs.items():
                    if lbs > 0.5:
                        rows.append(("551", mat[0], lbs, gmap[code], "H"))
                for bwart, matnr, qty, grund, shkzg in rows:
                    unit_price = price if matnr == mat[0] else std_price[matnr]
                    msegs.append(dict(MBLNR=str(mblnr_seq), MJAHR=d.year, ZEILE=zeile, BUDAT=d,
                                      CPUDT=d + timedelta(days=1 if s == 3 else 0), BWART=bwart, MATNR=matnr,
                                      WERKS=werks, LGORT="0001", MENGE=round(qty, 1), MEINS="LB",
                                      DMBTR=round(qty * unit_price, 2), AUFNR=cur["aufnr"], GRUND=grund,
                                      SHKZG=shkzg))
                    zeile += 1
                cur["good"] += good
                cur["scrap"] += scrap
                cur["remaining"] -= 1
                cur["werks"], cur["arbpl"], cur["rate"] = werks, arbpl, rate

    return shifts, orders, dts, confs, msegs, fg_cost


def build_frames(rate_scale, seed):
    shifts, orders, dts, confs, msegs, fg_cost = simulate(rate_scale, seed)
    return (pd.DataFrame(shifts), orders, pd.DataFrame(dts), pd.DataFrame(confs), pd.DataFrame(msegs), fg_cost)


def trailing_12m_lbs(df):
    d = pd.to_datetime(df["ISDD"])
    return df.loc[d >= pd.Timestamp(2025, 11, 1), "GOOD_LBS"].sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--rate-scale", type=float, default=DEFAULT_RATE_SCALE)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    ap.add_argument("--calibrate", action="store_true", help="print rate scale that hits 55M lbs and exit")
    args = ap.parse_args()

    if args.calibrate:
        sh = build_frames(1.0, args.seed)[0]
        lbs = trailing_12m_lbs(sh)
        print(f"trailing-12M good lbs at scale 1.0: {lbs:,.0f}  -> suggested scale {55e6 / lbs:.4f}")
        return

    out = os.path.abspath(args.out)
    for sub in ("sap_extracts", "reference", "ground_truth"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    rng = np.random.default_rng(args.seed + 1)

    sh, orders, dt, conf, mseg, fg_cost = build_frames(args.rate_scale, args.seed)

    # ------------------------------------------------ ground truth (clean) before DQ injection
    gt = sh.copy()
    gt["AVAILABILITY"] = (gt["RUN_MIN"] / gt["PLANNED_MIN"]).round(4)
    gt["PERFORMANCE"] = (gt["GROSS_LBS"] / (gt["RUN_MIN"] / 60 * gt["IDEAL_RATE"])).round(4)
    gt["QUALITY"] = (gt["GOOD_LBS"] / gt["GROSS_LBS"]).round(4)
    gt["OEE"] = (gt["GOOD_LBS"] / (gt["PLANNED_MIN"] / 60 * gt["IDEAL_RATE"])).round(4)
    gt.to_csv(os.path.join(out, "ground_truth", "shift_fact_clean.csv"), index=False)

    # ------------------------------------------------ orders (AFKO/AFPO)
    last_run = max(o["end"] for o in orders.values())
    orows = []
    for a, o in orders.items():
        est = o["n_planned"] * PLANNED_MIN / 60 * o["rate"] * 0.85
        open_ = o["remaining"] > 0 or o["end"] >= last_run - timedelta(days=1)
        orows.append(dict(AUFNR=a, AUART="PP01", WERKS=o["werks"], ARBPL=o["arbpl"], MATNR=o["mat"][0],
                          PSMNG=round(est, 0), WEMNG=round(o["good"], 1), IASMG=round(o["scrap"], 1), MEINS="LB",
                          GSTRP=o["start"], GLTRP=o["end"], STTXT="REL" if open_ else "TECO"))
    ords = pd.DataFrame(orows)

    # ------------------------------------------------ labor / timekeeping extract
    labor = sh[["WERKS", "ARBPL", "ISDD", "SHIFT", "HEADCOUNT", "REG_HOURS", "OT_HOURS"]].copy()

    # ------------------------------------------------ data-quality injection (documented in answer key)
    dq = []
    # 1) duplicate confirmations (double posting)
    dup_idx = conf.sample(frac=0.004, random_state=args.seed).index
    dups = conf.loc[dup_idx].copy()
    dups["RUECK"] = [str(20000000 + i) for i in range(len(dups))]
    conf = pd.concat([conf, dups], ignore_index=True)
    dq.append(("AFRU", "Duplicate confirmation postings", "all plants", len(dups)))
    # 2) late postings at plant 1030
    m = (conf["WERKS"] == "1030") & (rng.random(len(conf)) < 0.08)
    conf.loc[m, "BUDAT"] = [d + timedelta(days=int(rng.integers(1, 4))) for d in conf.loc[m, "ISDD"]]
    dq.append(("AFRU", "BUDAT later than ISDD (late posting)", "1030", int(m.sum())))
    # 3) negative scrap (reversal without original)
    m = rng.random(len(conf)) < 0.0015
    conf.loc[m, "XMNGA"] = -conf.loc[m, "XMNGA"]
    dq.append(("AFRU", "Negative scrap quantity", "all plants", int(m.sum())))
    # 4) UoM inconsistency: plant 1020 posts in KG Jan-Feb 2026
    m = (mseg["WERKS"] == "1020") & (pd.to_datetime(mseg["BUDAT"]).between("2026-01-01", "2026-02-28"))
    mseg.loc[m, "MENGE"] = (mseg.loc[m, "MENGE"] * 0.45359).round(1)
    mseg.loc[m, "MEINS"] = "KG"
    dq.append(("MSEG", "Quantities posted in KG instead of LB (Jan-Feb 2026)", "1020", int(m.sum())))
    # 5) missing labor records: timekeeping outage plant 1020
    m = (labor["WERKS"] == "1020") & (pd.to_datetime(labor["ISDD"]).between("2025-06-09", "2025-06-22"))
    dq.append(("LABOR", "Missing timekeeping rows (outage 2025-06-09 to 2025-06-22)", "1020", int(m.sum())))
    labor = labor.loc[~m]
    # 6) downtime with no reason selected
    m = rng.random(len(dt)) < 0.03
    dt.loc[m, "REASON_CODE"] = "DT999"
    dq.append(("DOWNTIME", "Operator left reason blank -> DT999 Unclassified", "all plants", int(m.sum())))

    # ------------------------------------------------ write SAP-style extracts
    ex = os.path.join(out, "sap_extracts")
    ords.to_csv(os.path.join(ex, "sap_afko_afpo_production_orders.csv"), index=False)
    conf.to_csv(os.path.join(ex, "sap_afru_confirmations.csv"), index=False)
    mseg.to_csv(os.path.join(ex, "sap_mseg_material_documents.csv"), index=False)
    dt.to_csv(os.path.join(ex, "mes_downtime_events.csv"), index=False)
    labor.to_csv(os.path.join(ex, "hr_labor_by_shift.csv"), index=False)

    # ------------------------------------------------ reference / master data
    ref = os.path.join(out, "reference")
    crhd = pd.DataFrame([dict(WERKS=w, ARBPL=a, KTEXT=desc, VERWE="0001", KOSTL=f"{w}-{a.replace('LN', '4')}00",
                              LINE_FORM=f, IDEAL_RATE_LBHR=round(r * args.rate_scale, 1), STD_CREW=c,
                              STD_HRS_PER_1000LB=round(c / (r * args.rate_scale * STD_OEE_ALLOWANCE) * 1000, 3))
                         for w, a, desc, f, r, c in LINES])
    crhd.to_csv(os.path.join(ref, "sap_crhd_work_centers.csv"), index=False)
    mara = [dict(MATNR=m[0], MAKTX=m[1], MTART="FERT", MATKL=m[2], MEINS="LB", ZSEASON=m[3], ZALLERGEN=m[4],
                 STPRS=fg_cost[m[0]]) for m in FG]
    mara += [dict(MATNR=k, MAKTX=v[0], MTART=v[1], MATKL="COMPONENT", MEINS="LB", ZSEASON="ALL", ZALLERGEN="NONE",
                  STPRS=v[2]) for k, v in RAW.items()]
    pd.DataFrame(mara).to_csv(os.path.join(ref, "sap_mara_makt_materials.csv"), index=False)
    pd.DataFrame([dict(WERKS=k, PLANT_NAME=v["name"], CITY=v["city"], STATE=v["state"]) for k, v in PLANTS.items()]
                 ).to_csv(os.path.join(ref, "ref_plants.csv"), index=False)
    pd.DataFrame(DOWNTIME_REASONS, columns=["REASON_CODE", "DESCRIPTION", "CATEGORY", "LOSS_GROUP"]
                 ).to_csv(os.path.join(ref, "ref_downtime_reasons.csv"), index=False)
    pd.DataFrame([(f"{i + 1:04d}", c, d) for i, (c, d) in enumerate(SCRAP_REASONS)],
                 columns=["GRUND", "SCRAP_CODE", "DESCRIPTION"]).to_csv(os.path.join(ref, "ref_scrap_reasons.csv"), index=False)
    pd.DataFrame([(f, *v) for f, v in KPI_TARGETS.items()],
                 columns=["LINE_FORM", "OEE_TARGET", "AVAILABILITY_TARGET", "PERFORMANCE_TARGET", "QUALITY_TARGET",
                          "SCRAP_RATE_TARGET", "LABOR_EFFICIENCY_TARGET"]).to_csv(os.path.join(ref, "ref_kpi_targets.csv"), index=False)
    days, hol = build_calendar()
    dd = pd.DataFrame({"DATE": days})
    dd["YEAR"], dd["MONTH"], dd["MONTH_NAME"] = dd.DATE.dt.year, dd.DATE.dt.month, dd.DATE.dt.strftime("%b")
    dd["QUARTER"], dd["ISO_WEEK"] = dd.DATE.dt.quarter, dd.DATE.dt.isocalendar().week.astype(int)
    dd["DAY_OF_WEEK"], dd["IS_HOLIDAY"] = dd.DATE.dt.day_name(), dd.DATE.isin(hol).astype(int)
    dd["SEASON_PHASE"] = dd.MONTH.map({1: "Easter Build", 2: "Easter Build", 3: "Low Season", 4: "Low Season",
                                       5: "Low Season", 6: "Halloween Ramp", 7: "Halloween Peak", 8: "Halloween / Christmas Peak",
                                       9: "Christmas Peak", 10: "Christmas / Valentine Ramp", 11: "Valentine Build", 12: "Valentine / Easter Build"})
    dd.to_csv(os.path.join(ref, "ref_calendar.csv"), index=False)
    pd.DataFrame(dq, columns=["TABLE", "ISSUE", "PLANT", "ROWS_AFFECTED"]).to_csv(
        os.path.join(out, "ground_truth", "dq_injection_log.csv"), index=False)

    # ------------------------------------------------ console summary
    t12 = gt[pd.to_datetime(gt.ISDD) >= "2025-11-01"]
    print(f"Shift records: {len(sh):,} | orders: {len(ords):,} | confirmations: {len(conf):,} | "
          f"material doc lines: {len(mseg):,} | downtime events: {len(dt):,}")
    print(f"Trailing-12M good output: {t12.GOOD_LBS.sum() / 1e6:,.1f}M lbs (target ~55M)")
    print("OEE by plant (T12M):")
    print((t12.groupby("WERKS").apply(lambda x: x.GOOD_LBS.sum() / (x.PLANNED_MIN / 60 * x.IDEAL_RATE).sum())).round(3).to_string())


if __name__ == "__main__":
    main()
