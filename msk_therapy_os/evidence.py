"""Curated evidence library with explicit tiers, citations, and provenance."""
from __future__ import annotations

import sqlite3
from typing import List, Optional
from msk_therapy_os.models import EvidenceRecord, EvidenceTier


# Curated, human-reviewed evidence records with provenance and tiering.
DEFAULT_EVIDENCE_CATALOG: List[EvidenceRecord] = [
    EvidenceRecord(
        evidence_id="EVID-G-001",
        title="NICE Guideline NG59: Low back pain and sciatica in over 16s: assessment and management",
        url="https://www.nice.org.uk/guidance/ng59",
        organization="National Institute for Health and Care Excellence (NICE)",
        year=2020,
        license="Open Government Licence v3.0",
        tier=EvidenceTier.TIER_1_CLINICAL_GUIDELINE.value,
        claim_scope="Assessment of red flags (cauda equina, spinal fracture, cancer, infection) and conservative MSK management limits.",
        reviewed_on="2026-10-19",
        reviewer="Clinical Governance Review Panel",
    ),
    EvidenceRecord(
        evidence_id="EVID-G-002",
        title="International Framework for Red Flags for Potential Serious Spinal Pathologies",
        url="https://doi.org/10.2522/ptj.20190687",
        organization="IFOMPT / Journal of Orthopaedic & Sports Physical Therapy (JOSPT)",
        year=2020,
        license="Peer-reviewed Open Access / Academic citation",
        tier=EvidenceTier.TIER_1_CLINICAL_GUIDELINE.value,
        claim_scope="Red flags screening framework: progressive weakness, saddle anesthesia, bowel/bladder dysfunction, unexplained weight loss, unremitting night pain.",
        reviewed_on="2026-10-19",
        reviewer="Clinical Governance Review Panel",
    ),
    EvidenceRecord(
        evidence_id="EVID-G-003",
        title="Guidance for Industry and FDA Staff: Powered Muscle Stimulator 510(k) Guidance",
        url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/guidance-document-powered-muscle-stimulator-510ks-guidance-industry-fda-reviewersstaff-and",
        organization="US Food and Drug Administration (FDA)",
        year=2022,
        license="US Public Domain",
        tier=EvidenceTier.TIER_1_CLINICAL_GUIDELINE.value,
        claim_scope="Electrical stimulation device contraindications: cardiac pacemakers, trans-thoracic placement, carotid sinus, active malignancy, pregnancy, damaged skin.",
        reviewed_on="2026-10-19",
        reviewer="Clinical Governance Review Panel",
    ),
    EvidenceRecord(
        evidence_id="EVID-A-001",
        title="Open Anatomy Atlas: Web-based 3D Human Anatomy Viewer",
        url="https://github.com/CognitionLabSNUC/open-anatomy-atlas",
        organization="Cognition Lab, Seoul National University",
        year=2024,
        license="MIT License",
        tier=EvidenceTier.TIER_2_PEER_REVIEWED_ANATOMY.value,
        claim_scope="3D web viewer interface and BodyParts3D coordinate mapping for educational anatomical structure visualization.",
        reviewed_on="2026-10-19",
        reviewer="Anatomical Science Working Group",
    ),
    EvidenceRecord(
        evidence_id="EVID-A-002",
        title="BodyParts3D: 3D Anatomical Concepts Database Release 4.0",
        url="https://lifesciencedb.jp/bp3d/",
        organization="Database Center for Life Science (DBCLS), Japan",
        year=2022,
        license="Creative Commons Attribution 2.1 Japan (CC BY 2.1 JP)",
        tier=EvidenceTier.TIER_2_PEER_REVIEWED_ANATOMY.value,
        claim_scope="Standardized anatomical ontology IDs (FMA identifiers) and segment meshes for cervical, thoracic, lumbar spine and peripheral muscles.",
        reviewed_on="2026-10-19",
        reviewer="Anatomical Science Working Group",
    ),
    EvidenceRecord(
        evidence_id="EVID-A-003",
        title="Z-Anatomy: Open 3D Anatomy of the Human Body",
        url="https://github.com/Z-Anatomy/Models-of-human-anatomy",
        organization="Z-Anatomy Project",
        year=2025,
        license="CC BY-SA 4.0 (individual meshes vary; non-commercial restrictions present in subset)",
        tier=EvidenceTier.TIER_2_PEER_REVIEWED_ANATOMY.value,
        claim_scope="Reference 3D mesh topologies for musculoskeletal education. Must verify sub-mesh licenses prior to redistribution.",
        reviewed_on="2026-10-19",
        reviewer="Anatomical Science Working Group",
    ),
    EvidenceRecord(
        evidence_id="EVID-D-001",
        title="Direct Current / DDS Device Regulatory Baseline and Specification Requirement",
        url="https://msk-therapy-os.local/evidence/dds-specification-rule",
        organization="MSK-Therapy-OS Technical Safety Board",
        year=2026,
        license="Open Medical Systems Specification",
        tier=EvidenceTier.TIER_3_MANUFACTURER_MANUAL.value,
        claim_scope="DDS product label is ambiguous. Device workflows locked until exact manufacturer manual, waveform, voltage/current limits, and clearance are verified.",
        reviewed_on="2026-10-19",
        reviewer="Biomedical Engineering Reviewer",
    ),
    EvidenceRecord(
        evidence_id="EVID-T-001",
        title="Traditional Thai Medicine: Sen Sib Line Trajectories & Acupressure Points",
        url="https://dtam.moph.go.th/index.php/en/",
        organization="Department of Thai Traditional and Alternative Medicine (DTAM), Ministry of Public Health, Thailand",
        year=2016,
        license="Government Educational Reference",
        tier=EvidenceTier.TIER_4_TRADITIONAL_SCHEMA.value,
        claim_scope="Traditional somatic line system (Sen Sib). Separate cultural curriculum construct; not physically equivalent to somatic nerves or vascular structures.",
        reviewed_on="2026-10-19",
        reviewer="Integrative Medicine Reviewer",
    ),
    EvidenceRecord(
        evidence_id="EVID-T-002",
        title="Dien Chan: Facial Reflexology Diagnostic and Therapeutic Schemes",
        url="https://www.dienchan.com/en/",
        organization="International Multireflexology Dien Chan Academy",
        year=2018,
        license="Educational Curriculum Material",
        tier=EvidenceTier.TIER_4_TRADITIONAL_SCHEMA.value,
        claim_scope="Facial reflex point schema (Bui Quoc Chau system). Separate traditional/cultural construct; not physically equivalent to cranial nerve distributions or pathology.",
        reviewed_on="2026-10-19",
        reviewer="Integrative Medicine Reviewer",
    ),
    EvidenceRecord(
        evidence_id="EVID-T-003",
        title="WHO Standard Acupuncture Point Locations & Nomenclature (WHO 2008 / GB/T 12346-2021)",
        url="https://iris.who.int/handle/10665/207797",
        organization="World Health Organization (WHO) / Standardization Administration of China",
        year=2021,
        license="WHO Open Access / National Standard",
        tier=EvidenceTier.TIER_4_TRADITIONAL_SCHEMA.value,
        claim_scope="Standardized surface topography and nomenclature for 361 classical acupuncture points. Traditional meridian construct; not physically equivalent to anatomical nerves, blood vessels, or fascia.",
        reviewed_on="2026-10-20",
        reviewer="Acupuncture & Integrative Medicine Governance Panel",
    ),
]


