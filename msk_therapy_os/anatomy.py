"""Anatomy Adapter linking anatomical structures, BodyParts3D IDs, and traditional namespaces."""
from __future__ import annotations

import sqlite3
from typing import List, Optional
from msk_therapy_os.models import AnatomyRecord, KnowledgeNamespace

DEFAULT_ATLAS_BASE = "https://CognitionLabSNUC.github.io/open-anatomy-atlas/"

DEFAULT_ANATOMY_CATALOG: List[AnatomyRecord] = [
    # Modern Evidence-Based Anatomy
    AnatomyRecord(
        structure_id="STR-CERV-001",
        name="Cervical Spine (C1-C7 vertebrae)",
        region="neck",
        source_dataset="BodyParts3D 4.0 / FMA 9914",
        bodyparts3d_id="FJ9914",
        atlas_url=f"{DEFAULT_ATLAS_BASE}?part=FJ9914",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-CERV-002",
        name="Trapezius Muscle (Descending/Transverse/Ascending parts)",
        region="neck",
        source_dataset="BodyParts3D 4.0 / FMA 9626",
        bodyparts3d_id="FJ9626",
        atlas_url=f"{DEFAULT_ATLAS_BASE}?part=FJ9626",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-CERV-003",
        name="Levator Scapulae Muscle",
        region="neck",
        source_dataset="BodyParts3D 4.0 / FMA 32519",
        bodyparts3d_id="FJ32519",
        atlas_url=f"{DEFAULT_ATLAS_BASE}?part=FJ32519",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-LUMB-001",
        name="Lumbar Vertebrae (L1-L5)",
        region="low_back",
        source_dataset="BodyParts3D 4.0 / FMA 9922",
        bodyparts3d_id="FJ9922",
        atlas_url=f"{DEFAULT_ATLAS_BASE}?part=FJ9922",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-LUMB-002",
        name="Erector Spinae Muscle Group",
        region="low_back",
        source_dataset="BodyParts3D 4.0 / FMA 71302",
        bodyparts3d_id="FJ71302",
        atlas_url=f"{DEFAULT_ATLAS_BASE}?part=FJ71302",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-LUMB-003",
        name="Piriformis Muscle & Sciatic Pathway Reference",
        region="low_back",
        source_dataset="BodyParts3D 4.0 / FMA 22357",
        bodyparts3d_id="FJ22357",
        atlas_url=f"{DEFAULT_ATLAS_BASE}?part=FJ22357",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    # Traditional Thai Line Schema (Separate namespace)
    AnatomyRecord(
        structure_id="TRAD-THAI-001",
        name="Sen Ittha (Left paramedian trajectory)",
        region="low_back",
        source_dataset="Department of Thai Traditional and Alternative Medicine (DTAM)",
        bodyparts3d_id=None,
        atlas_url=DEFAULT_ATLAS_BASE,
        namespace=KnowledgeNamespace.TRADITIONAL_MERIDIAN.value,
        evidence_id="EVID-T-001",
    ),
    AnatomyRecord(
        structure_id="TRAD-THAI-002",
        name="Sen Pingkhla (Right paramedian trajectory)",
        region="low_back",
        source_dataset="Department of Thai Traditional and Alternative Medicine (DTAM)",
        bodyparts3d_id=None,
        atlas_url=DEFAULT_ATLAS_BASE,
        namespace=KnowledgeNamespace.TRADITIONAL_MERIDIAN.value,
        evidence_id="EVID-T-001",
    ),
    # Dien Chan Facial Reflexology Schema (Separate namespace)
    AnatomyRecord(
        structure_id="TRAD-DIEN-001",
        name="Point 26 (Glabella reflex projection for neck/upper spine)",
        region="face",
        source_dataset="International Multireflexology Dien Chan Academy",
        bodyparts3d_id=None,
        atlas_url=DEFAULT_ATLAS_BASE,
        namespace=KnowledgeNamespace.DIEN_CHAN_REFLEX.value,
        evidence_id="EVID-T-002",
    ),
    AnatomyRecord(
        structure_id="TRAD-DIEN-002",
        name="Point 19 (Subnasal reflex projection for autonomic/spine)",
        region="face",
        source_dataset="International Multireflexology Dien Chan Academy",
        bodyparts3d_id=None,
        atlas_url=DEFAULT_ATLAS_BASE,
        namespace=KnowledgeNamespace.DIEN_CHAN_REFLEX.value,
        evidence_id="EVID-T-002",
    ),
]


def list_anatomy(
    db: sqlite3.Connection,
    region: Optional[str] = None,
    namespace: Optional[str] = None,
) -> List[AnatomyRecord]:
    """List anatomy structures, with optional region and namespace filtering."""
    query = (
        "SELECT structure_id, name, region, source_dataset, bodyparts3d_id, atlas_url, namespace, evidence_id "
        "FROM anatomy_structures"
    )
    conditions = []
    params: list = []
    if region:
        conditions.append("region = ?")
        params.append(region.strip().lower())
    if namespace:
        conditions.append("namespace = ?")
        params.append(namespace.strip())
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY namespace, region, structure_id"

    rows = db.execute(query, params).fetchall()
    return [
        AnatomyRecord(
            structure_id=r[0],
            name=r[1],
            region=r[2],
            source_dataset=r[3],
            bodyparts3d_id=r[4],
            atlas_url=r[5],
            namespace=r[6],
            evidence_id=r[7],
        )
        for r in rows
    ]


def get_anatomy_by_id(db: sqlite3.Connection, structure_id: str) -> Optional[AnatomyRecord]:
    """Retrieve an anatomy record by ID."""
    row = db.execute(
        "SELECT structure_id, name, region, source_dataset, bodyparts3d_id, atlas_url, namespace, evidence_id "
        "FROM anatomy_structures WHERE structure_id = ?",
        (structure_id,),
    ).fetchone()
    if not row:
        return None
    return AnatomyRecord(
        structure_id=row[0],
        name=row[1],
        region=row[2],
        source_dataset=row[3],
        bodyparts3d_id=row[4],
        atlas_url=row[5],
        namespace=row[6],
        evidence_id=row[7],
    )
