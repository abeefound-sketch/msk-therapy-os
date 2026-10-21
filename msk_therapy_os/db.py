"""Database schema definition, connection management, migrations, and seeding."""
from __future__ import annotations

import sqlite3
from msk_therapy_os.anatomy import DEFAULT_ANATOMY_CATALOG
from msk_therapy_os.assessment import DEFAULT_QUESTIONNAIRES
from msk_therapy_os.evidence import DEFAULT_EVIDENCE_CATALOG
from msk_therapy_os.points import init_points_tables


def open_db(path: str) -> sqlite3.Connection:
    """Open connection with foreign key constraints enabled."""
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db(db: sqlite3.Connection) -> None:
    """Create all relational tables required for MSK-Therapy-OS M1."""
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY,
            label TEXT NOT NULL CHECK (case_id LIKE 'DEMO-%')
        );

        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL REFERENCES cases(case_id),
            visit_date TEXT NOT NULL,
            region TEXT NOT NULL,
            pain INTEGER NOT NULL CHECK (pain BETWEEN 0 AND 10),
            rom_deg REAL NOT NULL CHECK (rom_deg BETWEEN 0 AND 360),
            flag TEXT NOT NULL,
            note TEXT NOT NULL,
            disposition TEXT NOT NULL,
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS intakes (
            case_id TEXT PRIMARY KEY REFERENCES cases(case_id),
            age_band TEXT NOT NULL,
            symptom_onset TEXT NOT NULL,
            primary_region TEXT NOT NULL,
            functional_limits TEXT NOT NULL,
            prior_care TEXT NOT NULL,
            operator_role TEXT NOT NULL DEFAULT 'student',
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS rom_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL REFERENCES visits(id),
            motion TEXT NOT NULL,
            side TEXT NOT NULL,
            angle_deg REAL NOT NULL CHECK (angle_deg BETWEEN 0 AND 360),
            method TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS soap_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL REFERENCES visits(id),
            subjective TEXT NOT NULL,
            objective TEXT NOT NULL,
            assessment TEXT NOT NULL,
            plan TEXT NOT NULL,
            author_role TEXT NOT NULL CHECK (author_role IN ('student', 'reviewer')),
            reviewed_by TEXT,
            review_status TEXT NOT NULL DEFAULT 'DRAFT' CHECK (review_status IN ('DRAFT', 'SUPERVISED', 'APPROVED', 'REJECTED')),
            review_notes TEXT,
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS evidence_catalog (
            evidence_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            organization TEXT NOT NULL,
            year INTEGER NOT NULL,
            license TEXT NOT NULL,
            tier INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 4),
            claim_scope TEXT NOT NULL,
            reviewed_on TEXT NOT NULL,
            reviewer TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS anatomy_structures (
            structure_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            source_dataset TEXT NOT NULL,
            bodyparts3d_id TEXT,
            atlas_url TEXT NOT NULL,
            namespace TEXT NOT NULL CHECK (namespace IN ('ANATOMY_EVIDENCE', 'TRADITIONAL_MERIDIAN', 'DIEN_CHAN_REFLEX')),
            evidence_id TEXT REFERENCES evidence_catalog(evidence_id)
        );

        CREATE TABLE IF NOT EXISTS questionnaires (
            item_id TEXT PRIMARY KEY,
            region TEXT NOT NULL,
            scenario_title TEXT NOT NULL,
            question_text TEXT NOT NULL,
            safety_critical INTEGER NOT NULL DEFAULT 0,
            evidence_id TEXT REFERENCES evidence_catalog(evidence_id)
        );

        CREATE TABLE IF NOT EXISTS clinical_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL REFERENCES visits(id),
            structure_id TEXT NOT NULL REFERENCES anatomy_structures(structure_id),
            structure_type TEXT NOT NULL CHECK (structure_type IN ('anatomy', 'acupoint', 'traditional_sen')),
            observation_type TEXT NOT NULL CHECK (observation_type IN ('palpation', 'pain_location', 'trigger_point', 'neurological', 'rom_restriction', 'traditional_pattern')),
            severity INTEGER NOT NULL CHECK (severity BETWEEN 0 AND 10),
            finding TEXT NOT NULL,
            interpretation TEXT NOT NULL,
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS therapy_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL REFERENCES visits(id),
            modality TEXT NOT NULL,
            duration_min INTEGER NOT NULL CHECK (duration_min > 0),
            target_structures TEXT NOT NULL,
            parameters TEXT NOT NULL,
            adverse_reactions TEXT NOT NULL DEFAULT 'none',
            practitioner_role TEXT NOT NULL CHECK (practitioner_role IN ('student', 'reviewer')),
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );
        """
    )
    init_points_tables(db)
    db.commit()


def seed_db(db: sqlite3.Connection) -> None:
    """Seed baseline fictional cases, vetted evidence, anatomy structures, and scenarios."""
    init_db(db)

    # 1. Demo Cases
    db.execute(
        "INSERT OR IGNORE INTO cases (case_id, label) VALUES (?, ?)",
        ("DEMO-NECK-001", "Fictional neck discomfort learning scenario"),
    )
    db.execute(
        "INSERT OR IGNORE INTO cases (case_id, label) VALUES (?, ?)",
        ("DEMO-LOWBACK-002", "Fictional low-back discomfort learning scenario"),
    )

    # 2. Evidence Catalog
    for item in DEFAULT_EVIDENCE_CATALOG:
        db.execute(
            """INSERT OR REPLACE INTO evidence_catalog
               (evidence_id, title, url, organization, year, license, tier, claim_scope, reviewed_on, reviewer)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item.evidence_id,
                item.title,
                item.url,
                item.organization,
                item.year,
                item.license,
                item.tier,
                item.claim_scope,
                item.reviewed_on,
                item.reviewer,
            ),
        )

    # 3. Anatomy Structures
    for item in DEFAULT_ANATOMY_CATALOG:
        db.execute(
            """INSERT OR REPLACE INTO anatomy_structures
               (structure_id, name, region, source_dataset, bodyparts3d_id, atlas_url, namespace, evidence_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item.structure_id,
                item.name,
                item.region,
                item.source_dataset,
                item.bodyparts3d_id,
                item.atlas_url,
                item.namespace,
                item.evidence_id,
            ),
        )

    # 4. Scenario Questionnaires
    for q in DEFAULT_QUESTIONNAIRES:
        db.execute(
            """INSERT OR REPLACE INTO questionnaires
               (item_id, region, scenario_title, question_text, safety_critical, evidence_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                q.item_id,
                q.region,
                q.scenario_title,
                q.question_text,
                1 if q.safety_critical else 0,
                q.evidence_id,
            ),
        )

    # 5. Baseline synthetic intakes for demo cases
    db.execute(
        """
        INSERT OR IGNORE INTO intakes
        (case_id, age_band, symptom_onset, primary_region, functional_limits, prior_care, operator_role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "DEMO-NECK-001",
            "30-49",
            "subacute_4_weeks",
            "neck",
            "limited_cervical_rotation_desk_work",
            "none",
            "student",
        ),
    )
    db.execute(
        """
        INSERT OR IGNORE INTO intakes
        (case_id, age_band, symptom_onset, primary_region, functional_limits, prior_care, operator_role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "DEMO-LOWBACK-002",
            "50-64",
            "chronic_6_months",
            "low_back",
            "stiffness_after_prolonged_sitting",
            "physical_therapy_2024",
            "student",
        ),
    )

    db.commit()


