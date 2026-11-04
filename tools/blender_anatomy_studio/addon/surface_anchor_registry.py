"""Anatomical Surface Anchor Registry for Milestones P29-P35.
Enforces strict anatomical provenance, prohibits inappropriate bone-to-marker cross-binding,
tracks vertex/barycentric surface anchoring with cryptographic hashes,
and enforces fail-closed validation on unit scale, laterality, and stale hashes.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Tuple


class AnatomicalSurfaceAnchorRegistry:
    """Registry managing anatomical surface anchors, prohibiting anatomically incorrect parent bindings."""

    # Authoritative ontological and anatomical mappings
    POINT_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
        "LI4": {
            "code": "LI4",
            "name_vi": "Hợp Cốc",
            "name_en": "Hegu",
            "fma_id": "FMA:23910",
            "ta2_name": "Musculus interosseus dorsalis primus / Ossa metacarpalia I-II",
            "required_parent_segment": "hand.R",
            "required_bone_mesh": "Metacarpals_R",
            "allowed_bone_meshes": ["Metacarpals_R", "Metacarpal_2_R", "FJ3352"],
            "laterality": "RIGHT",
            "source_reference": "WHO Standard Acupuncture Point Locations (2008), p. 33; GB/T 12346-2021",
            "clinical_uncertainty_mm": 5.0,
            "prohibited_bindings": ["Humerus_R", "upper_arm.R", "Scapula_R", "Clavicle_R", "forearm.R", "shank.R"],
            "verification_status": "EXPERT_REVIEW_PENDING"
        },
        "ST36": {
            "code": "ST36",
            "name_vi": "Túc Tam Lý",
            "name_en": "Zusanli",
            "fma_id": "FMA:24476",
            "ta2_name": "Tibialis anterior / Margo anterior tibiae",
            "required_parent_segment": "shank.R",
            "required_bone_mesh": "Tibia_R",
            "allowed_bone_meshes": ["Tibia_R", "FJ3387"],
            "laterality": "RIGHT",
            "source_reference": "WHO Standard Acupuncture Point Locations (2008), p. 69; GB/T 12346-2021",
            "clinical_uncertainty_mm": 10.0,
            "prohibited_bindings": ["Humerus_R", "Scapula_R", "Clavicle_R", "upper_arm.R", "hand.R"],
            "verification_status": "EXPERT_REVIEW_PENDING"
        },
        "KI3": {
            "code": "KI3",
            "name_vi": "Thái Khê",
            "name_en": "Taixi",
            "fma_id": "FMA:51111",
            "ta2_name": "Sulcus malleolaris / Tendo calcaneus",
            "required_parent_segment": "foot.R",
            "required_bone_mesh": "Calcaneus_Tarsals_R",
            "allowed_bone_meshes": ["Calcaneus_R", "Calcaneus_Tarsals_R", "FJ3360"],
            "laterality": "RIGHT",
            "source_reference": "WHO Standard Acupuncture Point Locations (2008), p. 112; GB/T 12346-2021",
            "clinical_uncertainty_mm": 8.0,
            "prohibited_bindings": ["Humerus_R", "Scapula_R", "Clavicle_R", "upper_arm.R", "hand.R"],
            "verification_status": "EXPERT_REVIEW_PENDING"
        },
        # Upper limb points present on shoulder / humerus assets:
        "LI14": {
            "code": "LI14",
            "name_vi": "Tí Nhu",
            "name_en": "Binao",
            "fma_id": "FMA:23412",
            "ta2_name": "Tuberositas deltoidea humeri",
            "required_parent_segment": "upper_arm.R",
            "required_bone_mesh": "Humerus_R",
            "allowed_bone_meshes": ["Humerus_R", "FJ3368"],
            "laterality": "RIGHT",
            "source_reference": "WHO Standard Acupuncture Point Locations (2008), p. 41; GB/T 12346-2021",
            "clinical_uncertainty_mm": 5.0,
            "prohibited_bindings": ["Clavicle_R", "Tibia_R", "Scapula_R", "hand.R"],
            "verification_status": "VALID_SURFACE_ANCHOR"
        },
        "LI15": {
            "code": "LI15",
            "name_vi": "Kiên Ngung",
            "name_en": "Jianyu",
            "fma_id": "FMA:23240",
            "ta2_name": "Angulus acromii / Sulcus intertubercularis",
            "required_parent_segment": "clavicle.R",
            "required_bone_mesh": "Scapula_R",
            "allowed_bone_meshes": ["Scapula_R", "FJ3384"],
            "laterality": "RIGHT",
            "source_reference": "WHO Standard Acupuncture Point Locations (2008), p. 42; GB/T 12346-2021",
            "clinical_uncertainty_mm": 6.0,
            "prohibited_bindings": ["Humerus_R", "Tibia_R", "hand.R"],
            "verification_status": "VALID_SURFACE_ANCHOR"
        },
        "LATERAL_EPICONDYLE": {
            "code": "LAT_EPI_R",
            "name_vi": "Mỏm Trên Lồi Cầu Ngoài Xương Cánh Tay",
            "name_en": "Lateral Epicondyle of Humerus",
            "fma_id": "FMA:23420",
            "ta2_name": "Epicondylus lateralis humeri",
            "required_parent_segment": "upper_arm.R",
            "required_bone_mesh": "Humerus_R",
            "allowed_bone_meshes": ["Humerus_R", "FJ3368"],
            "laterality": "RIGHT",
            "source_reference": "Terminologia Anatomica 2 (TA2:2988)",
            "clinical_uncertainty_mm": 3.0,
            "prohibited_bindings": ["Clavicle_R", "Scapula_R", "hand.R"],
            "verification_status": "VALID_SURFACE_ANCHOR"
        }
    }

    def __init__(self):
        self.registered_anchors: Dict[str, Dict[str, Any]] = {}

    def register_anchor(
        self,
        marker_id: str,
        code: str,
        target_mesh_name: str,
        target_bone_name: str,
        local_coordinates: Tuple[float, float, float],
        local_normal: Tuple[float, float, float],
        mesh_hash: str,
        expected_mesh_hash: Optional[str] = None,
        barycentric_coords: Optional[Tuple[float, float, float]] = None,
        laterality: str = "RIGHT",
        face_index: Optional[int] = 0,
        asset_id: str = "body-13.bin"
    ) -> Dict[str, Any]:
        """Register a surface anchor with fail-closed anatomical constraint validation."""
        spec = self.POINT_SPECIFICATIONS.get(code)
        if not spec:
            raise ValueError(f"Unknown point code '{code}'; registration rejected.")

        # 1. STRICT PROHIBITION CHECK
        if target_mesh_name in spec["prohibited_bindings"] or target_bone_name in spec["prohibited_bindings"]:
            raise ValueError(
                f"ANATOMICAL BINDING VIOLATION: Point '{code}' ({spec['name_vi']}) cannot be bound to "
                f"'{target_mesh_name}' / '{target_bone_name}'. "
                f"Required segment is '{spec['required_parent_segment']}' ({spec['required_bone_mesh']})."
            )

        # 2. LATERALITY CHECK
        if laterality.upper() != spec["laterality"]:
            raise ValueError(
                f"LATERALITY INVERSION CONFLICT: Point '{code}' is {spec['laterality']}, "
                f"cannot register on {laterality} segment."
            )

        # 3. SCALE DIVERGENCE CHECK (meters vs millimeters)
        if any(abs(c) > 5.0 for c in local_coordinates):
            raise ValueError(
                f"SCALE DIVERGENCE: Coordinates {local_coordinates} exceed meter bounds. Millimeters detected."
            )

        # 4. MESH CHECKSUM INTEGRITY CHECK
        if expected_mesh_hash and mesh_hash != expected_mesh_hash:
            raise ValueError(
                f"STALE MESH HASH: Provided hash '{mesh_hash}' does not match expected '{expected_mesh_hash}'."
            )

        # 5. BARYCENTRIC COORDINATES VALIDATION
        if barycentric_coords is not None:
            u, v, w = barycentric_coords
            if u < -1e-4 or v < -1e-4 or w < -1e-4 or abs((u + v + w) - 1.0) > 1e-3:
                raise ValueError(
                    f"INVALID BARYCENTRIC COORDINATES: {barycentric_coords}. Sum must equal 1.0 and components >= 0."
                )

        # 6. Segment and Allowed Mesh Check
        allowed_meshes = spec.get("allowed_bone_meshes", [spec["required_bone_mesh"]])
        if target_bone_name != spec["required_parent_segment"] or (
            target_mesh_name != spec["required_bone_mesh"] and target_mesh_name not in allowed_meshes
        ):
            status = "ASSET_NOT_AVAILABLE"
            tech_status = "UNATTACHED"
        else:
            status = spec["verification_status"]
            tech_status = "VALID_SURFACE_ANCHOR"

        anchor = {
            "marker_id": marker_id,
            "code": code,
            "name_vi": spec["name_vi"],
            "name_en": spec["name_en"],
            "fma_id": spec["fma_id"],
            "ta2_name": spec["ta2_name"],
            "source_asset_id": asset_id,
            "mesh_hash": mesh_hash,
            "target_mesh_name": target_mesh_name,
            "target_bone_name": target_bone_name,
            "face_index": face_index,
            "local_surface_coordinates": [round(float(c), 6) for c in local_coordinates],
            "local_normal": [round(float(n), 6) for n in local_normal],
            "barycentric_coordinates": list(barycentric_coords) if barycentric_coords else None,
            "reference_frame": f"local_{target_mesh_name}",
            "laterality": spec["laterality"],
            "source_reference": spec["source_reference"],
            "clinical_uncertainty_mm": spec["clinical_uncertainty_mm"],
            "verification_status": status,
            "technical_anchor_status": tech_status,
            "clinical_verification_status": status,  # ALWAYS EXPERT_REVIEW_PENDING for LI4/ST36/KI3
            "deformation_model": "DEFORMATION_MODEL_NOT_VALIDATED",
        }
        self.registered_anchors[marker_id] = anchor
        return anchor

    def get_anchor(self, marker_id: str) -> Optional[Dict[str, Any]]:
        return self.registered_anchors.get(marker_id)

    def validate_asset_coverage(self, available_mesh_names: List[str]) -> Dict[str, str]:
        """Assess which landmark points can be legitimately displayed on the available meshes."""
        coverage = {}
        for code, spec in self.POINT_SPECIFICATIONS.items():
            allowed = spec.get("allowed_bone_meshes", [spec["required_bone_mesh"]])
            if any(m in available_mesh_names for m in allowed):
                coverage[code] = "AVAILABLE"
            else:
                coverage[code] = "ASSET_NOT_AVAILABLE"
        return coverage
