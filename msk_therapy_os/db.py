"""Database schema definition, connection management, migrations, and seeding."""
from __future__ import annotations

import sqlite3
from msk_therapy_os.anatomy import DEFAULT_ANATOMY_CATALOG
from msk_therapy_os.assessment import DEFAULT_QUESTIONNAIRES
from msk_therapy_os.evidence import DEFAULT_EVIDENCE_CATALOG


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
        """
    )
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