def seed_longitudinal_trajectory(db: sqlite3.Connection) -> None:
    """Seed longitudinal Day 1, Day 3, and Day 7 trajectory for DEMO-NECK-001."""
    existing_visits = db.execute("SELECT COUNT(*) FROM visits WHERE case_id = 'DEMO-NECK-001'").fetchone()[0]
    if existing_visits > 0:
        return

    # Day 1
    c1 = db.execute(
        """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
           VALUES ('DEMO-NECK-001', '2026-10-19', 'neck', 6, 45.0, 'none',
                   'Initial presentation: right-sided cervical and trapezius stiffness after computer work.', 'DOCUMENT_ONLY')"""
    )
    v1_id = c1.lastrowid
    db.execute(
        "INSERT INTO rom_assessments (visit_id, motion, side, angle_deg, method) VALUES (?, 'cervical_rotation', 'right', 45.0, 'goniometer')",
        (v1_id,),
    )
    db.execute(
        """INSERT INTO clinical_observations (visit_id, structure_id, structure_type, observation_type, severity, finding, interpretation)
           VALUES (?, 'STR-CERV-002', 'anatomy', 'trigger_point', 6,
                   'Active myofascial trigger point palpable in right descending trapezius; taut band with localized referral.',
                   'Myofascial trigger point consistent with postural strain; no cervical radiculopathy.')""",
        (v1_id,),
    )
    db.execute(
        """INSERT INTO clinical_observations (visit_id, structure_id, structure_type, observation_type, severity, finding, interpretation)
           VALUES (?, 'ACU-GB21', 'acupoint', 'palpation', 6,
                   'Marked tender nodule at GB21 landmark coinciding with upper trapezius taut band.',
                   'Traditional Gallbladder channel stagnation / myofascial tension correlation.')""",
        (v1_id,),
    )
    db.execute(
        """INSERT INTO therapy_sessions (visit_id, modality, duration_min, target_structures, parameters, adverse_reactions, practitioner_role)
           VALUES (?, 'massage', 20, '["STR-CERV-002", "ACU-GB21"]',
                   'Gentle myofascial trigger point compression 30s x 3', 'none', 'student')""",
        (v1_id,),
    )
    db.execute(
        """INSERT INTO soap_notes (visit_id, subjective, objective, assessment, plan, author_role, reviewed_by, review_status, review_notes)
           VALUES (?,
                   'Ache in right neck/shoulder, worse after 6h computer work.',
                   'Examined structure: Trapezius (STR-CERV-002) and GB21 (ACU-GB21). Taut band with hypertonicity. Cervical rotation right limited to 45 deg.',
                   'Postural cervical myofascial pain syndrome without neurological deficit.',
                   'Gentle active ROM pauses; soft-tissue trigger point release; ergonomic guidance.',
                   'student', 'Clinical Supervisor', 'APPROVED', 'Appropriate observation and safety plan.')""",
        (v1_id,),
    )

    # Day 3
    c2 = db.execute(
        """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
           VALUES ('DEMO-NECK-001', '2026-10-21', 'neck', 4, 55.0, 'none',
                   'Follow-up visit 2: moderate improvement following active pauses and soft-tissue release.', 'DOCUMENT_ONLY')"""
    )
    v2_id = c2.lastrowid
    db.execute(
        "INSERT INTO rom_assessments (visit_id, motion, side, angle_deg, method) VALUES (?, 'cervical_rotation', 'right', 55.0, 'goniometer')",
        (v2_id,),
    )
    db.execute(
        """INSERT INTO clinical_observations (visit_id, structure_id, structure_type, observation_type, severity, finding, interpretation)
           VALUES (?, 'STR-CERV-002', 'anatomy', 'palpation', 4,
                   'Diminished taut band firmness. Palpation discomfort reduced to 4/10.',
                   'Progressing tissue compliance.')""",
        (v2_id,),
    )
    db.execute(
        """INSERT INTO clinical_observations (visit_id, structure_id, structure_type, observation_type, severity, finding, interpretation)
           VALUES (?, 'ACU-GB21', 'acupoint', 'palpation', 4,
                   'Moderate sensitivity persisting at GB21, improved tolerance to firm palpation.',
                   'Decreasing local tenderness.')""",
        (v2_id,),
    )
    db.execute(
        """INSERT INTO therapy_sessions (visit_id, modality, duration_min, target_structures, parameters, adverse_reactions, practitioner_role)
           VALUES (?, 'acupressure', 20, '["ACU-GB21", "STR-CERV-002"]',
                   'Sustained thumb pressure on GB21 and active neck rotation', 'none', 'student')""",
        (v2_id,),
    )
    db.execute(
        """INSERT INTO soap_notes (visit_id, subjective, objective, assessment, plan, author_role, reviewed_by, review_status, review_notes)
           VALUES (?,
                   'Noticeable reduction in stiffness; feels easier to turn head.',
                   'Cervical rotation right 55 deg (+10 deg). Palpation at Trapezius and GB21 moderately improved.',
                   'Subacute postural neck strain showing positive therapeutic trajectory.',
                   'Continue active movement breaks; introduce chin tucks and scapular retractions.',
                   'student', 'Clinical Supervisor', 'APPROVED', 'Positive progress noted; maintain conservative plan.')""",
        (v2_id,),
    )

    # Day 7
    c3 = db.execute(
        """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
           VALUES ('DEMO-NECK-001', '2026-10-25', 'neck', 2, 65.0, 'none',
                   'Follow-up visit 3: 1-week evaluation showing near full symptom resolution and normal ROM.', 'DOCUMENT_ONLY')"""
    )
    v3_id = c3.lastrowid
    db.execute(
        "INSERT INTO rom_assessments (visit_id, motion, side, angle_deg, method) VALUES (?, 'cervical_rotation', 'right', 65.0, 'goniometer')",
        (v3_id,),
    )
    db.execute(
        """INSERT INTO clinical_observations (visit_id, structure_id, structure_type, observation_type, severity, finding, interpretation)
           VALUES (?, 'STR-CERV-002', 'anatomy', 'palpation', 2,
                   'Minimal residual hypertonicity; no active taut band.',
                   'Resolution of acute myofascial spasm.')""",
        (v3_id,),
    )
    db.execute(
        """INSERT INTO clinical_observations (visit_id, structure_id, structure_type, observation_type, severity, finding, interpretation)
           VALUES (?, 'ACU-GB20', 'acupoint', 'palpation', 2,
                   'Mild suboccipital fullness without tenderness.',
                   'Normal suboccipital muscular tone.')""",
        (v3_id,),
    )
    db.execute(
        """INSERT INTO therapy_sessions (visit_id, modality, duration_min, target_structures, parameters, adverse_reactions, practitioner_role)
           VALUES (?, 'massage', 15, '["STR-CERV-002", "ACU-GB20"]',
                   'Light myofascial release and posture education', 'none', 'student')""",
        (v3_id,),
    )
    db.execute(
        """INSERT INTO soap_notes (visit_id, subjective, objective, assessment, plan, author_role, reviewed_by, review_status, review_notes)
           VALUES (?,
                   'Nearly symptom free (pain 2/10). Able to complete full workday without discomfort.',
                   'Cervical rotation right 65 deg (within normal limits). Trapezius and GB20 palpation supple and non-tender.',
                   'Resolved postural neck strain. Patient educated on long-term self-management.',
                   'Independent home ergonomic routine; discharge with self-care advice.',
                   'student', 'Clinical Supervisor', 'APPROVED', 'Goal reached. Case ready for final review.')""",
        (v3_id,),
    )

    db.commit()
