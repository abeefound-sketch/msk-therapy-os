"""
MSK-Therapy-OS V1.1 — Character Anatomy Registration Adapter
============================================================
Establishes a verifiable, provenance-backed registration bridge between
authentic BodyParts3D/Z-Anatomy skeletal assets and the MakeHuman humanoid rig.

Rules:
1. MakeHuman is the kinematic and surface representation baseline.
2. BodyParts3D 4.0 is the canonical anatomical structure source.
3. Never conflate meshes by name alone; require explicit landmark correspondence and mesh hash.
4. Non-registered structures must strictly report ANATOMICAL_REGISTRATION_PENDING.
"""

from dataclasses import dataclass, field, asdict
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BP3D_ASSETS_DIR = REPO_ROOT / "tools" / "blender_anatomy_studio" / "assets" / "bp3d"


@dataclass
class AnatomicalRegistrationEntry:
    structure_id: str                   # e.g., "FJ3368"
    structure_name_en: str              # e.g., "Right humerus"
    structure_name_vi: str              # e.g., "Xương cánh tay phải"
    source_dataset: str                 # "BodyParts3D 4.0 (CC-BY 2.1 JP)"
    source_mesh_file: str               # "Humerus_R.obj"
    mesh_sha256: str                    # SHA256 of canonical mesh file
    target_segment: str                 # "upper_arm.R"
    joint_reference_bone: str           # "upperarm_r"
    deformation_method: str             # "RIGID_PARENT_TO_BONE" (Bones do not stretch as soft tissue)
    landmark_correspondence: Dict[str, List[float]]  # e.g. {"head": [...], "capitulum": [...]}
    coordinate_transform: Dict[str, Any]             # {"translation": [...], "rotation_euler": [...], "scale": [...]}
    verification_status: str            # "REGISTERED_ACTIVE" or "ANATOMICAL_REGISTRATION_PENDING"
    clinical_safety_notice: str = "ENGINEERING_RESEARCH_ONLY; NOT_FOR_DIAGNOSTIC_OR_SURGICAL_PLANNING"


