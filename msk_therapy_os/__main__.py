"""MSK-Therapy-OS CLI: Constraint-First Musculoskeletal Learning and Safety Gating."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sqlite3
import sys

from msk_therapy_os.anatomy import (
    DEFAULT_ATLAS_BASE,
    get_anatomy_by_id,
    list_anatomy,
)
from msk_therapy_os.assessment import (
    VALID_AGE_BANDS,
    VALID_METHODS,
    VALID_REGIONS,
    VALID_SIDES,
    get_intake,
    get_visit_rom,
    list_questionnaires,
    record_intake,
    record_rom,
)
from msk_therapy_os.db import init_db, open_db, seed_db
from msk_therapy_os.evidence import get_evidence_by_id, list_evidence
from msk_therapy_os.models import KnowledgeNamespace, ReviewStatus, UserRole
from msk_therapy_os.reporting import generate_case_report
from msk_therapy_os.safety import RED_FLAGS, evaluate_safety
from msk_therapy_os.soap import (
    create_soap_note,
    get_soap_notes_for_visit,
    review_soap_note,
)
from msk_therapy_os.auth import bootstrap_initial_admin, get_user_count, create_user
from msk_therapy_os.points import (
    backup_database,
    restore_database_safely,
    get_backup_signing_key,
    rotate_backup_signing_key,
    export_backup_signing_key,
)

# Exported symbols for full backward compatibility with M0 unit tests
ATLAS = DEFAULT_ATLAS_BASE
DEFAULT_DB = "2data/demo.sqlite3" if Path("2data/demo.sqlite3").exists() else "demo.sqlite3"


def init(db: sqlite3.Connection) -> None:
    """Initialize database schema."""
    init_db(db)


def seed_demo(db: sqlite3.Connection) -> None:
    """Seed synthetic demo cases, evidence, and anatomy catalog."""
    seed_db(db)


def add_visit(
    db: sqlite3.Connection,
    *,
    case: str,
    when: str,
    pain: int,
    rom: float,
    region: str,
    flag: str,
    note: str,
) -> str:
    """Add a synthetic visit record, gated by the rule-based safety engine."""
    if not case.startswith("DEMO-"):
        raise ValueError("Synthetic DEMO-* case identifiers only; no real patients")
    date.fromisoformat(when)
    if pain not in range(11):
        raise ValueError("pain must be an integer between 0 and 10")
    if not (0 <= rom <= 360):
        raise ValueError("rom must be in degrees between 0 and 360")
    if flag not in RED_FLAGS:
        raise ValueError(f"flag must be one of: {', '.join(RED_FLAGS)}")
    if not region or not region.strip():
        raise ValueError("region is required")
    if len(note) > 500:
        raise ValueError("note must be <= 500 characters")
    if db.execute("SELECT 1 FROM cases WHERE case_id = ?", (case,)).fetchone() is None:
        raise ValueError("unknown DEMO case; run seed-demo")

    eval_result = evaluate_safety(flag=flag)
    disposition = eval_result.disposition.value

    db.execute(
        """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (case, when, region.strip(), pain, rom, flag, note, disposition),
    )
    db.commit()
    return disposition


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="msk_therapy_os",
        description="MSK-Therapy-OS: Constraint-First Synthetic Learning & Longitudinal Documentation",
    )
    sub = p.add_subparsers(dest="action", required=True)

    # 1. M0 Backward Compatible Subcommands
    for act in ["init", "seed-demo", "cases"]:
        cmd = sub.add_parser(act)
        cmd.add_argument("--db", default=DEFAULT_DB)

    tl = sub.add_parser("timeline")
    tl.add_argument("--db", default=DEFAULT_DB)
    tl.add_argument("--case", required=True)

    vis = sub.add_parser("add-visit")
    vis.add_argument("--db", default=DEFAULT_DB)
    vis.add_argument("--case", required=True)
    vis.add_argument("--date", dest="when", required=True)
    vis.add_argument("--pain", type=int, required=True)
    vis.add_argument("--rom", type=float, required=True)
    vis.add_argument("--region", required=True)
    vis.add_argument("--flag", required=True, choices=RED_FLAGS)
    vis.add_argument("--note", default="")

    sub.add_parser("atlas")

    # 2. M1 Safety Gating Screen
    safety_cmd = sub.add_parser("screen-safety", help="Screen red flags and modality contraindications")
    safety_cmd.add_argument("--flag", default="none", choices=RED_FLAGS)
    safety_cmd.add_argument("--modality", choices=["manual_massage", "dds_device", "passive_stretch", "spinal_manipulation"])
    safety_cmd.add_argument("--contraindication", action="append", help="Potential contraindication (can repeat)")

    # 3. M1 Structured Intake
    intake_cmd = sub.add_parser("intake", help="Record structured clinical intake for synthetic case")
    intake_cmd.add_argument("--db", default=DEFAULT_DB)
    intake_cmd.add_argument("--case", required=True)
    intake_cmd.add_argument("--age", required=True, choices=VALID_AGE_BANDS)
    intake_cmd.add_argument("--onset", required=True, help="e.g. acute_1_week, chronic_3_months")
    intake_cmd.add_argument("--region", required=True, choices=VALID_REGIONS)
    intake_cmd.add_argument("--limits", required=True, help="Functional limitations reported")
    intake_cmd.add_argument("--prior-care", default="none", help="Prior medical/physical care")
    intake_cmd.add_argument("--role", default="student", choices=["student", "reviewer"])

    show_intake = sub.add_parser("show-intake", help="View structured intake for synthetic case")
    show_intake.add_argument("--db", default=DEFAULT_DB)
    show_intake.add_argument("--case", required=True)

    # 4. M1 Objective ROM
    rom_cmd = sub.add_parser("add-rom", help="Record structured joint-specific ROM measurement")
    rom_cmd.add_argument("--db", default=DEFAULT_DB)
    rom_cmd.add_argument("--visit-id", type=int, required=True)
    rom_cmd.add_argument("--motion", required=True, help="e.g. cervical_flexion, lumbar_extension")
    rom_cmd.add_argument("--side", required=True, choices=VALID_SIDES)
    rom_cmd.add_argument("--angle", type=float, required=True, help="Angle in degrees (0-360)")
    rom_cmd.add_argument("--method", required=True, choices=VALID_METHODS)

    # 5. M1 Structured SOAP & Review Workflow
    soap_cmd = sub.add_parser("add-soap", help="Draft or record structured SOAP note")
    soap_cmd.add_argument("--db", default=DEFAULT_DB)
    soap_cmd.add_argument("--visit-id", type=int, required=True)
    soap_cmd.add_argument("--s", dest="subjective", required=True, help="Subjective findings")
    soap_cmd.add_argument("--o", dest="objective", required=True, help="Objective findings")
    soap_cmd.add_argument("--a", dest="assessment", required=True, help="Assessment hypothesis (educational only)")
    soap_cmd.add_argument("--p", dest="plan", required=True, help="Plan / Educational procedure")
    soap_cmd.add_argument("--role", default="student", choices=["student", "reviewer"])

    review_cmd = sub.add_parser("review-soap", help="Clinical supervisor review and sign-off of SOAP note")
    review_cmd.add_argument("--db", default=DEFAULT_DB)
    review_cmd.add_argument("--soap-id", type=int, required=True)
    review_cmd.add_argument("--reviewer", required=True, help="Supervisor name / identifier")
    review_cmd.add_argument("--role", default="reviewer", choices=["reviewer", "student"])
    review_cmd.add_argument("--decision", required=True, choices=["APPROVED", "REJECTED", "SUPERVISED"])
    review_cmd.add_argument("--feedback", default="", help="Supervisory comments / required corrections")

    # 6. M1 Offline Report
    rep_cmd = sub.add_parser("report", help="Generate full offline clinical education report")
    rep_cmd.add_argument("--db", default=DEFAULT_DB)
    rep_cmd.add_argument("--case", required=True)
    rep_cmd.add_argument("--out", help="Optional output path to write markdown report file")

    # 7. M1 Evidence Catalog
    ev_cmd = sub.add_parser("evidence", help="Browse curated evidence library and citations")
    ev_cmd.add_argument("--db", default=DEFAULT_DB)
    ev_cmd.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Filter by evidence tier")
    ev_cmd.add_argument("--id", dest="evidence_id", help="Lookup specific evidence ID")

    # 8. M1 Anatomy Adapter
    anat_cmd = sub.add_parser("anatomy", help="Browse anatomy structures, BodyParts3D IDs, and traditional namespaces")
    anat_cmd.add_argument("--db", default=DEFAULT_DB)
    anat_cmd.add_argument("--region", help="Filter by anatomical region (neck, low_back, face, etc.)")
    anat_cmd.add_argument("--namespace", choices=[ns.value for ns in KnowledgeNamespace], help="Filter by namespace")
    anat_cmd.add_argument("--id", dest="structure_id", help="Lookup specific structure ID")

    # 9. M1 Scenario Questionnaires
    q_cmd = sub.add_parser("questionnaires", help="List scenario-based assessment questionnaires")
    q_cmd.add_argument("--db", default=DEFAULT_DB)
    q_cmd.add_argument("--region", help="Filter by body region")

    # 10. M2 Body-Map Web Server
    srv = sub.add_parser("serve", help="Launch local HTTP web server for Milestone M2 Body-Map UI")
    srv.add_argument("--db", default=DEFAULT_DB)
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8080)

    # 11. Security & Admin Bootstrap Commands
    bs_cmd = sub.add_parser("bootstrap-admin", help="Bootstrap root administrator on a clean database")
    bs_cmd.add_argument("--db", default=DEFAULT_DB)
    bs_cmd.add_argument("--username", required=True, help="Administrator username")
    bs_cmd.add_argument("--password", required=True, help="Strong administrator password (>= 8 chars)")
    bs_cmd.add_argument("--name", default="Root Administrator", help="Display name")

    sub.add_parser("export-hmac-key", help="Export active HMAC backup authentication key")
    sub.add_parser("rotate-hmac-key", help="Rotate HMAC backup authentication key and archive old key to history")

    em_cmd = sub.add_parser("emergency-restore", help="Emergency break-glass SQLite database restore")
    em_cmd.add_argument("--db", default=DEFAULT_DB)
    em_cmd.add_argument("--backup", required=True, help="Path to backup sqlite3 file")
    em_cmd.add_argument("--reason", required=True, help="Detailed justification for break-glass restore")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    print("DEMO ONLY: Synthetic educational data only. Do not enter real patient data.")

    if args.action == "atlas":
        print(ATLAS)
        return 0

    if args.action == "screen-safety":
        res = evaluate_safety(
            flag=args.flag,
            modality=args.modality,
            contraindications=args.contraindication,
        )
        print(f"DISPOSITION: {res.disposition.value}")
        print(f"Safe to proceed: {res.is_safe_to_proceed}")
        if res.flags_triggered:
            print(f"Flags Triggered: {', '.join(res.flags_triggered)}")
        if res.contraindications_triggered:
            print(f"Contraindications Triggered: {', '.join(res.contraindications_triggered)}")
        print(f"Instructions: {res.escalation_instructions}")
        print(f"Clinical Rationale: {res.clinical_rationale}")
        print(f"Evidence Source: {res.evidence_id}")
        return 0

    if args.action == "serve":
        if not Path(args.db).exists():
            print("Database missing. Run init first.")
            return 2
        from msk_therapy_os.server import run_server
        run_server(db_path=args.db, host=args.host, port=args.port)
        return 0

    if args.action == "export-hmac-key":
        key_hex = export_backup_signing_key()
        print(f"ACTIVE_HMAC_KEY: {key_hex}")
        return 0

    if args.action == "rotate-hmac-key":
        new_k = rotate_backup_signing_key()
        print(f"HMAC key rotated successfully. New key: {new_k.hex()}")
        return 0

    if args.action == "emergency-restore":
        res = restore_database_safely(
            target_db_path=args.db,
            backup_source_path=args.backup,
            require_hmac=False,
            emergency_override=True,
            incident_reason=args.reason
        )
        print(f"Emergency restore complete: {res}")
        return 0

    if args.action != "init" and not Path(args.db).exists():
        print("Database missing. Run init first.")
        return 2

    with open_db(args.db) as db:
        try:
            if args.action == "init":
                init(db)
                print("Initialized synthetic-only demo database with M1 schema.")
            elif args.action == "seed-demo":
                seed_demo(db)
                print("Seeded fictional cases, evidence catalog, anatomy mappings, and questionnaires.")
            elif args.action == "cases":
                for row in db.execute("SELECT case_id, label FROM cases ORDER BY case_id"):
                    print(" | ".join(str(v) for v in row))
            elif args.action == "add-visit":
                result = add_visit(
                    db,
                    case=args.case,
                    when=args.when,
                    pain=args.pain,
                    rom=args.rom,
                    region=args.region,
                    flag=args.flag,
                    note=args.note,
                )
                print(result)
                if result == "STOP_AND_REFER":
                    print(
                        "Red flag reported: do not proceed with manual/electrical interventions; seek qualified medical assessment."
                    )
            elif args.action == "timeline":
                if not args.case.startswith("DEMO-"):
                    raise ValueError("Synthetic DEMO-* cases only")
                rows = db.execute(
                    """SELECT visit_date, region, pain, rom_deg, flag, disposition
                       FROM visits WHERE case_id=? ORDER BY visit_date, id""",
                    (args.case,),
                ).fetchall()
                if not rows:
                    print("No synthetic visits found")
                for row in rows:
                    print(
                        f"{row[0]} | {row[1]} | pain={row[2]}/10 | ROM={row[3]:g} deg | {row[4]} | {row[5]}"
                    )
            elif args.action == "intake":
                record_intake(
                    db,
                    case_id=args.case,
                    age_band=args.age,
                    symptom_onset=args.onset,
                    primary_region=args.region,
                    functional_limits=args.limits,
                    prior_care=args.prior_care,
                    operator_role=args.role,
                )
                print(f"Recorded structured intake for case {args.case} (Role: {args.role}).")
            elif args.action == "show-intake":
                rec = get_intake(db, args.case)
                if not rec:
                    print(f"No intake recorded for case {args.case}.")
                else:
                    print(f"Case: {rec.case_id}")
                    print(f"Age Band: {rec.age_band} | Region: {rec.primary_region}")
                    print(f"Onset: {rec.symptom_onset}")
                    print(f"Functional Limits: {rec.functional_limits}")
                    print(f"Prior Care: {rec.prior_care}")
                    print(f"Recorded By: {rec.operator_role} on {rec.created_utc}")
            elif args.action == "add-rom":
                rom_id = record_rom(
                    db,
                    visit_id=args.visit_id,
                    motion=args.motion,
                    side=args.side,
                    angle_deg=args.angle,
                    method=args.method,
                )
                print(f"Recorded ROM measurement #{rom_id} for Visit #{args.visit_id}: {args.motion} ({args.side}) = {args.angle:g}° [{args.method}].")
            elif args.action == "add-soap":
                soap_id = create_soap_note(
                    db,
                    visit_id=args.visit_id,
                    subjective=args.subjective,
                    objective=args.objective,
                    assessment=args.assessment,
                    plan=args.plan,
                    author_role=args.role,
                )
                print(f"Created SOAP note #{soap_id} for Visit #{args.visit_id} (Author Role: {args.role}).")
            elif args.action == "review-soap":
                review_soap_note(
                    db,
                    soap_id=args.soap_id,
                    reviewer_name=args.reviewer,
                    reviewer_role=args.role,
                    decision=args.decision,
                    feedback=args.feedback,
                )
                print(f"Updated SOAP note #{args.soap_id}: Decision = {args.decision} by {args.reviewer}.")
            elif args.action == "report":
                report_content = generate_case_report(db, args.case)
                if args.out:
                    Path(args.out).write_text(report_content, encoding="utf-8")
                    print(f"Report written to {args.out}")
                else:
                    print(report_content)
            elif args.action == "evidence":
                if args.evidence_id:
                    item = get_evidence_by_id(db, args.evidence_id)
                    if not item:
                        print(f"Evidence ID '{args.evidence_id}' not found.")
                    else:
                        print(f"[{item.evidence_id}] (Tier {item.tier}) {item.title}")
                        print(f"Organization: {item.organization} ({item.year}) | License: {item.license}")
                        print(f"Scope: {item.claim_scope}")
                        print(f"URL: {item.url}")
                        print(f"Reviewed: {item.reviewed_on} by {item.reviewer}")
                else:
                    items = list_evidence(db, tier=args.tier)
                    for item in items:
                        print(f"[{item.evidence_id}] Tier {item.tier} | {item.title} ({item.year}) | {item.organization}")
            elif args.action == "anatomy":
                if args.structure_id:
                    struct = get_anatomy_by_id(db, args.structure_id)
                    if not struct:
                        print(f"Structure ID '{args.structure_id}' not found.")
                    else:
                        print(f"[{struct.structure_id}] {struct.name} ({struct.region})")
                        print(f"Namespace: {struct.namespace} | Source: {struct.source_dataset}")
                        if struct.bodyparts3d_id:
                            print(f"BodyParts3D FMA ID: {struct.bodyparts3d_id}")
                        print(f"Atlas Link: {struct.atlas_url}")
                        print(f"Evidence Ref: {struct.evidence_id}")
                        if struct.namespace != KnowledgeNamespace.ANATOMY_EVIDENCE.value:
                            print("⚠️ NOTE: Traditional/reflexology schema. Not physically equivalent to nerves/vessels.")
                else:
                    structs = list_anatomy(db, region=args.region, namespace=args.namespace)
                    for s in structs:
                        bp_str = f" [BP3D: {s.bodyparts3d_id}]" if s.bodyparts3d_id else ""
                        print(f"[{s.structure_id}] ({s.namespace}) {s.name} - {s.region}{bp_str}")
            elif args.action == "questionnaires":
                qs = list_questionnaires(db, region=args.region)
                for q in qs:
                    crit_tag = "[CRITICAL SAFETY]" if q.safety_critical else "[CLINICAL ASSESSMENT]"
                    print(f"[{q.item_id}] {crit_tag} ({q.region}) {q.scenario_title}")
                    print(f"  Q: {q.question_text}")
                    print(f"  Ref: {q.evidence_id}")
            elif args.action == "bootstrap-admin":
                admin = bootstrap_initial_admin(
                    db,
                    username=args.username,
                    password=args.password,
                    display_name=args.name,
                )
                print(f"Successfully bootstrapped initial administrator: {admin['username']} ({admin['user_id']})")
        except (ValueError, PermissionError, sqlite3.Error) as error:
            print(f"ERROR: {error}")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
