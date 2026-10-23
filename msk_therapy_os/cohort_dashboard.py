"""M6 De-identified Synthetic-First Cohort Research Dashboard & Aggregate Analytics.

Provides longitudinal cohort statistics across pain (VAS), Range of Motion (ROM),
Patient-Reported Outcome Measures (NDI, QuickDASH, RMDQ), missing-data accounting,
CTCAE adverse event trends, and de-identified export capabilities.
Explicitly prohibits causal efficacy assertions on observational datasets.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sqlite3
import statistics
from typing import Any, Dict, List, Optional, Tuple


COHORT_ANALYTICS_DISCLAIMER = (
    "DESCRIPTIVE SYNTHETIC-FIRST OBSERVATIONAL SUMMARY ONLY. Generated from synthetic demo fixtures "
    "for institutional quality improvement and educational analytics. STRICTLY PROHIBITS causal "
    "efficacy assertions, therapy superiority claims, or generalized treatment effectiveness claims "
    "in the absence of randomized, blinded, prospectively controlled clinical trial methodology."
)


def pseudonymize_case_id(case_id: str) -> str:
    """Deterministically pseudonymize a case identifier for research export."""
    h = hashlib.sha256(case_id.encode("utf-8")).hexdigest()[:10].upper()
    return f"SYNTH-{h}"


def get_cohort_summary(db: sqlite3.Connection) -> Dict[str, Any]:
    """Calculate aggregate summary metrics, missingness, and AE rates across all cases."""
    cases = db.execute("SELECT case_id, label FROM cases ORDER BY case_id").fetchall()
    total_cases = len(cases)
    if total_cases == 0:
        return {
            "total_cases": 0,
            "total_visits": 0,
            "pain_analytics": {},
            "rom_analytics": {},
            "prom_analytics": {},
            "adverse_events_summary": {},
            "missingness_report": {"total_cases": 0, "cases_missing_followup": 0},
            "disclaimer": COHORT_ANALYTICS_DISCLAIMER,
        }

    visits_rows = db.execute(
        """SELECT id, case_id, visit_date, region, pain, rom_deg, disposition, created_utc
           FROM visits ORDER BY case_id, visit_date, id"""
    ).fetchall()

    total_visits = len(visits_rows)

    # Group visits by case
    case_visits: Dict[str, List[Any]] = {c[0]: [] for c in cases}
    for v in visits_rows:
        case_visits[v[1]].append(v)

    # 1. Pain (VAS) Analytics
    baseline_pains: List[float] = []
    followup_pains: List[float] = []
    pain_deltas: List[float] = []  # baseline - latest follow-up (positive = improvement)
    cases_with_followup_pain = 0

    # 2. ROM Analytics
    baseline_roms: List[float] = []
    followup_roms: List[float] = []
    rom_deltas: List[float] = []   # latest follow-up - baseline (positive = improvement)
    cases_with_followup_rom = 0

    cases_missing_followup = 0
    visits_missing_rom = 0

    for c_id, v_list in case_visits.items():
        if not v_list:
            cases_missing_followup += 1
            continue
        if len(v_list) < 2:
            cases_missing_followup += 1

        # Check visit-level missingness
        for v in v_list:
            if v[5] is None:
                visits_missing_rom += 1

        # Baseline visit
        v0 = v_list[0]
        p0 = v0[4]
        r0 = v0[5]
        if p0 is not None:
            baseline_pains.append(float(p0))
        if r0 is not None:
            baseline_roms.append(float(r0))

        # Follow-up visit (latest)
        if len(v_list) >= 2:
            v_last = v_list[-1]
            p_last = v_last[4]
            r_last = v_last[5]

            if p0 is not None and p_last is not None:
                followup_pains.append(float(p_last))
                pain_deltas.append(round(float(p0) - float(p_last), 2))
                cases_with_followup_pain += 1

            if r0 is not None and r_last is not None:
                followup_roms.append(float(r_last))
                rom_deltas.append(round(float(r_last) - float(r0), 2))
                cases_with_followup_rom += 1

    pain_summary = {
        "baseline_mean": round(statistics.mean(baseline_pains), 2) if baseline_pains else None,
        "followup_mean": round(statistics.mean(followup_pains), 2) if followup_pains else None,
        "mean_delta": round(statistics.mean(pain_deltas), 2) if pain_deltas else None,
        "median_delta": round(statistics.median(pain_deltas), 2) if pain_deltas else None,
        "cases_evaluated": cases_with_followup_pain,
    }
    if pain_summary["baseline_mean"] and pain_summary["mean_delta"] is not None and pain_summary["baseline_mean"] > 0:
        pain_summary["mean_percentage_reduction"] = round(
            (pain_summary["mean_delta"] / pain_summary["baseline_mean"]) * 100.0, 1
        )
    else:
        pain_summary["mean_percentage_reduction"] = None

    rom_summary = {
        "baseline_mean": round(statistics.mean(baseline_roms), 2) if baseline_roms else None,
        "followup_mean": round(statistics.mean(followup_roms), 2) if followup_roms else None,
        "mean_delta": round(statistics.mean(rom_deltas), 2) if rom_deltas else None,
        "median_delta": round(statistics.median(rom_deltas), 2) if rom_deltas else None,
        "cases_evaluated": cases_with_followup_rom,
    }

    # 3. PROM Analytics
    prom_rows = db.execute(
        """SELECT prom_id, case_id, visit_id, prom_type, percentage_score, administered_at
           FROM patient_proms ORDER BY case_id, administered_at"""
    ).fetchall()

    prom_by_case_type: Dict[Tuple[str, str], List[float]] = {}
    for pr in prom_rows:
        key = (pr[1], pr[3])  # (case_id, prom_type)
        if key not in prom_by_case_type:
            prom_by_case_type[key] = []
        prom_by_case_type[key].append(pr[4])

    prom_instruments = ["NDI", "QuickDASH", "RMDQ"]
    prom_summary: Dict[str, Any] = {}
    for inst in prom_instruments:
        deltas: List[float] = []
        b_scores: List[float] = []
        f_scores: List[float] = []
        cases_with_baseline = 0
        cases_with_paired = 0

        for (c_id, p_type), scores in prom_by_case_type.items():
            if p_type == inst and scores:
                cases_with_baseline += 1
                b_scores.append(scores[0])
                if len(scores) >= 2:
                    cases_with_paired += 1
                    f_scores.append(scores[-1])
                    # For disability questionnaires, baseline - followup = improvement
                    deltas.append(round(scores[0] - scores[-1], 2))

        prom_summary[inst] = {
            "cases_administered": cases_with_baseline,
            "cases_paired_followup": cases_with_paired,
            "baseline_mean_pct": round(statistics.mean(b_scores), 2) if b_scores else None,
            "followup_mean_pct": round(statistics.mean(f_scores), 2) if f_scores else None,
            "mean_disability_reduction_pct": round(statistics.mean(deltas), 2) if deltas else None,
            "followup_completion_rate": round((cases_with_paired / cases_with_baseline * 100.0), 1) if cases_with_baseline > 0 else 0.0,
        }

    # 4. CTCAE Adverse Events Summary
    ae_rows = db.execute(
        """SELECT event_id, case_id, ctcae_grade, resolution_status, event_category
           FROM adverse_events"""
    ).fetchall()
    total_aes = len(ae_rows)
    grade_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    status_counts = {"resolved": 0, "ongoing": 0, "sequelae": 0}
    for ae in ae_rows:
        g = ae[2]
        st = ae[3]
        if g in grade_counts:
            grade_counts[g] += 1
        if st in status_counts:
            status_counts[st] += 1

    ae_summary = {
        "total_events": total_aes,
        "incident_rate_per_visit_pct": round((total_aes / total_visits * 100.0), 2) if total_visits > 0 else 0.0,
        "grade_distribution": grade_counts,
        "resolution_distribution": status_counts,
    }

    # 5. Missingness Accounting
    missingness = {
        "total_cohort_cases": total_cases,
        "cases_missing_followup": cases_missing_followup,
        "case_retention_rate_pct": round(((total_cases - cases_missing_followup) / total_cases * 100.0), 1),
        "total_recorded_visits": total_visits,
        "visits_missing_rom": visits_missing_rom,
        "rom_documentation_rate_pct": round(((total_visits - visits_missing_rom) / total_visits * 100.0), 1) if total_visits > 0 else 0.0,
    }

    return {
        "total_cases": total_cases,
        "total_visits": total_visits,
        "pain_analytics": pain_summary,
        "rom_analytics": rom_summary,
        "prom_analytics": prom_summary,
        "adverse_events_summary": ae_summary,
        "missingness_report": missingness,
        "disclaimer": COHORT_ANALYTICS_DISCLAIMER,
    }


def export_deidentified_cohort(
    db: sqlite3.Connection,
    export_format: str = "json"
) -> Tuple[str, str]:
    """Export de-identified research dataset in json or csv format.

    Returns:
        (content_string, mime_type)
    """
    cases = db.execute("SELECT case_id, label FROM cases ORDER BY case_id").fetchall()
    dataset = []

    for c in cases:
        c_id = c[0]
        pseudo_id = pseudonymize_case_id(c_id)
        visits = db.execute(
            """SELECT id, visit_date, region, pain, rom_deg, disposition
               FROM visits WHERE case_id = ? ORDER BY visit_date, id""",
            (c_id,),
        ).fetchall()

        v_count = len(visits)
        region = visits[0][2] if visits else "unknown"
        p_base = visits[0][3] if visits else None
        p_latest = visits[-1][3] if v_count >= 2 else None
        p_delta = round(float(p_base) - float(p_latest), 2) if (p_base is not None and p_latest is not None) else None

        r_base = visits[0][4] if visits else None
        r_latest = visits[-1][4] if v_count >= 2 else None
        r_delta = round(float(r_latest) - float(r_base), 2) if (r_base is not None and r_latest is not None) else None

        # PROMs
        proms = db.execute(
            """SELECT prom_type, percentage_score FROM patient_proms
               WHERE case_id = ? ORDER BY administered_at""",
            (c_id,),
        ).fetchall()
        prom_type = proms[0][0] if proms else "None"
        prom_base = proms[0][1] if proms else None
        prom_latest = proms[-1][1] if len(proms) >= 2 else None
        prom_delta = round(float(prom_base) - float(prom_latest), 2) if (prom_base is not None and prom_latest is not None) else None

        # Adverse Events
        aes = db.execute(
            "SELECT ctcae_grade FROM adverse_events WHERE case_id = ?",
            (c_id,),
        ).fetchall()
        ae_count = len(aes)
        max_ae_grade = max([a[0] for a in aes]) if aes else 0

        dataset.append({
            "pseudo_case_id": pseudo_id,
            "region": region,
            "visit_count": v_count,
            "baseline_pain_vas": p_base,
            "latest_pain_vas": p_latest,
            "pain_delta": p_delta,
            "baseline_rom_deg": r_base,
            "latest_rom_deg": r_latest,
            "rom_delta": r_delta,
            "prom_instrument": prom_type,
            "prom_baseline_score_pct": prom_base,
            "prom_latest_score_pct": prom_latest,
            "prom_improvement_delta": prom_delta,
            "adverse_events_count": ae_count,
            "max_ctcae_grade": max_ae_grade,
        })

    if export_format.lower() == "csv":
        output = io.StringIO()
        fieldnames = [
            "pseudo_case_id",
            "region",
            "visit_count",
            "baseline_pain_vas",
            "latest_pain_vas",
            "pain_delta",
            "baseline_rom_deg",
            "latest_rom_deg",
            "rom_delta",
            "prom_instrument",
            "prom_baseline_score_pct",
            "prom_latest_score_pct",
            "prom_improvement_delta",
            "adverse_events_count",
            "max_ctcae_grade",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in dataset:
            writer.writerow(row)
        return output.getvalue(), "text/csv; charset=utf-8"

    # Default JSON
    export_payload = {
        "metadata": {
            "study_type": "SYNTHETIC_COHORT_DEIDENTIFIED_RESEARCH_EXPORT",
            "total_records": len(dataset),
            "disclaimer": COHORT_ANALYTICS_DISCLAIMER,
        },
        "records": dataset,
    }
    return json.dumps(export_payload, indent=2), "application/json; charset=utf-8"
