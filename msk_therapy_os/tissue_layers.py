"""M5 Reference Anatomy Layering, Discrete Tissue Opacity, and Slicing.

Provides discrete tissue layer visibility management (skin, fascia, superficial/deep muscle,
bone, neurovascular) and planar slicing controls on verified BodyParts3D meshes.
Strictly disclaims patient-specific tissue depth or safe instrument penetration.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Verified Standard Tissue Layer Catalog
TISSUE_LAYERS = {
    "skin": {
        "display_name": "Skin / Integumentary Surface",
        "system": "integumentary",
        "default_opacity": 0.5,
        "fma_ids": ["FMA7163"],
        "bodyparts3d_keys": ["FJ2810"],
        "description": "Outer boundary surface mesh",
    },
    "superficial_fascia": {
        "display_name": "Superficial Fascia & Subcutaneous Layer",
        "system": "fascial",
        "default_opacity": 0.3,
        "fma_ids": ["FMA78440"],
        "bodyparts3d_keys": [],
        "description": "Loose connective tissue separating skin from deep fascia",
    },
    "deep_fascia": {
        "display_name": "Deep Investing Fascia",
        "system": "fascial",
        "default_opacity": 0.4,
        "fma_ids": ["FMA78441"],
        "bodyparts3d_keys": [],
        "description": "Fibrous membrane investing cervical and thoracolumbar muscular compartments",
    },
    "muscle_superficial": {
        "display_name": "Superficial Skeletal Muscles",
        "system": "muscular",
        "default_opacity": 1.0,
        "fma_ids": ["FMA32529", "FMA13407", "FMA13083", "FMA9622"],
        "bodyparts3d_keys": ["FJ32529", "FJ13407", "FJ13083", "FJ9622"],
        "description": "Prime mover surface muscles: Trapezius, Sternocleidomastoid, Deltoid, Latissimus dorsi",
    },
    "muscle_deep": {
        "display_name": "Deep Skeletal Muscles & Stabilizers",
        "system": "muscular",
        "default_opacity": 1.0,
        "fma_ids": ["FMA32519", "FMA32557", "FMA13379", "FMA9625"],
        "bodyparts3d_keys": ["FJ32519", "FJ32557", "FJ13379", "FJ9625"],
        "description": "Deep stabilizers: Levator scapulae, Splenius, Rhomboids, Rotator cuff",
    },
    "skeletal_bone": {
        "display_name": "Skeletal System (Vertebrae & Girdle)",
        "system": "skeletal",
        "default_opacity": 1.0,
        "fma_ids": ["FMA9914", "FMA13373", "FMA13374"],
        "bodyparts3d_keys": ["FJ9914", "FJ13373", "FJ13374"],
        "description": "Cervical/thoracic vertebrae, scapulae, and clavicles",
    },
    "neurovascular": {
        "display_name": "Peripheral Nerves & Major Blood Vessels",
        "system": "neurovascular",
        "default_opacity": 0.8,
        "fma_ids": ["FMA5906", "FMA50344"],
        "bodyparts3d_keys": ["FJ5906", "FJ50344"],
        "description": "Brachial plexus roots, accessory nerve, vertebral and carotid vessels",
    },
}

LAYER_DISCLAIMER = (
    "REFERENCE TISSUE LAYERS ONLY. Visualized layers derive from the BodyParts3D 4.0 "
    "standard adult reference male model. They DO NOT measure or represent individual patient "
    "adipose thickness, fascia depth, or safe instrument penetration/puncture limits."
)


def init_tissue_layer_tables(db: sqlite3.Connection) -> None:
    """Initialize SQLite tables for M5 Tissue Layer configurations."""
    db.executescript("""
    CREATE TABLE IF NOT EXISTS tissue_layer_configs (
        config_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        layer_name TEXT NOT NULL CHECK(layer_name IN ('skin', 'superficial_fascia', 'deep_fascia', 'muscle_superficial', 'muscle_deep', 'skeletal_bone', 'neurovascular')),
        opacity REAL NOT NULL CHECK(opacity BETWEEN 0.0 AND 1.0),
        is_visible INTEGER NOT NULL CHECK(is_visible IN (0, 1)),
        slice_plane TEXT CHECK(slice_plane IN ('axial', 'sagittal', 'coronal', 'none')),
        slice_offset REAL CHECK(slice_offset BETWEEN -1.0 AND 1.0),
        disclaimer TEXT NOT NULL DEFAULT 'REFERENCE_TISSUE_LAYERS_ONLY; Not validated for needle depth',
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, layer_name)
    );
    """)


def get_layer_catalog() -> Dict[str, Any]:
    """Return catalog of supported tissue layers and legal disclaimer."""
    return {
        "layers": TISSUE_LAYERS,
        "disclaimer": LAYER_DISCLAIMER,
        "slice_planes": ["axial", "sagittal", "coronal"],
    }


def get_user_layer_config(db: sqlite3.Connection, user_id: str) -> List[Dict[str, Any]]:
    """Retrieve layer visibility configurations for a user or defaults."""
    rows = db.execute(
        """SELECT layer_name, opacity, is_visible, slice_plane, slice_offset, updated_at
           FROM tissue_layer_configs WHERE user_id = ?""",
        (user_id,),
    ).fetchall()

    if not rows:
        # Generate default state
        defaults = []
        for name, meta in TISSUE_LAYERS.items():
            defaults.append({
                "layer_name": name,
                "display_name": meta["display_name"],
                "opacity": meta["default_opacity"],
                "is_visible": 1 if meta["default_opacity"] > 0 else 0,
                "slice_plane": "none",
                "slice_offset": 0.0,
            })
        return defaults

    result = []
    for r in rows:
        name = r[0]
        result.append({
            "layer_name": name,
            "display_name": TISSUE_LAYERS.get(name, {}).get("display_name", name),
            "opacity": r[1],
            "is_visible": r[2],
            "slice_plane": r[3] or "none",
            "slice_offset": r[4] or 0.0,
            "updated_at": r[5],
        })
    return result


def update_layer_config(
    db: sqlite3.Connection,
    *,
    user_id: str,
    layer_name: str,
    opacity: float,
    is_visible: bool,
    slice_plane: Optional[str] = "none",
    slice_offset: Optional[float] = 0.0,
) -> Dict[str, Any]:
    """Update visibility and opacity of an anatomical tissue layer."""
    if layer_name not in TISSUE_LAYERS:
        raise ValueError(f"Unknown tissue layer '{layer_name}'")
    if not (0.0 <= opacity <= 1.0):
        raise ValueError("Opacity must be between 0.0 and 1.0")
    if slice_plane not in ('axial', 'sagittal', 'coronal', 'none'):
        raise ValueError("Invalid slice_plane")
    if slice_offset is not None and not (-1.0 <= slice_offset <= 1.0):
        raise ValueError("slice_offset must be between -1.0 and 1.0")

    config_id = f"LCFG-{uuid4().hex[:16]}"
    vis_val = 1 if is_visible else 0

    with db:
        db.execute(
            """INSERT INTO tissue_layer_configs
               (config_id, user_id, layer_name, opacity, is_visible, slice_plane, slice_offset)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, layer_name) DO UPDATE SET
               opacity = excluded.opacity,
               is_visible = excluded.is_visible,
               slice_plane = excluded.slice_plane,
               slice_offset = excluded.slice_offset,
               updated_at = CURRENT_TIMESTAMP""",
            (config_id, user_id, layer_name, opacity, vis_val, slice_plane, slice_offset),
        )

    return {
        "user_id": user_id,
        "layer_name": layer_name,
        "opacity": opacity,
        "is_visible": is_visible,
        "slice_plane": slice_plane,
        "slice_offset": slice_offset,
        "disclaimer": LAYER_DISCLAIMER,
    }