def list_evidence(db: sqlite3.Connection, tier: Optional[int] = None) -> List[EvidenceRecord]:
    """Retrieve evidence entries, optionally filtered by tier."""
    query = (
        "SELECT evidence_id, title, url, organization, year, license, tier, claim_scope, reviewed_on, reviewer "
        "FROM evidence_catalog"
    )
    params: list = []
    if tier is not None:
        query += " WHERE tier = ?"
        params.append(tier)
    query += " ORDER BY tier, evidence_id"

    rows = db.execute(query, params).fetchall()
    return [
        EvidenceRecord(
            evidence_id=r[0],
            title=r[1],
            url=r[2],
            organization=r[3],
            year=r[4],
            license=r[5],
            tier=r[6],
            claim_scope=r[7],
            reviewed_on=r[8],
            reviewer=r[9],
        )
        for r in rows
    ]


def get_evidence_by_id(db: sqlite3.Connection, evidence_id: str) -> Optional[EvidenceRecord]:
    """Lookup a single evidence record by ID."""
    row = db.execute(
        "SELECT evidence_id, title, url, organization, year, license, tier, claim_scope, reviewed_on, reviewer "
        "FROM evidence_catalog WHERE evidence_id = ?",
        (evidence_id,),
    ).fetchone()
    if not row:
        return None
    return EvidenceRecord(
        evidence_id=row[0],
        title=row[1],
        url=row[2],
        organization=row[3],
        year=row[4],
        license=row[5],
        tier=row[6],
        claim_scope=row[7],
        reviewed_on=row[8],
        reviewer=row[9],
    )
