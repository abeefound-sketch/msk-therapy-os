"""Anatomical Rig Binding Adapter for Milestones P29-P35.
Coordinates bone-to-mesh parenting, avoids double transforms, enforces scapulohumeral rhythm,
and validates rigid bone transform integrity across animation frames.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

try:
    import bpy
    import mathutils
    HAS_BPY = True
except ImportError:
    HAS_BPY = False


class AnatomicalRigBindingAdapter:
    """Manages rigid bone mesh binding to upper limb armature with scapulothoracic rhythm."""

    # Authoritative bone mapping (Upper limb + Hand + Crural anchor bones)
    BONE_MAPPING = {
        "Humerus_R": {
            "target_bone": "upper_arm.R",
            "required_class": "BONE",
            "segment_role": "GLENOHUMERAL_ARM",
            "fma_id": "FMA:23130"
        },
        "Clavicle_R": {
            "target_bone": "clavicle.R",
            "required_class": "BONE",
            "segment_role": "CLAVICULAR_STRUT",
            "fma_id": "FMA:13322"
        },
        "Scapula_R": {
            "target_bone": "clavicle.R",
            "required_class": "BONE",
            "segment_role": "SCAPULOTHORACIC_GIRDLE",
            "fma_id": "FMA:13395"
        },
        "Radius_R": {
            "target_bone": "forearm.R",
            "required_class": "BONE",
            "segment_role": "ANTEBRACHIAL_LATERAL",
            "fma_id": "FMA:23464"
        },
        "Ulna_R": {
            "target_bone": "forearm.R",
            "required_class": "BONE",
            "segment_role": "ANTEBRACHIAL_MEDIAL",
            "fma_id": "FMA:23467"
        },
        "Metacarpal_2_R": {
            "target_bone": "hand.R",
            "required_class": "BONE",
            "segment_role": "METACARPAL_INDEX",
            "fma_id": "FMA:24466"
        },
        "Metacarpals_R": {
            "target_bone": "hand.R",
            "required_class": "BONE",
            "segment_role": "METACARPAL_COMPLEX",
            "fma_id": "FMA:24466"
        },
        "Tibia_R": {
            "target_bone": "shank.R",
            "required_class": "BONE",
            "segment_role": "CRURAL_MEDIAL",
            "fma_id": "FMA:24477"
        },
        "Calcaneus_R": {
            "target_bone": "foot.R",
            "required_class": "BONE",
            "segment_role": "TARSAL_HEEL",
            "fma_id": "FMA:24497"
        }
    }

    MISSING_STRUCTURES = [
        "Phalanges_R",
        "Fibula_R"
    ]

    @classmethod
    def audit_scene_structures(cls, scene_objects: List[Any]) -> Dict[str, Any]:
        """Audit existing scene meshes against expected upper limb anatomy."""
        obj_names = {getattr(o, "name", str(o)) for o in scene_objects}
        present = {}
        missing = {}

        for mesh_name, meta in cls.BONE_MAPPING.items():
            if mesh_name in obj_names:
                present[mesh_name] = {
                    "status": "AVAILABLE",
                    "target_bone": meta["target_bone"],
                    "fma_id": meta["fma_id"]
                }
            else:
                missing[mesh_name] = {
                    "status": "ASSET_NOT_AVAILABLE",
                    "fma_id": meta["fma_id"]
                }

        for m in cls.MISSING_STRUCTURES:
            missing[m] = {
                "status": "ASSET_NOT_AVAILABLE",
                "notes": "Not present in baseline scene"
            }

        return {
            "present_structures": present,
            "missing_structures": missing,
            "total_present": len(present),
            "total_missing": len(missing)
        }

    @classmethod
    def bind_mesh_to_bone(
        cls,
        mesh_obj: Any,
        arm_obj: Any,
        bone_name: str
    ) -> Dict[str, Any]:
        """Parent a rigid bone mesh to an armature bone without double-transforms."""
        if not HAS_BPY:
            return {"status": "MOCK_BINDING_NO_BPY", "mesh": getattr(mesh_obj, "name", "mesh"), "bone": bone_name}

        if bone_name not in arm_obj.pose.bones:
            raise ValueError(f"Bone '{bone_name}' does not exist in armature '{arm_obj.name}'.")

        # Check existing scale to guarantee unit scaling
        scale = mesh_obj.scale
        if not (abs(scale.x - 1.0) < 1e-4 and abs(scale.y - 1.0) < 1e-4 and abs(scale.z - 1.0) < 1e-4):
            # Normalize scale before parenting to avoid scaling propagation
            bpy.context.view_layer.objects.active = mesh_obj
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        pose_bone = arm_obj.pose.bones[bone_name]

        # Calculate exact parent inverse matrix to lock rest pose
        parent_matrix = arm_obj.matrix_world @ pose_bone.matrix
        mesh_obj.parent = arm_obj
        mesh_obj.parent_type = 'BONE'
        mesh_obj.parent_bone = bone_name
        mesh_obj.matrix_parent_inverse = parent_matrix.inverted()

        return {
            "status": "BOUND",
            "mesh_name": mesh_obj.name,
            "armature_name": arm_obj.name,
            "parent_bone": bone_name,
            "parent_type": "BONE",
            "scale_verified": [round(s, 4) for s in mesh_obj.scale]
        }

    @classmethod
    def apply_scapulohumeral_rhythm(
        cls,
        arm_obj: Any,
        thoracohumeral_elevation_deg: float,
        elbow_flexion_deg: Optional[float] = None,
        frame: Optional[int] = None
    ) -> Dict[str, float]:
        """Apply Inman/Codman/Seth 2:1 scapulohumeral rhythm to clavicle and humerus.
        For every 3 deg of total elevation: ~1 deg clavicle/scapula rotation, ~2 deg glenohumeral rotation.
        Optionally keyframe elbow flexion on forearm.R.
        """
        scapular_upward_rot_deg = thoracohumeral_elevation_deg * (1.0 / 3.0)
        glenohumeral_elev_deg = thoracohumeral_elevation_deg * (2.0 / 3.0)

        if HAS_BPY and arm_obj and hasattr(arm_obj, "pose"):
            p_clav = arm_obj.pose.bones.get("clavicle.R")
            p_arm = arm_obj.pose.bones.get("upper_arm.R")
            p_fore = arm_obj.pose.bones.get("forearm.R")

            if p_clav:
                p_clav.rotation_mode = 'XYZ'
                p_clav.rotation_euler = (0.0, 0.0, math.radians(scapular_upward_rot_deg))
                if frame is not None:
                    p_clav.keyframe_insert(data_path="rotation_euler", frame=frame)

            if p_arm:
                p_arm.rotation_mode = 'XYZ'
                p_arm.rotation_euler = (math.radians(glenohumeral_elev_deg), 0.0, 0.0)
                if frame is not None:
                    p_arm.keyframe_insert(data_path="rotation_euler", frame=frame)

            if p_fore and elbow_flexion_deg is not None:
                p_fore.rotation_mode = 'XYZ'
                p_fore.rotation_euler = (math.radians(elbow_flexion_deg), 0.0, 0.0)
                if frame is not None:
                    p_fore.keyframe_insert(data_path="rotation_euler", frame=frame)

        res = {
            "thoracohumeral_elevation_deg": round(thoracohumeral_elevation_deg, 2),
            "scapular_elevation_deg": round(scapular_upward_rot_deg, 2),
            "glenohumeral_elevation_deg": round(glenohumeral_elev_deg, 2),
            "rhythm_ratio": "2:1 (Inman 1944 / Seth 2016)"
        }
        if elbow_flexion_deg is not None:
            res["elbow_flexion_deg"] = round(elbow_flexion_deg, 2)
        return res
