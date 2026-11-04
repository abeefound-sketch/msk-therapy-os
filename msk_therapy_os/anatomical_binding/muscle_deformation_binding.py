"""
MSK-Therapy-OS V1.2 — Anatomical Binding System: Muscle Deformation Binding
===========================================================================
Defines the biomechanical deformation models for authentic arm muscles:
- Biceps brachii (Long head FJ1478, Short head FJ1512)
- Triceps brachii (Lateral head FJ1477, Long head FJ1479, Medial head FJ1480)
- Brachialis (FJ1486)

Biomechanical Principles:
1. Dual-bone attachment: Muscle bridges across joint (e.g. upperarm_r to lowerarm_r).
2. Physiological muscle path: Evaluated from anatomical origin landmarks to insertion landmarks.
3. Length change & Contraction ratio:
   - Elbow flexion 0° -> 90° shortens Biceps by ~22-26% (contraction ratio ~0.74 - 0.78).
   - Elbow flexion 0° -> 90° elongates Triceps by ~18-22% (stretch ratio ~1.18 - 1.22).
4. Isovolumetric volume conservation:
   - When muscle length shortens: transversal cross-section increases (muscle belly bulge).
   - Radial bulge factor: k_bulge = sqrt(L_rest / L_curr).
5. Vertex weight distribution:
   - Proximal vertices near origin -> 100% upperarm_r (or scapula/clavicle).
   - Distal vertices near insertion -> 100% lowerarm_r.
   - Intermediate belly vertices -> smooth transition with non-linear bulge along normal.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from msk_therapy_os.canonical_skeleton_adapter import Laterality

REPO_ROOT = Path(__file__).resolve().parents[2]
BP3D_DIR = REPO_ROOT / "tools" / "blender_anatomy_studio" / "assets" / "bp3d"


class DeformationStrategy(str, Enum):
    DUAL_BONE_SKINNING_AND_BULGE = "DUAL_BONE_SKINNING_AND_BULGE"
    RIGID_SEGMENT_TRACKING = "RIGID_SEGMENT_TRACKING"
    MORPH_TARGET_BULGE = "MORPH_TARGET_BULGE"


@dataclass
class MuscleBiomechanicalState:
    muscle_id: str
    elbow_flexion_deg: float
    current_length_m: float
    resting_length_m: float
    contraction_ratio: float           # L_curr / L_rest (< 1.0 is contraction, > 1.0 is stretch)
    bulge_factor: float                # sqrt(L_rest / L_curr) for isovolumetric bulging
    state_description: str             # "CONTRACTING_BULGING", "STRETCHED", "RESTING"


@dataclass
class MuscleDeformationBindingEntry:
    anatomy_id: str
    muscle_name_en: str
    muscle_name_vi: str
    source_mesh_id: str
    source_mesh_file: str
    source_hash: str
    canonical_origin_bone: str         # Bone containing origin
    canonical_insertion_bone: str      # Bone containing insertion
    origin_landmark_m: Tuple[float, float, float]
    insertion_landmark_m: Tuple[float, float, float]
    resting_length_m: float            # At elbow 0°
    flexed_length_90_m: float          # At elbow 90°
    expected_contraction_90: float     # L_flex / L_rest
    deformation_strategy: DeformationStrategy
    laterality: Laterality
    volume_preservation_enabled: bool = True
    verification_status: str = "REGISTERED_ACTIVE"
    clinical_safety_notice: str = "ENGINEERING_RESEARCH_ONLY; NOT_FOR_CLINICAL_USE"

    def evaluate_state(self, elbow_flexion_deg: float) -> MuscleBiomechanicalState:
        """Evaluates muscle length, contraction ratio, and bulge factor for a given elbow angle."""
        theta_rad = math.radians(elbow_flexion_deg)
        # Approximate physiological path shortening/lengthening using law of cosines around elbow pivot:
        # L(theta)^2 = r_orig^2 + r_ins^2 - 2 * r_orig * r_ins * cos(phi - sign * theta)
        # For small angles, linear/cos interpolation between 0° and 90°:
        t = math.sin(theta_rad / 2.0)  # non-linear physiological progression
        L_rest = self.resting_length_m
        L_90 = self.flexed_length_90_m
        L_curr = L_rest + (L_90 - L_rest) * (t * math.sqrt(2))  # normalized to 90 deg where theta/2 = 45 deg

        contraction_ratio = round(L_curr / L_rest, 4)
        if self.volume_preservation_enabled and contraction_ratio < 1.0:
            bulge_factor = round(math.sqrt(1.0 / max(contraction_ratio, 0.4)), 4)
            desc = "CONTRACTING_BULGING"
        elif contraction_ratio > 1.0:
            bulge_factor = round(math.sqrt(1.0 / contraction_ratio), 4)
            desc = "STRETCHED"
        else:
            bulge_factor = 1.0
            desc = "RESTING"

        return MuscleBiomechanicalState(
            muscle_id=self.anatomy_id,
            elbow_flexion_deg=elbow_flexion_deg,
            current_length_m=round(L_curr, 4),
            resting_length_m=round(L_rest, 4),
            contraction_ratio=contraction_ratio,
            bulge_factor=bulge_factor,
            state_description=desc
        )


class MuscleDeformationAdapter:
    """Manages muscle registrations and real-time biomechanical deformation evaluations."""

    def __init__(self):
        self._muscles: Dict[str, MuscleDeformationBindingEntry] = {}
        self._init_canonical_muscles()

    def _file_hash(self, filename: str) -> str:
        p = BP3D_DIR / filename
        if not p.exists():
            return "MISSING"
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def _init_canonical_muscles(self):
        # 1. Biceps brachii - Long head (FJ1478)
        # Origin: Supraglenoid tubercle of scapula
        # Insertion: Radial tuberosity of radius
        self._muscles["FJ1478"] = MuscleDeformationBindingEntry(
            anatomy_id="FJ1478",
            muscle_name_en="Biceps brachii (Long head)",
            muscle_name_vi="Cơ nhị đầu cánh tay (Đầu dài)",
            source_mesh_id="Biceps_brachii_long_R",
            source_mesh_file="Biceps_brachii_long_R.obj",
            source_hash=self._file_hash("Biceps_brachii_long_R.obj"),
            canonical_origin_bone="upperarm_r",
            canonical_insertion_bone="lowerarm_r",
            origin_landmark_m=(-0.170, 0.502, -0.019),
            insertion_landmark_m=(-0.340, 0.300, -0.015),
            resting_length_m=0.315,
            flexed_length_90_m=0.242,
            expected_contraction_90=0.768,  # ~23.2% shortening
            deformation_strategy=DeformationStrategy.DUAL_BONE_SKINNING_AND_BULGE,
            laterality=Laterality.RIGHT,
        )

        # 2. Biceps brachii - Short head (FJ1512)
        # Origin: Coracoid process of scapula
        # Insertion: Radial tuberosity
        self._muscles["FJ1512"] = MuscleDeformationBindingEntry(
            anatomy_id="FJ1512",
            muscle_name_en="Biceps brachii (Short head)",
            muscle_name_vi="Cơ nhị đầu cánh tay (Đầu ngắn)",
            source_mesh_id="Biceps_brachii_short_R",
            source_mesh_file="Biceps_brachii_short_R.obj",
            source_hash=self._file_hash("Biceps_brachii_short_R.obj"),
            canonical_origin_bone="upperarm_r",
            canonical_insertion_bone="lowerarm_r",
            origin_landmark_m=(-0.165, 0.495, -0.010),
            insertion_landmark_m=(-0.340, 0.300, -0.015),
            resting_length_m=0.298,
            flexed_length_90_m=0.230,
            expected_contraction_90=0.772,  # ~22.8% shortening
            deformation_strategy=DeformationStrategy.DUAL_BONE_SKINNING_AND_BULGE,
            laterality=Laterality.RIGHT,
        )

        # 3. Triceps brachii - Lateral head (FJ1477)
        # Origin: Posterior surface of humerus
        # Insertion: Olecranon of ulna
        self._muscles["FJ1477"] = MuscleDeformationBindingEntry(
            anatomy_id="FJ1477",
            muscle_name_en="Triceps brachii (Lateral head)",
            muscle_name_vi="Cơ tam đầu cánh tay (Đầu ngoài)",
            source_mesh_id="Triceps_brachii_lateral_R",
            source_mesh_file="Triceps_brachii_lateral_R.obj",
            source_hash=self._file_hash("Triceps_brachii_lateral_R.obj"),
            canonical_origin_bone="upperarm_r",
            canonical_insertion_bone="lowerarm_r",
            origin_landmark_m=(-0.200, 0.450, -0.055),
            insertion_landmark_m=(-0.335, 0.320, -0.060),
            resting_length_m=0.210,
            flexed_length_90_m=0.252,
            expected_contraction_90=1.200,  # ~20% stretch
            deformation_strategy=DeformationStrategy.DUAL_BONE_SKINNING_AND_BULGE,
            laterality=Laterality.RIGHT,
        )

        # 4. Triceps brachii - Long head (FJ1479)
        # Origin: Infraglenoid tubercle of scapula
        # Insertion: Olecranon of ulna
        self._muscles["FJ1479"] = MuscleDeformationBindingEntry(
            anatomy_id="FJ1479",
            muscle_name_en="Triceps brachii (Long head)",
            muscle_name_vi="Cơ tam đầu cánh tay (Đầu dài)",
            source_mesh_id="Triceps_brachii_long_R",
            source_mesh_file="Triceps_brachii_long_R.obj",
            source_hash=self._file_hash("Triceps_brachii_long_R.obj"),
            canonical_origin_bone="upperarm_r",
            canonical_insertion_bone="lowerarm_r",
            origin_landmark_m=(-0.180, 0.490, -0.060),
            insertion_landmark_m=(-0.335, 0.320, -0.060),
            resting_length_m=0.245,
            flexed_length_90_m=0.294,
            expected_contraction_90=1.200,  # ~20% stretch
            deformation_strategy=DeformationStrategy.DUAL_BONE_SKINNING_AND_BULGE,
            laterality=Laterality.RIGHT,
        )

        # 5. Triceps brachii - Medial head (FJ1480)
        # Origin: Posterior humerus distal to radial groove
        # Insertion: Olecranon of ulna
        self._muscles["FJ1480"] = MuscleDeformationBindingEntry(
            anatomy_id="FJ1480",
            muscle_name_en="Triceps brachii (Medial head)",
            muscle_name_vi="Cơ tam đầu cánh tay (Đầu trong)",
            source_mesh_id="Triceps_brachii_medial_R",
            source_mesh_file="Triceps_brachii_medial_R.obj",
            source_hash=self._file_hash("Triceps_brachii_medial_R.obj"),
            canonical_origin_bone="upperarm_r",
            canonical_insertion_bone="lowerarm_r",
            origin_landmark_m=(-0.210, 0.400, -0.045),
            insertion_landmark_m=(-0.335, 0.320, -0.055),
            resting_length_m=0.185,
            flexed_length_90_m=0.222,
            expected_contraction_90=1.200,
            deformation_strategy=DeformationStrategy.DUAL_BONE_SKINNING_AND_BULGE,
            laterality=Laterality.RIGHT,
        )

        # 6. Brachialis (FJ1486)
        # Origin: Anterior lower half of humerus
        # Insertion: Coronoid process and tuberosity of ulna
        self._muscles["FJ1486"] = MuscleDeformationBindingEntry(
            anatomy_id="FJ1486",
            muscle_name_en="Brachialis",
            muscle_name_vi="Cơ cánh tay",
            source_mesh_id="Brachialis_R",
            source_mesh_file="Brachialis_R.obj",
            source_hash=self._file_hash("Brachialis_R.obj"),
            canonical_origin_bone="upperarm_r",
            canonical_insertion_bone="lowerarm_r",
            origin_landmark_m=(-0.220, 0.410, -0.015),
            insertion_landmark_m=(-0.335, 0.315, -0.010),
            resting_length_m=0.160,
            flexed_length_90_m=0.125,
            expected_contraction_90=0.781,  # ~21.9% shortening
            deformation_strategy=DeformationStrategy.DUAL_BONE_SKINNING_AND_BULGE,
            laterality=Laterality.RIGHT,
        )

    def get_muscle(self, anatomy_id: str) -> Optional[MuscleDeformationBindingEntry]:
        return self._muscles.get(anatomy_id)

    def list_muscles(self) -> List[Dict[str, Any]]:
        return [asdict(m) for m in self._muscles.values()]

    def evaluate_all_muscles(self, elbow_flexion_deg: float) -> List[Dict[str, Any]]:
        """Evaluates states of all registered muscles at given elbow flexion."""
        results = []
        for m in self._muscles.values():
            st = m.evaluate_state(elbow_flexion_deg)
            results.append(asdict(st))
        return results


muscle_deformation_adapter = MuscleDeformationAdapter()
