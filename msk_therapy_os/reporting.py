"""Offline report generation with longitudinal progress, method comparability, and missing-data audits."""
from __future__ import annotations

import sqlite3
from typing import List, Tuple
from msk_therapy_os.assessment import get_intake, get_visit_rom
from msk_therapy_os.soap import get_soap_notes_for_visit


def generate_case_report(db: sqlite3.Connection, case_id: str) -> str:
    """Generate an offline structured clinical education report in Markdown.

    Emphasizes synthetic-only boundaries, method comparability, and audit completeness.
    """
    if not case_id.startswith("DEMO-"):
        raise ValueError("Synthetic DEMO-* cases only; real patient reports prohibited.")

    case_row = db.execute("SELECT case_id, label FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if not case_row:
        raise ValueError(f"Case '{case_id}' not found.")

    cid, label = case_row
    intake = get_intake(db, case_id)
    visits = db.execute(
        """SELECT id, visit_date, region, pain, rom_deg, flag, note, disposition, created_utc
           FROM visits WHERE case_id = ? ORDER BY visit_date, id""",
        (case_id,),
    ).fetchall()

    lines: List[str] = []
    lines.append("================================================================================")
    lines.append("⚠️  MSK-THERAPY-OS: SYNTHETIC CLINICAL LEARNING REPORT - DEMO ONLY  ⚠️")
    lines.append("   CONFIDENTIALITY / SAFETY NOTICE: FICTIONAL PATIENT SCENARIO ONLY.")
    lines.append("   NOT SUITABLE FOR ACTUAL DIAGNOSIS, THERAPY PRESCRIPTION, OR DEVICE CONTROL.")
    lines.append("================================================================================")
    lines.append("")
    lines.append(f"# Case Report: {cid}")
    lines.append(f"**Description:** {label}")
    lines.append("")

    # Intake section & missing-data audit
    lines.append("## 1. Intake & Baseline Screening")
    if intake:
        lines.append(f"- **Age Band:** {intake.age_band}")
        lines.append(f"- **Primary Region:** {intake.primary_region}")
        lines.append(f"- **Symptom Onset:** {intake.symptom_onset}")
        lines.append(f"- **Functional Limits:** {intake.functional_limits}")
        lines.append(f"- **Prior Care:** {intake.prior_care}")
        lines.append(f"- **Recorded By (Role):** {intake.operator_role}")
        lines.append(f"- **Timestamp:** {intake.created_utc}")
    else:
        lines.append("> ⚠️ **AUDIT WARNING: MISSING INTAKE.** No formal intake questionnaire recorded for this case.")
    lines.append("")

    # Visits section
    lines.append("## 2. Longitudinal Visit Timeline")
    if not visits:
        lines.append("No visits recorded for this case.")
        lines.append("")
    else:
        lines.append("| Visit ID | Date | Region | Pain (0-10) | Gross ROM | Red Flag | Disposition |")
        lines.append("|---|---|---|---|---|---|---|")
        for v in visits:
            lines.append(
                f"| #{v[0]} | {v[1]} | {v[2]} | {v[3]}/10 | {v[4]:g}° | {v[5]} | **{v[7]}** |"
            )
        lines.append("")

        # Method comparability and progress trends
        lines.append("## 3. Objective Progress & Measurement Comparability Analysis")
        all_rom_records: List[Tuple[int, str, float, str]] = []  # (visit_id, motion, angle, method)
        for v in visits:
            v_id = v[0]
            detailed_roms = get_visit_rom(db, v_id)
            for r in detailed_roms:
                all_rom_records.append((v_id, f"{r.motion}_{r.side}", r.angle_deg, r.method))

        if len(visits) > 1:
            first_v = visits[0]
            last_v = visits[-1]
            pain_delta = last_v[3] - first_v[3]
            gross_rom_delta = last_v[4] - first_v[4]
            lines.append(f"- **Gross Pain Trend:** Baseline {first_v[3]}/10 → Latest {last_v[3]}/10 (Δ = {pain_delta:+d})")
            lines.append(f"- **Gross ROM Trend:** Baseline {first_v[4]:g}° → Latest {last_v[4]:g}° (Δ = {gross_rom_delta:+g}°)")

        if all_rom_records:
            # Check comparability of methods
            methods_used = set(r[3] for r in all_rom_records)
            if len(methods_used) > 1:
                lines.append(
                    f"> ⚠️ **METHOD COMPARABILITY ALERT:** Multiple ROM instruments recorded ({', '.join(sorted(methods_used))}). "
                    "Inclinometer, goniometer, and visual estimation measurements cannot be directly compared mathematically."
                )
            lines.append("")
            lines.append("### Detailed Joint-Specific ROM Records:")
            for r in all_rom_records:
                lines.append(f"- Visit #{r[0]}: {r[1]} = {r[2]:g}° (Instrument: {r[3]})")
        else:
            lines.append("> ℹ️ No joint-specific structured ROM assessments entered (only gross summary ROM recorded).")
        lines.append("")

        # Detailed SOAP Notes & Supervision Review Audit
        lines.append("## 4. Structured SOAP Records & Clinical Supervisory Reviews")
        missing_soap_visits = []
        for v in visits:
            v_id = v[0]
            v_date = v[1]
            soaps = get_soap_notes_for_visit(db, v_id)
            if not soaps:
                missing_soap_visits.append(f"#{v_id} ({v_date})")
                continue

            for s in soaps:
                lines.append(f"### Visit #{v_id} ({v_date}) - SOAP Record #{s.id}")
                lines.append(f"- **Author Role:** `{s.author_role}` | **Review Status:** `[{s.review_status}]`")
                if s.reviewed_by:
                    lines.append(f"- **Supervisory Reviewer:** {s.reviewed_by}")
                if s.review_notes:
                    lines.append(f"- **Supervisory Feedback:** *{s.review_notes}*")
                lines.append("")
                lines.append("**S (Subjective):**")
                lines.append(s.subjective)
                lines.append("")
                lines.append("**O (Objective):**")
                lines.append(s.objective)
                lines.append("")
                lines.append("**A (Assessment - Educational Hypothesis Only; No Medical Diagnosis):**")
                lines.append(s.assessment)
                lines.append("")
                lines.append("**P (Plan - Non-Invasive Educational Modality / Referral):**")
                lines.append(s.plan)
                lines.append("")
                lines.append("---")

        if missing_soap_visits:
            lines.append(
                f"> ⚠️ **DOCUMENTATION GAP:** The following visits lack structured SOAP documentation: {', '.join(missing_soap_visits)}."
            )
        lines.append("")

    lines.append("## 5. Clinical Safety & Governance Sign-off")
    lines.append("```")
    lines.append("Supervising Instructor / Reviewer Signature: ____________________________________")
    lines.append("Review Date: ________________________   Status: [ ] APPROVED   [ ] REVISION REQUIRED")
    lines.append("Clinical Clearance Disclaimer: This educational review does not convey medical advice.")
    lines.append("```")

    return "\n".join(lines)