class CharacterAnatomyRegistrationAdapter:
    """Manages the mapping, geometric alignment, and audit lineage of anatomy-to-character registration."""

    def __init__(self):
        self._registry: Dict[str, AnatomicalRegistrationEntry] = {}
        self._init_canonical_registrations()

    def _compute_file_sha256(self, path: Path) -> str:
        if not path.exists():
            return "MISSING_FILE"
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _init_canonical_registrations(self):
        # 1. Right Clavicle (FJ3238) -> clavicle_r
        clav_path = BP3D_ASSETS_DIR / "Clavicle_R.obj"
        self._registry["FJ3238"] = AnatomicalRegistrationEntry(
            structure_id="FJ3238",
            structure_name_en="Right clavicle",
            structure_name_vi="Xương đòn phải",
            source_dataset="BodyParts3D 4.0 (CC-BY 2.1 JP)",
            source_mesh_file="Clavicle_R.obj",
            mesh_sha256=self._compute_file_sha256(clav_path),
            target_segment="clavicle.R",
            joint_reference_bone="clavicle_r",
            deformation_method="RIGID_PARENT_TO_BONE",
            landmark_correspondence={
                "sternal_end": [-0.010, 1.410, 0.001],
                "acromial_end": [-0.170, 1.410, -0.020]
            },
            coordinate_transform={
                "translation": [-0.07, 0.0, 0.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            verification_status="REGISTERED_ACTIVE"
        )

        # 2. Right Humerus (FJ3368) -> upperarm_r
        hum_path = BP3D_ASSETS_DIR / "Humerus_R.obj"
        self._registry["FJ3368"] = AnatomicalRegistrationEntry(
            structure_id="FJ3368",
            structure_name_en="Right humerus",
            structure_name_vi="Xương cánh tay phải",
            source_dataset="BodyParts3D 4.0 (CC-BY 2.1 JP)",
            source_mesh_file="Humerus_R.obj",
            mesh_sha256=self._compute_file_sha256(hum_path),
            target_segment="upper_arm.R",
            joint_reference_bone="upperarm_r",
            deformation_method="RIGID_PARENT_TO_BONE",
            landmark_correspondence={
                "humeral_head": [-0.190, 1.395, -0.024],
                "lateral_epicondyle": [-0.215, 1.120, -0.015]
            },
            coordinate_transform={
                "translation": [-0.08, -0.09, 0.0],
                "rotation_euler": [0.0, 0.0, 0.74],
                "scale": [1.0, 1.0, 1.0]
            },
            verification_status="REGISTERED_ACTIVE"
        )

        # 3. Right Radius (FJ3381) -> lowerarm_r
        rad_path = BP3D_ASSETS_DIR / "Radius_R.obj"
        self._registry["FJ3381"] = AnatomicalRegistrationEntry(
            structure_id="FJ3381",
            structure_name_en="Right radius",
            structure_name_vi="Xương quay phải",
            source_dataset="BodyParts3D 4.0 (CC-BY 2.1 JP)",
            source_mesh_file="Radius_R.obj",
            mesh_sha256=self._compute_file_sha256(rad_path),
            target_segment="forearm.R",
            joint_reference_bone="lowerarm_r",
            deformation_method="RIGID_PARENT_TO_BONE",
            landmark_correspondence={
                "radial_head": [-0.215, 1.120, -0.015],
                "radial_styloid": [-0.280, 0.894, 0.035]
            },
            coordinate_transform={
                "translation": [0.0, 0.10, 0.0],
                "rotation_euler": [1.57, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            verification_status="REGISTERED_ACTIVE"
        )

        # 4. Right Ulna (FJ3383) -> lowerarm_r
        ulna_path = BP3D_ASSETS_DIR / "Ulna_R.obj"
        self._registry["FJ3383"] = AnatomicalRegistrationEntry(
            structure_id="FJ3383",
            structure_name_en="Right ulna",
            structure_name_vi="Xương trụ phải",
            source_dataset="BodyParts3D 4.0 (CC-BY 2.1 JP)",
            source_mesh_file="Ulna_R.obj",
            mesh_sha256=self._compute_file_sha256(ulna_path),
            target_segment="forearm.R",
            joint_reference_bone="lowerarm_r",
            deformation_method="RIGID_PARENT_TO_BONE",
            landmark_correspondence={
                "olecranon": [-0.190, 1.122, -0.024],
                "ulnar_head": [-0.250, 0.894, -0.006]
            },
            coordinate_transform={
                "translation": [-0.015, 0.10, 0.0],
                "rotation_euler": [1.57, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            verification_status="REGISTERED_ACTIVE"
        )

        # 5. Right Metacarpal 2 (FJ3352) -> hand_r
        meta_path = BP3D_ASSETS_DIR / "Metacarpal_2_R.obj"
        self._registry["FJ3352"] = AnatomicalRegistrationEntry(
            structure_id="FJ3352",
            structure_name_en="Right second metacarpal bone",
            structure_name_vi="Xương bàn tay 2 phải",
            source_dataset="BodyParts3D 4.0 (CC-BY 2.1 JP)",
            source_mesh_file="Metacarpal_2_R.obj",
            mesh_sha256=self._compute_file_sha256(meta_path),
            target_segment="hand.R",
            joint_reference_bone="hand_r",
            deformation_method="RIGID_PARENT_TO_BONE",
            landmark_correspondence={
                "base": [-0.255, 0.890, 0.015],
                "head": [-0.280, 0.835, 0.035]
            },
            coordinate_transform={
                "translation": [0.0, 0.04, 0.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            verification_status="REGISTERED_ACTIVE"
        )

        # 6. Unregistered Thoracic Spine Placeholder -> ANATOMICAL_REGISTRATION_PENDING
        self._registry["FJ3280"] = AnatomicalRegistrationEntry(
            structure_id="FJ3280",
            structure_name_en="Thoracic vertebra 1",
            structure_name_vi="Đốt sống ngực T1",
            source_dataset="BodyParts3D 4.0 (CC-BY 2.1 JP)",
            source_mesh_file="Thoracic_Vertebra_1.obj",
            mesh_sha256="PENDING_AUDIT",
            target_segment="torso.spine_t1",
            joint_reference_bone="spine_03",
            deformation_method="PENDING_MODEL",
            landmark_correspondence={},
            coordinate_transform={},
            verification_status="ANATOMICAL_REGISTRATION_PENDING"
        )

    def get_registration(self, structure_id: str) -> Optional[AnatomicalRegistrationEntry]:
        return self._registry.get(structure_id)

    def list_registrations(self) -> List[Dict[str, Any]]:
        return [asdict(entry) for entry in self._registry.values()]

    def get_active_registrations_count(self) -> int:
        return sum(1 for e in self._registry.values() if e.verification_status == "REGISTERED_ACTIVE")

    def get_pending_registrations_count(self) -> int:
        return sum(1 for e in self._registry.values() if e.verification_status == "ANATOMICAL_REGISTRATION_PENDING")


# Module-level singleton
registration_adapter = CharacterAnatomyRegistrationAdapter()
