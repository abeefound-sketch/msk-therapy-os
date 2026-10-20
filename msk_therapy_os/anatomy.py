"""Anatomy Adapter linking anatomical structures, BodyParts3D IDs, and traditional namespaces."""
from __future__ import annotations

import sqlite3
from typing import List, Optional
from msk_therapy_os.models import AnatomyRecord, KnowledgeNamespace

DEFAULT_ATLAS_BASE = "https://CognitionLabSNUC.github.io/open-anatomy-atlas/"

# Local atlas path served by the MSK-Therapy-OS server at /atlas/
LOCAL_ATLAS_PATH = "/atlas/"

DEFAULT_ANATOMY_CATALOG: List[AnatomyRecord] = [
    # -----------------------------------------------------------------------
    # Modern Evidence-Based Anatomy — Neck & Cervical Region
    # FMA IDs verified against BodyParts3D 4.0 index.json (2,234 meshes,
    # 3,434 named structures, downloaded 2026-10-20 from dbarchive.biosciencedbc.jp).
    # -----------------------------------------------------------------------
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
        name="Zone of Trapezius (Descending/Transverse/Ascending)",
        region="neck",
        source_dataset="BodyParts3D 4.0 / FMA32529",
        bodyparts3d_id="FMA32529",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-CERV-003",
        name="Levator Scapulae",
        region="neck",
        source_dataset="BodyParts3D 4.0 / FMA32519",
        bodyparts3d_id="FMA32519",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-CERV-004",
        name="Descending Part of Trapezius (Upper Trapezius)",
        region="neck",
        source_dataset="BodyParts3D 4.0 / FMA32557",
        bodyparts3d_id="FMA32557",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-CERV-005",
        name="Transverse Part of Trapezius (Middle Trapezius)",
        region="neck",
        source_dataset="BodyParts3D 4.0 / FMA32556",
        bodyparts3d_id="FMA32556",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-CERV-006",
        name="Ascending Part of Trapezius (Lower Trapezius)",
        region="neck",
        source_dataset="BodyParts3D 4.0 / FMA32555",
        bodyparts3d_id="FMA32555",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    # -----------------------------------------------------------------------
    # Shoulder Region
    # -----------------------------------------------------------------------
    AnatomyRecord(
        structure_id="STR-SHLD-001",
        name="Clavicle",
        region="shoulder",
        source_dataset="BodyParts3D 4.0 / FMA13321",
        bodyparts3d_id="FMA13321",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-SHLD-002",
        name="Deep Extrinsic Muscle of Shoulder",
        region="shoulder",
        source_dataset="BodyParts3D 4.0 / FMA32518",
        bodyparts3d_id="FMA32518",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-SHLD-003",
        name="Extrinsic Muscle of Shoulder",
        region="shoulder",
        source_dataset="BodyParts3D 4.0 / FMA32516",
        bodyparts3d_id="FMA32516",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    # -----------------------------------------------------------------------
    # Lumbar / Low-Back Region
    # -----------------------------------------------------------------------
    AnatomyRecord(
        structure_id="STR-LUMB-001",
        name="Lumbar Vertebral Column",
        region="low_back",
        source_dataset="BodyParts3D 4.0 / FMA16203",
        bodyparts3d_id="FMA16203",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-LUMB-002",
        name="Lumbar Vertebra (L1-L5)",
        region="low_back",
        source_dataset="BodyParts3D 4.0 / FMA9921",
        bodyparts3d_id="FMA9921",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    AnatomyRecord(
        structure_id="STR-LUMB-003",
        name="Piriformis",
        region="low_back",
        source_dataset="BodyParts3D 4.0 / FMA19082",
        bodyparts3d_id="FMA19082",
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value,
        evidence_id="EVID-A-002",
    ),
    # -----------------------------------------------------------------------
    # Verified Traditional Meridian & Acupoints (WHO 2008 & GB/T 12346-2021)
    # -----------------------------------------------------------------------
    AnatomyRecord(
        structure_id="ACU-GB21",
        name="Jianjing (GB21 / 肩井 - Trapezius Trigger Point Zone)",
        region="neck",
        source_dataset="WHO 2008 / GB/T 12346-2021 / chino-meds",
        bodyparts3d_id=None,
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.TRADITIONAL_MERIDIAN.value,
        evidence_id="EVID-T-003",
    ),
    AnatomyRecord(
        structure_id="ACU-GB20",
        name="Fengchi (GB20 / 风池 - Suboccipital Region)",
        region="neck",
        source_dataset="WHO 2008 / GB/T 12346-2021 / chino-meds",
        bodyparts3d_id=None,
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.TRADITIONAL_MERIDIAN.value,
        evidence_id="EVID-T-003",
    ),
    AnatomyRecord(
        structure_id="ACU-GV14",
        name="Dazhui (GV14 / 大椎 - C7-T1 Spinous Process Junction)",
        region="neck",
        source_dataset="WHO 2008 / GB/T 12346-2021 / chino-meds",
        bodyparts3d_id=None,
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.TRADITIONAL_MERIDIAN.value,
        evidence_id="EVID-T-003",
    ),
    AnatomyRecord(
        structure_id="ACU-BL10",
        name="Tianzhu (BL10 / 天柱 - Paraspinal Cervical Border)",
        region="neck",
        source_dataset="WHO 2008 / GB/T 12346-2021 / chino-meds",
        bodyparts3d_id=None,
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.TRADITIONAL_MERIDIAN.value,
        evidence_id="EVID-T-003",
    ),
    AnatomyRecord(
        structure_id="ACU-LI4",
        name="Hegu (LI4 / 合谷 - First Dorsal Interosseous)",
        region="shoulder",
        source_dataset="WHO 2008 / GB/T 12346-2021 / chino-meds",
        bodyparts3d_id=None,
        atlas_url=f"{DEFAULT_ATLAS_BASE}",
        namespace=KnowledgeNamespace.TRADITIONAL_MERIDIAN.value,
        evidence_id="EVID-T-003",
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
    AnatomyRecord(
        structure_id="TRAD-THAI-003",
        name="Sen Sumana (Central midline spinal trajectory)",
        region="neck",
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
    AnatomyRecord(
        structure_id="TRAD-DIEN-003",
        name="Point 34 (Above medial brow / shoulder reflex)",
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
