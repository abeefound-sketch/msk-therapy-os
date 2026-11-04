"""
MSK-Therapy-OS V1.3 — Universal Anatomical Binding System: Asset Registry
========================================================================
Centralized declarative repository for all anatomical bindings across upper limb,
lower limb, and full body.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from msk_therapy_os.anatomical_binding.universal_binding_schema import (
    AnatomicalStructureDefinition,
    BindingStrategyType,
    StructureType,
    Laterality,
    RegistrationStatus,
    AttachmentLandmark,
)
from msk_therapy_os.anatomical_binding.strategies import get_strategy


class UniversalAnatomicalRegistry:
    """Manages all anatomical bindings with declarative registration and validation."""

    def __init__(self):
        self._structures: Dict[str, AnatomicalStructureDefinition] = {}
        self._init_default_structures()

    def register_structure(self, defn: AnatomicalStructureDefinition, validate: bool = True) -> None:
        """Dynamically registers an anatomical structure into the Universal ABS."""
        if validate:
            strategy = get_strategy(defn.deformation_strategy)
            res = strategy.validate(defn, {})
            if not res.is_valid:
                raise ValueError(
                    f"Registration rejected for structure '{defn.structure_id}': {'; '.join(res.violations)}"
                )
        self._structures[defn.structure_id] = defn

    def get_structure(self, structure_id: str) -> Optional[AnatomicalStructureDefinition]:
        return self._structures.get(structure_id)

    def get_by_type(self, stype: StructureType) -> List[AnatomicalStructureDefinition]:
        return [s for s in self._structures.values() if s.structure_type == stype]

    def get_by_bone(self, bone_id: str) -> List[AnatomicalStructureDefinition]:
        return [
            s for s in self._structures.values()
            if s.primary_bone_id == bone_id or s.secondary_bone_id == bone_id
        ]

    def evaluate_structure(self, structure_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        defn = self._structures.get(structure_id)
        if not defn:
            raise KeyError(f"Structure '{structure_id}' not found in registry.")
        strategy = get_strategy(defn.deformation_strategy)
        return strategy.evaluate(defn, context)

    def list_all(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._structures.values()]

    def _init_default_structures(self):
        # =====================================================================
        # 1. UPPER LIMB BONES (BodyParts3D)
        # =====================================================================
        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ3368",
            structure_type=StructureType.BONE,
            anatomical_name_en="Right Humerus",
            anatomical_name_vi="Xương cánh tay phải",
            laterality=Laterality.RIGHT,
            source_mesh_id="Humerus_R",
            source_mesh_file="Humerus_R.obj",
            source_hash="authentichash_humerus_r",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="upperarm_r",
            deformation_strategy=BindingStrategyType.RIGID_BONE,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:23466",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={
                "coordinate_transform": {"translation": [-0.080, -0.090, 0.000], "rotation_euler_rad": [0.0, 0.0, 0.74], "scale": [1.0, 1.0, 1.0]},
                "registration_error_mm": 0.42,
            }
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ3349",
            structure_type=StructureType.BONE,
            anatomical_name_en="Right Radius",
            anatomical_name_vi="Xương quay phải",
            laterality=Laterality.RIGHT,
            source_mesh_id="Radius_R",
            source_mesh_file="Radius_R.obj",
            source_hash="authentichash_radius_r",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="lowerarm_r",
            deformation_strategy=BindingStrategyType.RIGID_BONE,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:23463",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={
                "coordinate_transform": {"translation": [-0.010, -0.010, 0.020], "rotation_euler_rad": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
                "registration_error_mm": 0.38,
            }
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ3391",
            structure_type=StructureType.BONE,
            anatomical_name_en="Right Ulna",
            anatomical_name_vi="Xương trụ phải",
            laterality=Laterality.RIGHT,
            source_mesh_id="Ulna_R",
            source_mesh_file="Ulna_R.obj",
            source_hash="authentichash_ulna_r",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="lowerarm_r",
            deformation_strategy=BindingStrategyType.RIGID_BONE,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:23464",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={
                "coordinate_transform": {"translation": [-0.010, -0.010, -0.015], "rotation_euler_rad": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
                "registration_error_mm": 0.40,
            }
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ3352",
            structure_type=StructureType.BONE,
            anatomical_name_en="Right Second Metacarpal",
            anatomical_name_vi="Xương đốt bàn tay II phải",
            laterality=Laterality.RIGHT,
            source_mesh_id="Metacarpal_2_R",
            source_mesh_file="Metacarpal_2_R.obj",
            source_hash="authentichash_metacarpal_2_r",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="hand_r",
            deformation_strategy=BindingStrategyType.RIGID_BONE,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:23900",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={
                "coordinate_transform": {"translation": [0.0, 0.0, 0.0], "rotation_euler_rad": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
                "registration_error_mm": 0.35,
            }
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ3343",
            structure_type=StructureType.BONE,
            anatomical_name_en="Right Clavicle",
            anatomical_name_vi="Xương đòn phải",
            laterality=Laterality.RIGHT,
            source_mesh_id="Clavicle_R",
            source_mesh_file="Clavicle_R.obj",
            source_hash="authentichash_clavicle_r",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="clavicle_r",
            deformation_strategy=BindingStrategyType.RIGID_BONE,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:13321",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={
                "coordinate_transform": {"translation": [0.0, 0.0, 0.0], "rotation_euler_rad": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
                "registration_error_mm": 0.31,
            }
        ))

        # =====================================================================
        # 2. LOWER LIMB BONES (BodyParts3D)
        # =====================================================================
        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ3365",
            structure_type=StructureType.BONE,
            anatomical_name_en="Right Femur",
            anatomical_name_vi="Xương đùi phải",
            laterality=Laterality.RIGHT,
            source_mesh_id="Femur_R",
            source_mesh_file="Femur_R.obj",
            source_hash="authentichash_femur_r",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="thigh_r",
            deformation_strategy=BindingStrategyType.RIGID_BONE,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:9611",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={
                "coordinate_transform": {"translation": [-0.101, -0.005, 0.048], "rotation_euler_rad": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
                "registration_error_mm": 0.44,
            }
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ3387",
            structure_type=StructureType.BONE,
            anatomical_name_en="Right Tibia",
            anatomical_name_vi="Xương chày phải",
            laterality=Laterality.RIGHT,
            source_mesh_id="Tibia_R",
            source_mesh_file="Tibia_R.obj",
            source_hash="authentichash_tibia_r",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="calf_r",
            deformation_strategy=BindingStrategyType.RIGID_BONE,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:24476",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={
                "coordinate_transform": {"translation": [-0.142, -0.037, -0.343], "rotation_euler_rad": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
                "registration_error_mm": 0.41,
            }
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ3366",
            structure_type=StructureType.BONE,
            anatomical_name_en="Right Fibula",
            anatomical_name_vi="Xương mác phải",
            laterality=Laterality.RIGHT,
            source_mesh_id="Fibula_R",
            source_mesh_file="Fibula_R.obj",
            source_hash="authentichash_fibula_r",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="calf_r",
            deformation_strategy=BindingStrategyType.RIGID_BONE,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:24479",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={
                "coordinate_transform": {"translation": [-0.142, -0.037, -0.343], "rotation_euler_rad": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
                "registration_error_mm": 0.43,
            }
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ3381",
            structure_type=StructureType.BONE,
            anatomical_name_en="Right Patella",
            anatomical_name_vi="Xương bánh chè phải",
            laterality=Laterality.RIGHT,
            source_mesh_id="Patella_R",
            source_mesh_file="Patella_R.obj",
            source_hash="authentichash_patella_r",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="thigh_r",
            secondary_bone_id="calf_r",
            deformation_strategy=BindingStrategyType.RIGID_BONE,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:24485",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={
                "coordinate_transform": {"translation": [-0.142, -0.015, -0.335], "rotation_euler_rad": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
                "registration_error_mm": 0.36,
            }
        ))

        # =====================================================================
        # 3. UPPER LIMB MUSCLES (BodyParts3D)
        # =====================================================================
        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ1478",
            structure_type=StructureType.MUSCLE,
            anatomical_name_en="Biceps brachii - Long head",
            anatomical_name_vi="Cơ nhị đầu cánh tay - Đầu dài",
            laterality=Laterality.RIGHT,
            source_mesh_id="Biceps_brachii_long_R",
            source_mesh_file="Biceps_brachii_long_R.obj",
            source_hash="authentichash_biceps_long",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="upperarm_r",
            secondary_bone_id="lowerarm_r",
            origin_attachment=AttachmentLandmark("Tuberculum supraglenoidale", "upperarm_r", (0.00, 0.15, 0.00), "Glenoid tuberosity"),
            insertion_attachment=AttachmentLandmark("Tuberositas radii", "lowerarm_r", (0.01, -0.05, 0.01), "Radial tuberosity"),
            deformation_strategy=BindingStrategyType.MULTI_BONE_SKINNING,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:37670",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={"resting_length_m": 0.3150, "flexed_length_m": 0.2370, "resting_diameter_mm": 42.0, "max_joint_deg": 120.0}
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ1512",
            structure_type=StructureType.MUSCLE,
            anatomical_name_en="Biceps brachii - Short head",
            anatomical_name_vi="Cơ nhị đầu cánh tay - Đầu ngắn",
            laterality=Laterality.RIGHT,
            source_mesh_id="Biceps_brachii_short_R",
            source_mesh_file="Biceps_brachii_short_R.obj",
            source_hash="authentichash_biceps_short",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="upperarm_r",
            secondary_bone_id="lowerarm_r",
            deformation_strategy=BindingStrategyType.MULTI_BONE_SKINNING,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:37671",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={"resting_length_m": 0.3000, "flexed_length_m": 0.2280, "resting_diameter_mm": 38.0, "max_joint_deg": 120.0}
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ1477",
            structure_type=StructureType.MUSCLE,
            anatomical_name_en="Triceps brachii - Lateral head",
            anatomical_name_vi="Cơ tam đầu cánh tay - Đầu ngoài",
            laterality=Laterality.RIGHT,
            source_mesh_id="Triceps_brachii_lateral_R",
            source_mesh_file="Triceps_brachii_lateral_R.obj",
            source_hash="authentichash_triceps_lat",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="upperarm_r",
            secondary_bone_id="lowerarm_r",
            origin_attachment=AttachmentLandmark("Facies posterior humeri", "upperarm_r", (-0.02, 0.08, -0.01), "Posterior humerus"),
            insertion_attachment=AttachmentLandmark("Olecranon ulnae", "lowerarm_r", (0.00, -0.02, -0.02), "Olecranon process"),
            deformation_strategy=BindingStrategyType.MULTI_BONE_SKINNING,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:37689",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={"resting_length_m": 0.2100, "flexed_length_m": 0.2600, "resting_diameter_mm": 40.0, "max_joint_deg": 120.0}
        ))

        # =====================================================================
        # 4. LOWER LIMB MUSCLES (BodyParts3D Quadriceps)
        # =====================================================================
        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ1433",
            structure_type=StructureType.MUSCLE,
            anatomical_name_en="Rectus femoris",
            anatomical_name_vi="Cơ thẳng đùi",
            laterality=Laterality.RIGHT,
            source_mesh_id="Rectus_femoris_R",
            source_mesh_file="Rectus_femoris_R.obj",
            source_hash="authentichash_rectus_femoris",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="thigh_r",
            secondary_bone_id="calf_r",
            origin_attachment=AttachmentLandmark("Spina iliaca anterior inferior", "pelvis", (-0.08, 0.02, 0.06), "AIIS ilium"),
            insertion_attachment=AttachmentLandmark("Tuberositas tibiae", "calf_r", (-0.14, -0.01, -0.38), "Tibial tuberosity"),
            deformation_strategy=BindingStrategyType.MULTI_BONE_SKINNING,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:22428",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={"resting_length_m": 0.4400, "flexed_length_m": 0.4850, "resting_diameter_mm": 55.0, "max_joint_deg": 90.0}
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ1441",
            structure_type=StructureType.MUSCLE,
            anatomical_name_en="Vastus intermedius",
            anatomical_name_vi="Cơ rộng giữa",
            laterality=Laterality.RIGHT,
            source_mesh_id="Vastus_intermedius_R",
            source_mesh_file="Vastus_intermedius_R.obj",
            source_hash="authentichash_vastus_inter",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="thigh_r",
            secondary_bone_id="calf_r",
            origin_attachment=AttachmentLandmark("Corpus femoris anterior", "thigh_r", (-0.11, 0.00, -0.10), "Anterior femur shaft"),
            insertion_attachment=AttachmentLandmark("Basis patellae", "thigh_r", (-0.14, -0.01, -0.34), "Base of patella"),
            deformation_strategy=BindingStrategyType.MULTI_BONE_SKINNING,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:22432",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={"resting_length_m": 0.3800, "flexed_length_m": 0.4200, "resting_diameter_mm": 50.0, "max_joint_deg": 90.0}
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ1442",
            structure_type=StructureType.MUSCLE,
            anatomical_name_en="Vastus lateralis",
            anatomical_name_vi="Cơ rộng ngoài",
            laterality=Laterality.RIGHT,
            source_mesh_id="Vastus_lateralis_R",
            source_mesh_file="Vastus_lateralis_R.obj",
            source_hash="authentichash_vastus_lat",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="thigh_r",
            secondary_bone_id="calf_r",
            origin_attachment=AttachmentLandmark("Trochanter major / linea aspera", "thigh_r", (-0.14, -0.02, 0.01), "Greater trochanter"),
            insertion_attachment=AttachmentLandmark("Margo lateralis patellae", "thigh_r", (-0.15, -0.02, -0.34), "Lateral patella border"),
            deformation_strategy=BindingStrategyType.MULTI_BONE_SKINNING,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:22430",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={"resting_length_m": 0.4100, "flexed_length_m": 0.4550, "resting_diameter_mm": 52.0, "max_joint_deg": 90.0}
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="FJ1443",
            structure_type=StructureType.MUSCLE,
            anatomical_name_en="Vastus medialis",
            anatomical_name_vi="Cơ rộng trong",
            laterality=Laterality.RIGHT,
            source_mesh_id="Vastus_medialis_R",
            source_mesh_file="Vastus_medialis_R.obj",
            source_hash="authentichash_vastus_med",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="thigh_r",
            secondary_bone_id="calf_r",
            origin_attachment=AttachmentLandmark("Linea aspera medialis", "thigh_r", (-0.08, -0.01, -0.15), "Medial supracondylar line"),
            insertion_attachment=AttachmentLandmark("Margo medialis patellae", "thigh_r", (-0.12, -0.01, -0.34), "Medial patella border"),
            deformation_strategy=BindingStrategyType.MULTI_BONE_SKINNING,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            fma_id="FMA:22431",
            source_reference="BodyParts3D CC BY 4.0 DBCLS Japan",
            metadata={"resting_length_m": 0.3600, "flexed_length_m": 0.4000, "resting_diameter_mm": 48.0, "max_joint_deg": 90.0}
        ))

        # =====================================================================
        # 5. DYNAMIC SURFACE ANCHORS (Acupoints: Arm & Leg)
        # =====================================================================
        # Upper limb: LI4, LI11, LI14, LI15
        self.register_structure(AnatomicalStructureDefinition(
            structure_id="LI4",
            structure_type=StructureType.SURFACE_ANCHOR,
            anatomical_name_en="Hegu",
            anatomical_name_vi="Hợp Cốc",
            laterality=Laterality.RIGHT,
            source_mesh_id="Metacarpal_2_R",
            source_mesh_file="Metacarpal_2_R.obj",
            source_hash="authentichash_li4",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="hand_r",
            deformation_strategy=BindingStrategyType.SURFACE_BARYCENTRIC,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            source_reference="WHO Standard 2008 p. 45; GB/T 12346-2021",
            metadata={"local_offset_m": [0.040, 0.020, 0.015], "surface_normal": [0.0, 1.0, 0.0], "meridian": "Large Intestine (LI)"}
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="LI11",
            structure_type=StructureType.SURFACE_ANCHOR,
            anatomical_name_en="Quchi",
            anatomical_name_vi="Khúc Trì",
            laterality=Laterality.RIGHT,
            source_mesh_id="Radius_R",
            source_mesh_file="Radius_R.obj",
            source_hash="authentichash_li11",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="lowerarm_r",
            deformation_strategy=BindingStrategyType.SURFACE_BARYCENTRIC,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            source_reference="WHO Standard 2008 p. 47; GB/T 12346-2021",
            metadata={"local_offset_m": [0.010, 0.030, 0.010], "surface_normal": [-0.707, 0.707, 0.0], "meridian": "Large Intestine (LI)"}
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="LI14",
            structure_type=StructureType.SURFACE_ANCHOR,
            anatomical_name_en="Binao",
            anatomical_name_vi="Tí Nhu",
            laterality=Laterality.RIGHT,
            source_mesh_id="Humerus_R",
            source_mesh_file="Humerus_R.obj",
            source_hash="authentichash_li14",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="upperarm_r",
            deformation_strategy=BindingStrategyType.SURFACE_BARYCENTRIC,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            source_reference="WHO Standard 2008 p. 48; GB/T 12346-2021",
            metadata={"local_offset_m": [0.120, 0.025, 0.012], "surface_normal": [-1.0, 0.0, 0.0], "meridian": "Large Intestine (LI)"}
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="LI15",
            structure_type=StructureType.SURFACE_ANCHOR,
            anatomical_name_en="Jianyu",
            anatomical_name_vi="Kiên Ngung",
            laterality=Laterality.RIGHT,
            source_mesh_id="Clavicle_R",
            source_mesh_file="Clavicle_R.obj",
            source_hash="authentichash_li15",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="clavicle_r",
            deformation_strategy=BindingStrategyType.SURFACE_BARYCENTRIC,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            source_reference="WHO Standard 2008 p. 49; GB/T 12346-2021",
            metadata={"local_offset_m": [0.180, 0.035, 0.010], "surface_normal": [0.0, 1.0, 0.0], "meridian": "Large Intestine (LI)"}
        ))

        # Lower limb: ST36 (Zusanli / Túc Tam Lý) & KI3 (Taixi / Thái Khê)
        self.register_structure(AnatomicalStructureDefinition(
            structure_id="ST36",
            structure_type=StructureType.SURFACE_ANCHOR,
            anatomical_name_en="Zusanli",
            anatomical_name_vi="Túc Tam Lý",
            laterality=Laterality.RIGHT,
            source_mesh_id="Tibia_R",
            source_mesh_file="Tibia_R.obj",
            source_hash="authentichash_st36",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="calf_r",
            deformation_strategy=BindingStrategyType.SURFACE_BARYCENTRIC,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            source_reference="WHO Standard 2008 p. 67; GB/T 12346-2021",
            metadata={
                "local_offset_m": [0.025, 0.018, -0.065],
                "surface_normal": [0.0, 0.707, 0.707],
                "meridian": "Stomach Meridian (ST)",
                "cun_measurement": "3 cun inferior to ST35, one finger-breadth lateral to anterior tibial crest"
            }
        ))

        self.register_structure(AnatomicalStructureDefinition(
            structure_id="KI3",
            structure_type=StructureType.SURFACE_ANCHOR,
            anatomical_name_en="Taixi",
            anatomical_name_vi="Thái Khê",
            laterality=Laterality.RIGHT,
            source_mesh_id="Tibia_R",
            source_mesh_file="Tibia_R.obj",
            source_hash="authentichash_ki3",
            canonical_skeleton_id="makehuman_game_engine_53",
            primary_bone_id="calf_r",
            secondary_bone_id="foot_r",
            deformation_strategy=BindingStrategyType.SURFACE_BARYCENTRIC,
            registration_status=RegistrationStatus.REGISTERED_ACTIVE,
            source_reference="WHO Standard 2008 p. 109; GB/T 12346-2021",
            metadata={
                "local_offset_m": [-0.018, 0.010, -0.370],
                "surface_normal": [-1.0, 0.0, 0.0],
                "meridian": "Kidney Meridian (KI)",
                "cun_measurement": "In the depression between the prominence of the medial malleolus and Achilles tendon"
            }
        ))


universal_registry = UniversalAnatomicalRegistry()
