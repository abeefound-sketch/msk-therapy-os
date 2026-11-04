"""Anatomy Asset Registry & Canonical Frame Transform Registry for Milestone P35.
Manages genuine anatomical bone and tissue meshes from BodyParts3D (CC BY 4.0 DBCLS Japan)
and Z-Anatomy (CC BY-SA 4.0), enforces stable IDs, SHA-256 hashes, parent segments,
and provides invertible coordinate frame transformations.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]


class AssetIntegrityError(Exception):
    """Raised when an asset hash or format fails integrity checks."""
    pass


class SegmentMismatchError(Exception):
    """Raised when a mesh is assigned to an anatomically incorrect segment."""
    pass


class LateralityConflictError(Exception):
    """Raised when mesh laterality conflicts with armature bone laterality."""
    pass


class UnitScaleDivergenceError(Exception):
    """Raised when coordinate scale diverges from standard meters."""
    pass


@dataclass
class AnatomicalAssetRecord:
    asset_id: str
    bone_name: str
    canonical_name: str
    fma_id: str
    parent_segment: str
    laterality: str  # "RIGHT", "LEFT", "MIDLINE"
    expected_sha256: str
    vertex_count: int
    triangle_count: int
    license: str
    source_chunk: str
    bounds: List[List[float]]
    units: str = "METERS"
    deformation_model: str = "RIGID_SKELETAL"


class CanonicalFrameTransformRegistry:
    """Manages invertible transformations between BodyParts3D reference frame,
    Blender coordinates, and clinical anatomical orientation.
    BodyParts3D frame: +X = Right, +Y = Superior (Up), +Z = Anterior (Front) in meters.
    Blender frame: +X = Right, +Y = Anterior (Front), +Z = Superior (Up) in meters.
    """

    @staticmethod
    def bodyparts3d_to_blender(coords: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Convert BodyParts3D (X_bp, Y_bp, Z_bp) to Blender (X_bl, Y_bl, Z_bl).
        X_bl = X_bp
        Y_bl = Z_bp
        Z_bl = Y_bp
        """
        x, y, z = coords
        # Scale check: human limb bones must be within [-2.0, 2.0] meters
        if any(abs(v) > 5.0 for v in [x, y, z]):
            raise UnitScaleDivergenceError(f"Scale divergence detected: coords {coords} exceed physiological meter limits (suspected mm).")
        return (float(x), float(z), float(y))

    @staticmethod
    def blender_to_bodyparts3d(coords: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Convert Blender (X_bl, Y_bl, Z_bl) back to BodyParts3D (X_bp, Y_bp, Z_bp).
        X_bp = X_bl
        Y_bp = Z_bl
        Z_bp = Y_bl
        """
        x, y, z = coords
        if any(abs(v) > 5.0 for v in [x, y, z]):
            raise UnitScaleDivergenceError(f"Scale divergence detected: coords {coords} exceed physiological meter limits (suspected mm).")
        return (float(x), float(z), float(y))


class AnatomyAssetRegistry:
    """Authoritative registry for anatomical mesh assets with cryptographic verification."""

    # Authoritative records extracted from BodyParts3D 4.0
    AUTHORITATIVE_ASSETS: Dict[str, AnatomicalAssetRecord] = {
        "FJ3368": AnatomicalAssetRecord(
            asset_id="FJ3368",
            bone_name="Humerus_R",
            canonical_name="Right humerus",
            fma_id="FMA:23130",
            parent_segment="upper_arm.R",
            laterality="RIGHT",
            expected_sha256="d583ad2e7ee11cf1523f2f819fbc7da3ce7fe505d96ca418bf7dd8178e72750d",
            vertex_count=794,
            triangle_count=1070,
            license="CC BY 4.0 DBCLS Japan",
            source_chunk="body-13.bin",
            bounds=[[-0.2408, 1.1073, -0.0490], [-0.1401, 1.4147, 0.0002]]
        ),
        "FJ3349": AnatomicalAssetRecord(
            asset_id="FJ3349",
            bone_name="Radius_R",
            canonical_name="Right radius",
            fma_id="FMA:23464",
            parent_segment="forearm.R",
            laterality="RIGHT",
            expected_sha256="347290571f6dbe692b6045ee33e7ee5a837e289bf53b9fba71ca706798032ba8",
            vertex_count=249,
            triangle_count=408,
            license="CC BY 4.0 DBCLS Japan",
            source_chunk="body-13.bin",
            bounds=[[-0.2795, 0.8839, -0.0389], [-0.2198, 1.1132, 0.0269]]
        ),
        "FJ3391": AnatomicalAssetRecord(
            asset_id="FJ3391",
            bone_name="Ulna_R",
            canonical_name="Right ulna",
            fma_id="FMA:23467",
            parent_segment="forearm.R",
            laterality="RIGHT",
            expected_sha256="6af632e4dd2f6797f6c310c83a5441cb48bb446210b37651c6ebf26372b64d04",
            vertex_count=305,
            triangle_count=482,
            license="CC BY 4.0 DBCLS Japan",
            source_chunk="body-13.bin",
            bounds=[[-0.2472, 0.8833, -0.0552], [-0.1969, 1.1306, 0.0235]]
        ),
        "FJ3352": AnatomicalAssetRecord(
            asset_id="FJ3352",
            bone_name="Metacarpal_2_R",
            canonical_name="Right second metacarpal bone",
            fma_id="FMA:24466",
            parent_segment="hand.R",
            laterality="RIGHT",
            expected_sha256="23c39f4eb1ff3ffc0ff314ae1938507851390499ba5d3989cf8bdfa3754e60fa",
            vertex_count=347,
            triangle_count=610,
            license="CC BY 4.0 DBCLS Japan",
            source_chunk="body-13.bin",
            bounds=[[-0.2927, 0.7970, 0.0171], [-0.2618, 0.8650, 0.0428]]
        ),
        "FJ3384": AnatomicalAssetRecord(
            asset_id="FJ3384",
            bone_name="Scapula_R",
            canonical_name="Right scapula",
            fma_id="FMA:13395",
            parent_segment="clavicle.R",
            laterality="RIGHT",
            expected_sha256="0ee8ecd6595fb0b0467554f65c197e41be868d407ae48eb2cf829f0e1f37e19f",
            vertex_count=2896,
            triangle_count=5756,
            license="CC BY 4.0 DBCLS Japan",
            source_chunk="body-13.bin",
            bounds=[[-0.1665, 1.2621, -0.1051], [-0.0571, 1.4280, 0.0029]]
        ),
        "FJ3362": AnatomicalAssetRecord(
            asset_id="FJ3362",
            bone_name="Clavicle_R",
            canonical_name="Right clavicle",
            fma_id="FMA:13322",
            parent_segment="clavicle.R",
            laterality="RIGHT",
            expected_sha256="0eff6dc9d4c1a5db488bbd0bf85b03f0b2f790209dfa53e410f97970d4f26038",
            vertex_count=420,
            triangle_count=820,
            license="CC BY 4.0 DBCLS Japan",
            source_chunk="body-13.bin",
            bounds=[[-0.1453, 1.3867, -0.0456], [-0.0097, 1.4336, 0.0469]]
        ),
        "FJ3387": AnatomicalAssetRecord(
            asset_id="FJ3387",
            bone_name="Tibia_R",
            canonical_name="Right tibia",
            fma_id="FMA:24477",
            parent_segment="shank.R",
            laterality="RIGHT",
            expected_sha256="2fe1e44d01ad47a4ba7ff0a653bb1e5c464b55e37ca98bb55f41aa8ce04a0808",
            vertex_count=334,
            triangle_count=634,
            license="CC BY 4.0 DBCLS Japan",
            source_chunk="body-13.bin",
            bounds=[[-0.1094, 0.0721, -0.0479], [-0.0352, 0.4520, 0.0148]]
        ),
        "FJ3360": AnatomicalAssetRecord(
            asset_id="FJ3360",
            bone_name="Calcaneus_R",
            canonical_name="Right calcaneus",
            fma_id="FMA:24497",
            parent_segment="foot.R",
            laterality="RIGHT",
            expected_sha256="5db839d328652d8b1aa6a56e5dfc929a7566b6c507c5aa3f37b7ca2c5025a153",
            vertex_count=641,
            triangle_count=1076,
            license="CC BY 4.0 DBCLS Japan",
            source_chunk="body-13.bin",
            bounds=[[-0.1008, 0.0096, -0.0760], [-0.0449, 0.0590, -0.0059]]
        ),
    }

    @classmethod
    def get_asset(cls, asset_id: str) -> Optional[AnatomicalAssetRecord]:
        return cls.AUTHORITATIVE_ASSETS.get(asset_id)

    @classmethod
    def validate_mesh_data(cls, asset_id: str, raw_bytes: bytes) -> bool:
        """Validate raw binary mesh against expected SHA-256 hash."""
        record = cls.get_asset(asset_id)
        if not record:
            raise KeyError(f"Asset ID '{asset_id}' not found in AnatomicalAssetRegistry.")
        actual_hash = hashlib.sha256(raw_bytes).hexdigest()
        if actual_hash != record.expected_sha256:
            raise AssetIntegrityError(
                f"STALE MESH HASH: Asset '{asset_id}' expected {record.expected_sha256}, got {actual_hash}"
            )
        return True

    @classmethod
    def validate_bone_binding(cls, asset_id: str, target_bone_name: str, target_laterality: str = "RIGHT") -> Dict[str, Any]:
        """Strict validation of anatomical parent bone binding."""
        record = cls.get_asset(asset_id)
        if not record:
            raise KeyError(f"Unknown asset '{asset_id}'.")

        # 1. Segment match check
        if target_bone_name != record.parent_segment:
            raise SegmentMismatchError(
                f"ANATOMICAL SEGMENT MISMATCH: Mesh '{record.bone_name}' ({record.canonical_name}) "
                f"must bind to segment '{record.parent_segment}', not '{target_bone_name}'."
            )

        # 2. Laterality check
        if target_laterality.upper() != record.laterality:
            raise LateralityConflictError(
                f"LATERALITY INVERSION CONFLICT: Mesh '{record.bone_name}' is {record.laterality}, "
                f"cannot bind to {target_laterality} armature bone."
            )

        return {
            "status": "VALID_ANATOMICAL_BINDING",
            "asset_id": asset_id,
            "bone_name": record.bone_name,
            "parent_segment": record.parent_segment,
            "deformation_model": record.deformation_model,
        }
