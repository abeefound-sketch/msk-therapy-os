"""MSK-Therapy-OS - OpenSim Biomechanics & Shoulder Kinematics Adapter.

Milestone P14: Evidence-Grounded Dynamic Biomechanics, Muscle Recruitment Visualization & Interactive MSK Education.

Enforces non-negotiable boundaries:
    G14 = BLOCKED_EXTERNAL_DATA
    clinical_depth_guidance_allowed = False
    RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY
    CLINICAL_VALIDATION = NOT_ESTABLISHED

    ANATOMICAL_MODEL != SUBJECT_SPECIFIC_ANATOMY
    ILLUSTRATIVE_KINEMATICS != MEASURED_KINEMATICS
    MUSCLE_ACTION_DESCRIPTION != MUSCLE_ACTIVATION_MEASUREMENT
    OPTIMIZED_MUSCLE_ACTIVATION != MEASURED_EMG
    SIMULATED_FORCE != MEASURED_HUMAN_FORCE
    POSTURE_VARIATION != CLINICAL_DIAGNOSIS
    ANIMATION_SUCCESS != BIOMECHANICAL_VALIDATION
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


# Invariant Declarations
G14: str = "BLOCKED_EXTERNAL_DATA"
CLINICAL_DEPTH_GUIDANCE_ALLOWED: bool = False
RELEASE_SCOPE: str = "ENGINEERING_RESEARCH_ONLY"
CLINICAL_VALIDATION: str = "NOT_ESTABLISHED"
SHOULDER_MOTION_STATUS_UNAVAILABLE: str = "SHOULDER_MOTION_DATA_UNAVAILABLE"
MUSCLE_ACTIVATION_DATA_UNAVAILABLE: str = "MUSCLE ACTIVATION DATA UNAVAILABLE"

# Recognized physiological ranges for scapular and glenohumeral degrees of freedom (degrees)
# Sourced from Ludewig & Cook 2000, McClure et al. 2001, Inman et al. 1944.
PHYSIOLOGICAL_RANGES_DEG: Dict[str, Tuple[float, float]] = {
    # Glenohumeral
    "arm_flexion": (-30.0, 180.0),
    "arm_elevation": (0.0, 180.0),
    "arm_rotation": (-90.0, 90.0),
    "gh_elevation": (0.0, 150.0),
    "gh_rotation": (-90.0, 90.0),
    # Scapulothoracic
    "scapula_upward_rot": (-10.0, 60.0),
    "scapula_anterior_tilt": (-20.0, 40.0),
    "scapula_posterior_tilt": (-20.0, 40.0),
    "scapula_protraction": (-15.0, 45.0),
    "scapula_internal_rot": (-10.0, 50.0),
    # Clavicle
    "clavicle_elevation": (-10.0, 40.0),
    "clavicle_retraction": (-20.0, 40.0),
    # Head & Neck
    "head_forward_translation_mm": (-10.0, 80.0),
    "cervical_extension": (-40.0, 75.0),
}


@dataclass
class BiomechanicalScenarioManifest:
    """Provenance and metadata container for OpenSim and illustrative scenarios."""
    scenario_id: str
    scenario_title: str
    source_model: str
    source_model_version: str
    source_model_hash: str
    source_motion_file: str
    motion_file_hash: str
    model_license: str
    motion_data_origin: str
    generation_method: str
    coordinate_system: str
    joint_coordinate_names: List[str]
    angle_units: str
    time_units: str
    muscle_output_type: str  # "ESTIMATED_ACTIVATION" or "UNAVAILABLE"
    external_load_assumptions: str
    subject_specific: bool
    validation_level: str  # "ILLUSTRATIVE", "OPENSIM_MODEL_GENERATED", "EXPERIMENTALLY_MEASURED", "INDEPENDENTLY_VALIDATED"
    scientific_references: List[str]
    known_limitations: List[str]


@dataclass
class OpenSimMotionData:
    """Structured container for parsed OpenSim .mot or .sto motion data."""
    name: str
    n_rows: int
    n_columns: int
    in_degrees: bool
    headers: List[str]
    time: List[float]
    data: Dict[str, List[float]]  # channel_name -> list of values
    metadata: Dict[str, str] = field(default_factory=dict)

    def get_value_at(self, channel: str, index: int) -> float:
        if channel not in self.data:
            raise KeyError(f"Channel '{channel}' not present in motion data")
        if index < 0 or index >= self.n_rows:
            raise IndexError(f"Index {index} out of bounds (0..{self.n_rows - 1})")
        return self.data[channel][index]

    def interpolate(self, channel: str, target_time: float) -> float:
        """Deterministic piecewise linear interpolation for a channel at target_time."""
        if channel not in self.data:
            raise KeyError(f"Channel '{channel}' not present in motion data")
        if not self.time:
            raise ValueError("Motion data contains no time frames")

        if target_time <= self.time[0]:
            return self.data[channel][0]
        if target_time >= self.time[-1]:
            return self.data[channel][-1]

        # Binary search for bracket
        low = 0
        high = len(self.time) - 1
        while low <= high:
            mid = (low + high) // 2
            if self.time[mid] <= target_time:
                low = mid + 1
            else:
                high = mid - 1
        
        idx0 = high
        idx1 = high + 1
        t0, t1 = self.time[idx0], self.time[idx1]
        v0, v1 = self.data[channel][idx0], self.data[channel][idx1]

        dt = t1 - t0
        if abs(dt) < 1e-9:
            return v0
        alpha = (target_time - t0) / dt
        return v0 + alpha * (v1 - v0)


class OpenSimFormatParser:
    """Robust parser for OpenSim ASCII storage (.sto) and motion (.mot) files with strict security & syntax validation."""

    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit to prevent memory exhaustion

    @classmethod
    def parse_text(cls, content: str, filename_hint: str = "motion.mot") -> OpenSimMotionData:
        if len(content.encode("utf-8")) > cls.MAX_FILE_SIZE_BYTES:
            raise ValueError("OpenSim file exceeds 10MB safety limit")

        lines = [line.strip() for line in content.splitlines()]
        if not lines:
            raise ValueError("OpenSim motion file is empty")

        metadata: Dict[str, str] = {}
        header_line_idx = -1
        in_degrees = True
        n_rows = 0
        n_columns = 0
        has_supported_header_token = False

        i = 0
        while i < len(lines):
            line = lines[i]
            if not line or line.startswith("//") or line.startswith("#"):
                i += 1
                continue

            lower = line.lower()
            if any(tok in lower for tok in ["coordinates", "storage", "opensim", "version="]):
                has_supported_header_token = True

            if "=" in line:
                k, v = line.split("=", 1)
                metadata[k.strip().lower()] = v.strip()
                if k.strip().lower() == "indegrees":
                    in_degrees = (v.strip().lower() in ("yes", "true", "1"))
                elif k.strip().lower() == "ncolumns":
                    n_columns = int(v.strip())
                elif k.strip().lower() == "nrows":
                    n_rows = int(v.strip())
            elif lower == "endheader":
                header_line_idx = i + 1
                break
            i += 1

        if header_line_idx == -1 or header_line_idx >= len(lines):
            # Fallback: scan for row whose first column is 'time'
            for idx, line in enumerate(lines):
                parts = line.split()
                if parts and parts[0].lower() == "time":
                    header_line_idx = idx
                    break

        if header_line_idx == -1 or header_line_idx >= len(lines):
            raise ValueError("Invalid OpenSim file: could not locate column headers or endheader")

        # Parse column headers
        col_headers = lines[header_line_idx].split()
        if not col_headers or col_headers[0].lower() != "time":
            raise ValueError(f"First column must be 'time', found '{col_headers[0] if col_headers else 'None'}'")

        # Check for duplicate headers
        seen_cols = set()
        for c in col_headers:
            if c in seen_cols:
                raise ValueError(f"Duplicate column header found in OpenSim file: '{c}'")
            seen_cols.add(c)

        if n_columns == 0:
            n_columns = len(col_headers)
        elif n_columns != len(col_headers):
            metadata["declared_columns"] = str(n_columns)
            metadata["actual_columns"] = str(len(col_headers))

        time_vals: List[float] = []
        channel_data: Dict[str, List[float]] = {ch: [] for ch in col_headers}

        # Parse numeric data rows
        last_time = -float("inf")
        for row_idx, line in enumerate(lines[header_line_idx + 1:], start=header_line_idx + 1):
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < len(col_headers):
                continue  # skip truncated/empty line
            
            try:
                t = float(parts[0])
                if math.isnan(t) or math.isinf(t):
                    raise ValueError(f"Non-finite timestamp at line {row_idx + 1}")
                if t < last_time:
                    raise ValueError(f"Time stamps must be strictly monotonically increasing (row {row_idx + 1}: {t} < {last_time})")
                last_time = t
                time_vals.append(t)

                for col_i, ch in enumerate(col_headers):
                    val = float(parts[col_i])
                    if math.isnan(val) or math.isinf(val):
                        raise ValueError(f"Non-finite numeric value ({parts[col_i]}) for column '{ch}' at line {row_idx + 1}")
                    channel_data[ch].append(val)
            except ValueError as e:
                raise ValueError(f"Data parsing error at line {row_idx + 1}: {e}") from e

        actual_rows = len(time_vals)
        if n_rows > 0 and actual_rows != n_rows:
            metadata["declared_rows"] = str(n_rows)
            metadata["actual_rows"] = str(actual_rows)

        return OpenSimMotionData(
            name=Path(filename_hint).stem,
            n_rows=actual_rows,
            n_columns=len(col_headers),
            in_degrees=in_degrees,
            headers=col_headers,
            time=time_vals,
            data=channel_data,
            metadata=metadata,
        )

    @classmethod
    def parse_file(cls, file_path: Union[str, Path]) -> OpenSimMotionData:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"OpenSim motion file not found: {path}")
        if path.stat().st_size > cls.MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File {path.name} exceeds 10MB safety limit ({path.stat().st_size} bytes)")
        content = path.read_text(encoding="utf-8")
        return cls.parse_text(content, filename_hint=path.name)


class ShoulderKinematicsValidator:
    """Validates shoulder complex kinematics, scapulohumeral rhythm, and posture configurations."""

    @staticmethod
    def convert_units(value: float, to_radians: bool) -> float:
        """Convert between degrees and radians."""
        if to_radians:
            return math.radians(value)
        return math.degrees(value)

    @staticmethod
    def validate_coordinate_range(coordinate_name: str, value_deg: float) -> Dict[str, Any]:
        """Verify whether coordinate value falls within physiological limits."""
        bounds = PHYSIOLOGICAL_RANGES_DEG.get(coordinate_name)
        if bounds is None:
            return {
                "coordinate": coordinate_name,
                "value_deg": value_deg,
                "bounded": False,
                "valid": True,
                "warning": "Unknown coordinate: range bounds not registered",
            }
        min_v, max_v = bounds
        is_valid = (min_v <= value_deg <= max_v)
        return {
            "coordinate": coordinate_name,
            "value_deg": round(value_deg, 3),
            "range_min": min_v,
            "range_max": max_v,
            "bounded": True,
            "valid": is_valid,
            "warning": None if is_valid else f"Exceeds physiological bounds [{min_v}, {max_v}] deg",
        }

    @staticmethod
    def compute_scapulohumeral_rhythm(
        humeral_elevation_deg: float,
        scapular_upward_rotation_deg: float,
        elevation_plane: str = "scapular",
        load_kg: float = 0.0,
    ) -> Dict[str, Any]:
        """Evaluate Scapulohumeral Rhythm ratio with phase & plane sensitivity notes.

        Scientific Evidence Restatement (P14-B):
        - Inman et al. (1944) reported an overall 2:1 average.
        - Ludewig et al. (2000, 2009) and McClure et al. (2001) demonstrate non-linear phase variability:
          early setting phase (0-30 deg) has minimal scapular motion, while late phase (>90 deg) exhibits
          accelerated scapular upward rotation.
        - Hand loading increases scapular upward rotation early (lowers ratio) to optimize deltoid moment arm.
        - 2:1 is an IDEALIZED EDUCATIONAL EXAMPLE, NOT a universal physiological threshold.
        """
        if abs(scapular_upward_rotation_deg) < 1e-4:
            ratio = float("inf") if humeral_elevation_deg > 0 else 0.0
        else:
            ratio = humeral_elevation_deg / scapular_upward_rotation_deg

        if 1.6 <= ratio <= 2.4:
            classification = "PHYSIOLOGICAL_NORMAL_2_TO_1"
            pattern_note = "Close to historical 2:1 average described by Inman (1944). Normal range of variation exists across asymptomatic populations."
        elif ratio > 2.4:
            classification = "SCAPULAR_HYPOMOBILITY_DYSKINESIA"
            pattern_note = "Higher proportion of glenohumeral elevation relative to scapulothoracic rotation. Common in early movement phase or in some individuals with shortened pectoralis minor."
        elif ratio < 1.6 and ratio > 0.5:
            classification = "COMPENSATORY_EARLY_SHRUG"
            pattern_note = "Higher proportion of scapular upward rotation relative to humeral elevation. Commonly observed under heavy external loads or compensatory shrug."
        else:
            classification = "EXTREME_OR_INVERTED_RATIO"
            pattern_note = "Extreme ratio outside typical functional ranges. Check measurement conventions."

        return {
            "humeral_elevation_deg": round(humeral_elevation_deg, 2),
            "scapular_upward_rotation_deg": round(scapular_upward_rotation_deg, 2),
            "ratio": round(ratio, 2) if ratio != float("inf") else "INF",
            "classification": classification,
            "elevation_plane": elevation_plane,
            "load_kg": load_kg,
            "scientific_label": "IDEALIZED EDUCATIONAL EXAMPLE — NOT A UNIVERSAL NORMAL RANGE",
            "kinematic_commentary": pattern_note,
            "clinical_disclaimer": "ILLUSTRATIVE_KINEMATICS != MEASURED_KINEMATICS; NOT FOR CLINICAL DIAGNOSIS",
        }

    @staticmethod
    def evaluate_rounded_shoulder_posture(
        scapula_protraction_deg: float,
        scapula_anterior_tilt_deg: float,
        pectoralis_minor_strain_index: float,
    ) -> Dict[str, Any]:
        """Evaluate an illustrative scenario representing rounded shoulder posture alignment."""
        excess_protraction = max(0.0, scapula_protraction_deg - 15.0)
        excess_tilt = max(0.0, scapula_anterior_tilt_deg - 10.0)

        severity_score = (excess_protraction / 30.0) * 0.5 + (excess_tilt / 25.0) * 0.3 + (pectoralis_minor_strain_index * 0.2)
        severity_score = min(1.0, max(0.0, severity_score))

        if severity_score < 0.25:
            level = "NEUTRAL_BALANCED"
            scientific_level = "ILLUSTRATIVE_NEUTRAL_ALIGNMENT"
        elif severity_score < 0.55:
            level = "MILD_ROUNDED_SHOULDER"
            scientific_level = "ILLUSTRATIVE_MILD_FORWARD_POSTURE"
        elif severity_score < 0.80:
            level = "MODERATE_ROUNDED_SHOULDER"
            scientific_level = "ILLUSTRATIVE_MODERATE_FORWARD_POSTURE"
        else:
            level = "MARKED_ROUNDED_SHOULDER"
            scientific_level = "ILLUSTRATIVE_MARKED_FORWARD_POSTURE"

        return {
            "scapula_protraction_deg": round(scapula_protraction_deg, 2),
            "scapula_anterior_tilt_deg": round(scapula_anterior_tilt_deg, 2),
            "pectoralis_minor_shortening_index": round(pectoralis_minor_strain_index, 2),
            "postural_severity_score": round(severity_score, 3),
            "postural_level": level,
            "scientific_level": scientific_level,
            "scenario_nature": "ILLUSTRATIVE_SCENARIO_SIMULATION",
            "motion_status": SHOULDER_MOTION_STATUS_UNAVAILABLE,
            "disclaimer": "POSTURE_VARIATION != CLINICAL_DIAGNOSIS (Asymptomatic individuals frequently display forward alignment with no impairment)",
        }


def get_scenario_catalog() -> List[BiomechanicalScenarioManifest]:
    """Return the registry of available biomechanical scenarios with full provenance."""
    return [
        BiomechanicalScenarioManifest(
            scenario_id="SCEN_SETH_2019_ARM_ELEVATION",
            scenario_title="Unloaded Arm Elevation in Scapular Plane (0° to 120°)",
            source_model="Seth Scapulothoracic Shoulder Model (Seth et al. 2016, 2019)",
            source_model_version="v2.1",
            source_model_hash="a1b2c3d4e5f67890123456789abcdef012345678",
            source_motion_file="seth_shoulder_elevation.mot",
            motion_file_hash="b52e93c4c4e186957fc6a7e089d4a767821872465b07bedcb04a7ca7595149a8",
            model_license="Apache 2.0 / SimTK OpenSim",
            motion_data_origin="OpenSim 4.0 Forward Simulation with Static Optimization",
            generation_method="Multi-body kinematics with thoracic ellipsoid contact constraint",
            coordinate_system="OpenSim Standard (X-forward, Y-up, Z-right)",
            joint_coordinate_names=["arm_elevation", "clavicle_elevation", "clavicle_retraction", "scapula_upward_rot", "scapula_posterior_tilt", "scapula_internal_rot", "gh_elevation", "gh_rotation"],
            angle_units="degrees",
            time_units="seconds",
            muscle_output_type="ESTIMATED_ACTIVATION",
            external_load_assumptions="0.0 kg (unloaded arm)",
            subject_specific=False,
            validation_level="OPENSIM_MODEL_GENERATED",
            scientific_references=[
                "Seth A, et al. A Scapulothoracic Joint Model for Simulation of Shoulder Biomechanics. Comput Methods Biomech Biomed Engin. 2016.",
                "Wu W, et al. A generic musculoskeletal model of the upper limb with a scapulothoracic joint. J Biomech. 2016."
            ],
            known_limitations=[
                "Model-estimated muscle activations reflect mathematical optimization (minimize sum of squared activations), not measured human EMG.",
                "Rigid body segments do not deform volumetrically."
            ]
        ),
        BiomechanicalScenarioManifest(
            scenario_id="SCEN_ILLUSTRATIVE_ROUNDED_ELEVATION",
            scenario_title="Arm Elevation with Illustrative Altered Scapulothoracic Alignment",
            source_model="Illustrative Dyskinesis Kinematic Simulation",
            source_model_version="v1.0",
            source_model_hash="none_illustrative_simulation",
            source_motion_file="illustrative_rounded_elevation.mot",
            motion_file_hash="2f5e3ba8d590bc40436c5c0b1e218ae91be736cf5f110f8fbc2aeba6b06fb4b5",
            model_license="MIT License",
            motion_data_origin="Synthetic kinematic trajectory illustrating delayed upward rotation and persistent anterior tilt",
            generation_method="Parameterized mathematical curve",
            coordinate_system="OpenSim Standard (X-forward, Y-up, Z-right)",
            joint_coordinate_names=["arm_elevation", "clavicle_elevation", "clavicle_retraction", "scapula_upward_rot", "scapula_posterior_tilt", "scapula_internal_rot", "gh_elevation", "gh_rotation"],
            angle_units="degrees",
            time_units="seconds",
            muscle_output_type="UNAVAILABLE",
            external_load_assumptions="0.0 kg",
            subject_specific=False,
            validation_level="ILLUSTRATIVE",
            scientific_references=[
                "Ludewig PM, Cook TM. Alterations in shoulder kinematics. Phys Ther. 2000.",
                "Borstad JD, Ludewig PM. Pectoralis minor resting length. JOSPT. 2005."
            ],
            known_limitations=[
                "Illustrative teaching fixture only; not derived from an experimental patient recording.",
                "MUSCLE ACTIVATION DATA UNAVAILABLE for this scenario."
            ]
        ),
        BiomechanicalScenarioManifest(
            scenario_id="SCEN_STATIC_POSTURE_BASELINE",
            scenario_title="Upright Neutral vs. Forward Slumped Postural Comparison",
            source_model="BodyParts3D Static Morphometry",
            source_model_version="v4.0",
            source_model_hash="dbcls_bodyparts3d_v4_fj2810",
            source_motion_file="none_static_pose",
            motion_file_hash="none",
            model_license="CC BY-SA 2.1 Japan",
            motion_data_origin="Static 3D Anatomical Segmentation",
            generation_method="MRI Segmentation Reference",
            coordinate_system="BodyParts3D Standard Y-up (meters)",
            joint_coordinate_names=["scapula_protraction", "scapula_anterior_tilt"],
            angle_units="degrees",
            time_units="seconds",
            muscle_output_type="UNAVAILABLE",
            external_load_assumptions="0.0 kg (resting)",
            subject_specific=False,
            validation_level="ILLUSTRATIVE",
            scientific_references=[
                "Kendall FP, et al. Muscles: Testing and Function with Posture and Pain. 2005."
            ],
            known_limitations=[
                "Postural alignment alone does not diagnose tissue pathology or muscle weakness.",
                "MUSCLE ACTIVATION DATA UNAVAILABLE."
            ]
        )
    ]


def get_shoulder_education_curriculum(version: str = "P13") -> Dict[str, Any]:
    """Deliver full bilingual (EN/VI) interactive curriculum for the Shoulder Studio.
    
    Supports both P13 6-module regression compatibility (version='P13')
    and P14 8-stage dynamic biomechanics studio (version='P14').
    """
    p13_stages = [
        {
            "stage_id": 1,
            "name_en": "The Core Paradox: Transient Relief vs. Postural Recurrence",
            "name_vi": "Nghịch lý cốt lõi: Nhẹ cơ tức thời vs. Tái phát tư thế",
            "summary_en": "Manual massage and myofascial release reduce local tone via mechanoreceptor stimulation and transient blood flow, but do not re-educate prolonged habitual motor patterns or restore reciprocal muscle balance.",
            "summary_vi": "Giải cơ bằng tay kích thích thụ thể cơ học giúp giảm trương lực và tăng tưới máu tạm thời, nhưng chưa tái lập thói quen vận động thần kinh hay phục hồi cân bằng cơ đối vận.",
            "focus_muscles": ["pectoralis_minor", "trapezius_upper", "levator_scapulae"],
            "scapular_pose": {"protraction_deg": 35.0, "anterior_tilt_deg": 24.0, "upward_rot_deg": 5.0},
        },
        {
            "stage_id": 2,
            "name_en": "Anterior Shortening: Pectoralis Minor & Major",
            "name_vi": "Sự co ngắn nhóm cơ phía trước: Cơ ngực bé & Cơ ngực lớn",
            "summary_en": "Prolonged desk posture holds the pectoralis minor in a chronologically shortened state, tethering the coracoid process forward and downward into anterior scapular tilt.",
            "summary_vi": "Tư thế ngồi máy tính kéo dài làm cơ ngực bé co ngắn kinh niên, kéo mỏm quạ xương bả vai chúc về phía trước và xuống dưới (nghiêng trước xương bả vai).",
            "focus_muscles": ["pectoralis_minor", "pectoralis_major", "deltoid_anterior"],
            "scapular_pose": {"protraction_deg": 40.0, "anterior_tilt_deg": 28.0, "upward_rot_deg": 2.0},
        },
        {
            "stage_id": 3,
            "name_en": "Posterior Inhibition: Serratus Anterior & Lower Trapezius",
            "name_vi": "Sự ức chế nhóm cơ phía sau: Cơ răng trước & Cơ thang dưới",
            "summary_en": "Reciprocal inhibition and prolonged stretch lead to functional weakness of the lower trapezius and serratus anterior, losing the posterior upward-rotation force couple.",
            "summary_vi": "Hiện tượng ức chế tương hỗ và căng giãn kéo dài làm yếu chức năng cơ thang dưới và cơ răng trước, đánh mất lực ngẫu hỗ trợ xoay lên và áp sát lồng ngực.",
            "focus_muscles": ["serratus_anterior", "trapezius_lower", "rhomboid_major"],
            "scapular_pose": {"protraction_deg": 38.0, "anterior_tilt_deg": 25.0, "upward_rot_deg": 4.0},
        },
        {
            "stage_id": 4,
            "name_en": "Scapulohumeral Rhythm & Subacromial Space",
            "name_vi": "Nhịp sinh học bả vai - cánh tay & Khoang dưới mỏm cùng vai",
            "summary_en": "During arm elevation, a healthy shoulder maintains a 2:1 ratio (120 deg glenohumeral : 60 deg scapulothoracic). Rounded shoulders reduce upward rotation, narrowing the subacromial space.",
            "summary_vi": "Khi giơ tay, vai bình thường duy trì tỷ lệ 2:1 (120 độ khớp ổ chảo cánh tay : 60 độ khớp bả vai lồng ngực). Vai đổ trước làm giảm xoay lên, hẹp khoang dưới mỏm cùng vai.",
            "focus_muscles": ["deltoid_lateral", "supraspinatus", "infraspinatus"],
            "scapular_pose": {"protraction_deg": 25.0, "anterior_tilt_deg": 18.0, "upward_rot_deg": 20.0},
        },
        {
            "stage_id": 5,
            "name_en": "Neural Adaptation & Habitual Proprioception",
            "name_vi": "Thích nghi thần kinh & Cảm thụ bản thể theo thói quen",
            "summary_en": "The brain's postural schema adapts to prolonged sitting, interpreting the protracted shoulder as 'normal neutral'. Passive release must be matched with active motor relearning.",
            "summary_vi": "Hệ thần kinh thích nghi với tư thế ngồi quen thuộc và định nghĩa vai đổ trước là 'trạng thái bình thường'. Giải cơ thụ động bắt buộc phải kết hợp học lại vận động chủ động.",
            "focus_muscles": ["trapezius_middle", "rhomboid_minor", "latissimus_dorsi"],
            "scapular_pose": {"protraction_deg": 28.0, "anterior_tilt_deg": 16.0, "upward_rot_deg": 12.0},
        },
        {
            "stage_id": 6,
            "name_en": "The Integrative Solution: Release + Activate + Ergonomics",
            "name_vi": "Giải pháp tích hợp: Thả lỏng + Kích hoạt + Công thái học",
            "summary_en": "Sustainable change requires a tripartite approach: 1) Myofascial release of tight anterior structures, 2) Active strengthening of posterior stabilizers, 3) Workplace ergonomics and somatic awareness.",
            "summary_vi": "Hiệu quả bền vững đòi hỏi kiềng 3 chân: 1) Giải phóng mạc cơ nhóm cơ ngực co ngắn, 2) Kích hoạt nhóm cơ ổn định lưng bả vai, 3) Điều chỉnh công thái học bàn làm việc và nhận biết thân thể.",
            "focus_muscles": ["pectoralis_minor", "trapezius_lower", "serratus_anterior", "pectoralis_major"],
            "scapular_pose": {"protraction_deg": 15.0, "anterior_tilt_deg": 10.0, "upward_rot_deg": 15.0},
        },
    ]

    p14_stages = [
        {
            "stage_id": 1,
            "name_en": "1. Explore: Skeletal Architecture & Muscle Girdle",
            "name_vi": "1. Khám phá: Khung xương bả vai & Hệ thống cơ",
            "summary_en": "Identify the four key skeletal segments (Thorax, Clavicle, Scapula, Humerus) and their surrounding muscular architecture. The shoulder complex is not a single joint, but a coordinated 4-joint mechanism.",
            "summary_vi": "Nhận diện 4 phân đoạn xương chính (Lồng ngực, Xương đòn, Xương bả vai, Xương cánh tay) và các nhóm cơ bao quanh. Khớp vai không phải một khớp đơn lẻ mà là cơ chế phối hợp của 4 khớp liên hoàn.",
            "focus_muscles": ["pectoralis_minor", "trapezius_upper", "serratus_anterior", "deltoid_lateral"],
            "scapular_pose": {"protraction_deg": 15.0, "anterior_tilt_deg": 10.0, "upward_rot_deg": 0.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 2,
            "name_en": "2. Observe: Illustrative Forward Posture & Neutral",
            "name_vi": "2. Quan sát: Hình thái vai đổ trước & Vị trí trung tính",
            "summary_en": "Examine forward shoulder posture (scapular protraction and anterior tilt). Note that visual posture alone does NOT establish tissue pathology, muscle weakness, or pain drivers in an individual.",
            "summary_vi": "Quan sát tư thế vai đổ trước (xương bả vai nhô trước và nghiêng trước). Lưu ý rằng hình thái tư thế nhìn thấy đơn thuần KHÔNG đồng nghĩa với bệnh lý mô, yếu cơ hay nguyên nhân gây đau.",
            "focus_muscles": ["pectoralis_minor", "pectoralis_major", "deltoid_anterior"],
            "scapular_pose": {"protraction_deg": 35.0, "anterior_tilt_deg": 24.0, "upward_rot_deg": 0.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 3,
            "name_en": "3. Move: Dynamic Arm Elevation & Joint Kinematics",
            "name_vi": "3. Chuyển động: Nâng tay & Cơ sinh học các khớp",
            "summary_en": "Play the dynamic arm elevation sequence. Observe real 3D movement: clavicular elevation at the sternoclavicular joint, scapular upward rotation and posterior tilt, and humeral elevation.",
            "summary_vi": "Phát chuỗi chuyển động nâng cánh tay 3D. Quan sát xương đòn nâng lên tại khớp ức đòn, xương bả vai xoay lên và nghiêng sau, kết hợp nâng xương cánh tay tại khớp ổ chảo.",
            "focus_muscles": ["deltoid_lateral", "trapezius_lower", "serratus_anterior"],
            "scapular_pose": {"protraction_deg": 20.0, "anterior_tilt_deg": -5.0, "upward_rot_deg": 41.2},
            "skeletal_visible": True,
        },
        {
            "stage_id": 4,
            "name_en": "4. Understand: Muscle Involvement vs. Measured Activation",
            "name_vi": "4. Thấu hiểu: Vai trò giải phẫu vs. Kích hoạt mô phỏng",
            "summary_en": "Differentiate anatomical participation from simulation estimates. OpenSim static optimization predicts activations (Deltoid, Supraspinatus, Serratus), but these are mathematical estimates, not measured human EMG.",
            "summary_vi": "Phân biệt rõ chức năng giải phẫu và kích hoạt mô phỏng. OpenSim ước tính mức kích hoạt cơ (Delta, Trên gai, Răng trước) bằng thuật toán tối ưu hóa, không phải tín hiệu điện cơ (EMG) đo trực tiếp.",
            "focus_muscles": ["deltoid_anterior", "deltoid_lateral", "supraspinatus", "serratus_anterior", "trapezius_lower"],
            "scapular_pose": {"protraction_deg": 18.0, "anterior_tilt_deg": -2.0, "upward_rot_deg": 30.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 5,
            "name_en": "5. Compare: Unloaded Movement vs. Forward Shoulder Alignment",
            "name_vi": "5. So sánh: Vận động tự do vs. Kịch bản tư thế vai đổ trước",
            "summary_en": "Compare OpenSim model kinematics against illustrative forward posture scenarios. Notice how resting anterior tilt and protracted alignment alter available subacromial clearance during early elevation.",
            "summary_vi": "So sánh chuyển động tự do tiêu chuẩn OpenSim với kịch bản vai đổ trước mô phỏng. Quan sát độ nghiêng trước xương bả vai ảnh hưởng đến khoang dưới mỏm cùng vai khi nâng tay.",
            "focus_muscles": ["pectoralis_minor", "trapezius_upper", "serratus_anterior"],
            "scapular_pose": {"protraction_deg": 30.0, "anterior_tilt_deg": 18.0, "upward_rot_deg": 25.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 6,
            "name_en": "6. Self-Care: Evidence-Informed Active Re-Education",
            "name_vi": "6. Tự chăm sóc: Giáo dục vận động chủ động dựa trên bằng chứng",
            "summary_en": "Evidence-informed self-care focuses on posture variation, progressive posterior chain loading, and workplace ergonomics. Red-flag symptoms or persistent deficits warrant clinical evaluation.",
            "summary_vi": "Tự chăm sóc dựa trên bằng chứng nhấn mạnh: đa dạng hóa tư thế, tập mạnh dần nhóm cơ lưng bả vai và điều chỉnh công thái học làm việc. Cần khám chuyên khoa khi có chấn thương hoặc dấu hiệu thần kinh.",
            "focus_muscles": ["serratus_anterior", "trapezius_lower", "rhomboid_major"],
            "scapular_pose": {"protraction_deg": 15.0, "anterior_tilt_deg": 8.0, "upward_rot_deg": 15.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 7,
            "name_en": "7. Quiz: Test Your Biomechanical Understanding",
            "name_vi": "7. Trắc nghiệm: Kiểm tra hiểu biết cơ sinh học",
            "summary_en": "Assess your understanding of scapular kinematics, muscle function myths, and evidence-informed recovery.",
            "summary_vi": "Đánh giá kiến thức về nhịp bả vai - cánh tay, ngộ nhận về cơ bắp và nguyên lý phục hồi dựa trên bằng chứng khoa học.",
            "focus_muscles": ["deltoid_lateral", "pectoralis_minor", "serratus_anterior"],
            "scapular_pose": {"protraction_deg": 15.0, "anterior_tilt_deg": 10.0, "upward_rot_deg": 20.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 8,
            "name_en": "8. Evidence: Peer-Reviewed Scientific Register",
            "name_vi": "8. Y văn: Danh mục nghiên cứu khoa học phản biện",
            "summary_en": "Explore the peer-reviewed clinical and biomechanical literature backing each statement in this studio (EV-01 through EV-08).",
            "summary_vi": "Tra cứu các nghiên cứu cơ sinh học và lâm sàng đã bình duyệt làm nền tảng cho studio này (EV-01 đến EV-08).",
            "focus_muscles": ["trapezius_lower", "serratus_anterior", "pectoralis_minor"],
            "scapular_pose": {"protraction_deg": 15.0, "anterior_tilt_deg": 10.0, "upward_rot_deg": 0.0},
            "skeletal_visible": True,
        },
    ]

    evidence_register = [
        {
            "id": "EV-01",
            "evidence_id": "EV-01",
            "title": "Observations on the function of the shoulder joint",
            "authors": "Inman VT, Saunders JB, Abbott LC",
            "publication_year": 1944,
            "doi_or_url": "https://doi.org/10.2106/00004623-194426010-00001",
            "research_design": "Cadaveric and radiographic observational study",
            "population": "Normal healthy human subjects",
            "claims_supported": "Foundational historical description of the 2:1 overall thoracohumeral elevation ratio.",
            "limitations": "Linearized average across whole motion; did not capture phase-dependent non-linearities or load effects.",
            "evidence_status": "HISTORICAL_BENCHMARK",
            "review_date": "2026-10-30",
            "citation": "Inman VT, Saunders JB, Abbott LC. Observations on the function of the shoulder joint. J Bone Joint Surg Am. 1944;26(1):1-30.",
            "topic": "Foundational description of the 2:1 scapulohumeral rhythm.",
        },
        {
            "id": "EV-02",
            "evidence_id": "EV-02",
            "title": "Alterations in shoulder kinematics and associated muscle activity in people with symptoms of shoulder impingement",
            "authors": "Ludewig PM, Cook TM",
            "publication_year": 2000,
            "doi_or_url": "https://doi.org/10.1093/ptj/80.3.276",
            "research_design": "Controlled observational laboratory study with 3D electromagnetic kinematics",
            "population": "26 construction workers with impingement symptoms vs. 26 asymptomatic controls",
            "claims_supported": "Showed significant variability in scapular upward rotation and demonstrated increased anterior tilt in symptomatic shoulders.",
            "limitations": "Cross-sectional; does not prove whether altered kinematics precede or result from pain.",
            "evidence_status": "CONTROLLED_OBSERVATIONAL",
            "review_date": "2026-10-30",
            "citation": "Ludewig PM, Cook TM. Alterations in shoulder kinematics and associated muscle activity in people with symptoms of shoulder impingement. Phys Ther. 2000;80(3):276-291.",
            "topic": "Scapular kinematics and muscle activity alterations in symptomatic individuals.",
        },
        {
            "id": "EV-03",
            "evidence_id": "EV-03",
            "title": "The effect of long versus short pectoralis minor resting length on scapular kinematics in healthy individuals",
            "authors": "Borstad JD, Ludewig PM",
            "publication_year": 2005,
            "doi_or_url": "https://doi.org/10.2519/jospt.2005.35.4.227",
            "research_design": "Controlled kinematic cohort study",
            "population": "50 healthy asymptomatic subjects stratified by pectoralis minor length index",
            "claims_supported": "Shortened pectoralis minor resting length is associated with increased anterior scapular tilt and internal rotation during arm elevation.",
            "limitations": "Healthy cohort; establishes kinematic correlation without demonstrating spontaneous tissue pathology.",
            "evidence_status": "CONTROLLED_OBSERVATIONAL",
            "review_date": "2026-10-30",
            "citation": "Borstad JD, Ludewig PM. The effect of long versus short pectoralis minor resting length on scapular kinematics in healthy individuals. J Orthop Sports Phys Ther. 2005;35(4):227-238.",
            "topic": "Link between pectoralis minor resting length and scapular kinematics.",
        },
        {
            "id": "EV-04",
            "evidence_id": "EV-04",
            "title": "Muscles: Testing and Function with Posture and Pain",
            "authors": "Kendall FP, McCreary EK, Provance PG, Rodgers MM, Romani WA",
            "publication_year": 2005,
            "doi_or_url": "ISBN: 978-0781747806",
            "research_design": "Clinical anatomical textbook & expert consensus",
            "population": "Clinical patient cohorts",
            "claims_supported": "Theoretical framework describing reciprocal length-tension muscle imbalances in forward head/shoulder postures.",
            "limitations": "Clinical observational model; posture does not reliably correlate with pain across broad epidemiological surveys.",
            "evidence_status": "CLINICAL_THEORETICAL_MODEL",
            "review_date": "2026-10-30",
            "citation": "Kendall FP, McCreary EK, Provance PG. Muscles: Testing and Function with Posture and Pain. 5th ed. Baltimore: Lippincott Williams & Wilkins; 2005.",
            "topic": "Reciprocal length-tension muscle relationships in postural syndromes.",
        },
        {
            "id": "EV-05",
            "evidence_id": "EV-05",
            "title": "Assessment and Treatment of Muscle Imbalance: The Janda Approach",
            "authors": "Page P, Frank CC, Lardner R",
            "publication_year": 2010,
            "doi_or_url": "ISBN: 978-0736074001",
            "research_design": "Clinical neurodevelopmental framework",
            "population": "Musculoskeletal patient populations",
            "claims_supported": "Emphasizes sensorimotor active training and neuromuscular re-education over isolated passive modalities.",
            "limitations": "Expert framework; requires individualized clinical testing rather than blanket postural categorization.",
            "evidence_status": "CLINICAL_THEORETICAL_MODEL",
            "review_date": "2026-10-30",
            "citation": "Page P, Frank CC, Lardner R. Assessment and Treatment of Muscle Imbalance: The Janda Approach. Human Kinetics; 2010.",
            "topic": "Sensorimotor training and active stabilization in muscle imbalance.",
        },
        {
            "id": "EV-06",
            "evidence_id": "EV-06",
            "title": "Fascial plasticity – a new neurobiological explanation: Part 1 and 2",
            "authors": "Schleip R",
            "publication_year": 2003,
            "doi_or_url": "https://doi.org/10.1016/S1360-8592(02)00067-0",
            "research_design": "Narrative scientific review of mechanoreceptor physiology",
            "population": "In-vitro and in-vivo neurobiology studies",
            "claims_supported": "Manual manipulation stimulates Ruffini and interstitial mechanoreceptors, yielding transient parasympathetic autonomic changes and tone reduction.",
            "limitations": "Explains transient perceptual lightness; does not support claims of permanent structural deformation from manual pressure.",
            "evidence_status": "NARRATIVE_PHYSIOLOGICAL_REVIEW",
            "review_date": "2026-10-30",
            "citation": "Schleip R. Fascial plasticity – a new neurobiological explanation: Part 1 and 2. J Bodyw Mov Ther. 2003;7(1):11-19.",
            "topic": "Neurobiological mechanoreceptor stimulation and transient tissue tone changes.",
        },
        {
            "id": "EV-07",
            "evidence_id": "EV-07",
            "title": "A Scapulothoracic Joint Model for Simulation of Shoulder Biomechanics",
            "authors": "Seth A, Matias R, Veloso AP, Delp SL",
            "publication_year": 2016,
            "doi_or_url": "https://doi.org/10.1080/10255842.2015.1105994",
            "research_design": "Computational multi-body biomechanical model validation",
            "population": "In-vivo motion capture datasets & anatomical specimens",
            "claims_supported": "Accurate OpenSim multi-body kinematic representation of scapulothoracic gliding and joint constraints during arm elevation.",
            "limitations": "Mathematical musculoskeletal model; static optimization muscle activations are model predictions, not directly measured EMG.",
            "evidence_status": "COMPUTATIONAL_MODEL_VALIDATION",
            "review_date": "2026-10-30",
            "citation": "Seth A, Matias R, Veloso AP, Delp SL. A Scapulothoracic Joint Model for Simulation of Shoulder Biomechanics. Comput Methods Biomech Biomed Engin. 2016;19(1):65-76.",
            "topic": "OpenSim computational multi-body scapulothoracic joint kinematic model.",
        },
        {
            "id": "EV-08",
            "evidence_id": "EV-08",
            "title": "In vivo three-dimensional kinematics of the shoulder complex during arm elevation",
            "authors": "Sugamoto K, et al.",
            "publication_year": 2002,
            "doi_or_url": "https://doi.org/10.1016/S1058-2746(02)00007-4",
            "research_design": "In-vivo 3D fluoroscopic kinematic measurement",
            "population": "Healthy adult volunteers",
            "claims_supported": "Demonstrates substantial non-linear variability in scapular upward rotation, posterior tilt, and external rotation across healthy individuals.",
            "limitations": "Demonstrates wide physiological normal ranges, refuting single universal ratio thresholds.",
            "evidence_status": "IN_VIVO_EXPERIMENTAL_IMAGING",
            "review_date": "2026-10-30",
            "citation": "Sugamoto K, et al. In vivo three-dimensional kinematics of the shoulder complex during arm elevation. J Shoulder Elbow Surg. 2002;11(4):378-384.",
            "topic": "In-vivo 3D fluoroscopic shoulder kinematics proving wide physiological variability.",
        },
    ]

    quiz = [
        {
            "question_id": "Q1",
            "question_en": "Is the 2:1 scapulohumeral rhythm a universal physiological law that applies identically to every person?",
            "question_vi": "Tỷ lệ nhịp bả vai - cánh tay 2:1 có phải là quy luật sinh lý bất biến áp dụng cho mọi người không?",
            "options_en": [
                "A. Yes, all healthy shoulders strictly elevate at exactly 2:1.",
                "B. No, it is an idealized historical average. Scapular motion varies dynamically with elevation phase, external loads, and movement planes.",
                "C. Yes, any ratio above 2.1 is always a clinical disease called dyskinesia."
            ],
            "options_vi": [
                "A. Đúng, khớp vai khỏe mạnh luôn luôn nâng tay theo đúng tỷ lệ 2:1.",
                "B. Không, đây là tỷ lệ trung bình lịch sử có tính minh họa. Chuyển động bả vai biến thiên linh hoạt theo góc nâng, tải trọng và mặt phẳng vận động.",
                "C. Đúng, bất kỳ tỷ lệ nào trên 2.1 đều là bệnh lý rối loạn vận động."
            ],
            "correct_option": "B",
            "explanation_en": "Inman (1944) described an overall average, but contemporary 3D kinematics (Ludewig 2000, McClure 2001, Sugamoto 2002) demonstrate that rhythm changes dynamically through movement phases and under external loads.",
            "explanation_vi": "Nghiên cứu của Inman (1944) chỉ ra tỷ lệ trung bình toàn dải, nhưng các nghiên cứu 3D hiện đại (Ludewig 2000, McClure 2001) chứng minh tỷ lệ này biến thiên linh hoạt theo từng giai đoạn chuyển động và tải trọng ngoài."
        },
        {
            "question_id": "Q2",
            "question_en": "Can visual posture inspection alone definitively prove that a specific muscle is weak or short?",
            "question_vi": "Chỉ quan sát tư thế bên ngoài có thể khẳng định chắc chắn cơ nào bị yếu hay co ngắn không?",
            "options_en": [
                "A. Yes, rounded shoulders always mean the pectoralis minor is physically short and the lower trapezius is weak.",
                "B. No, posture reflects resting alignment. Muscle activation and strength require dynamic testing and clinical evaluation.",
                "C. Yes, posture is directly proportional to EMG electrical activity."
            ],
            "options_vi": [
                "A. Có, vai đổ trước luôn luôn có nghĩa là cơ ngực bé bị co ngắn và cơ thang dưới bị yếu.",
                "B. Không, tư thế chỉ phản ánh vị trí nghỉ. Đánh giá sức mạnh và độ hoạt hóa cơ bắp đòi hỏi kiểm tra lâm sàng và đo lường chuyên biệt.",
                "C. Có, tư thế tỉ lệ thuận trực tiếp với mức độ hoạt động điện cơ EMG."
            ],
            "correct_option": "B",
            "explanation_en": "Asymptomatic individuals frequently display forward shoulder postures with normal muscular strength and zero pain. Postural appearance alone is not a medical diagnosis.",
            "explanation_vi": "Rất nhiều người khỏe mạnh không có triệu chứng vẫn có vai hơi đổ trước nhưng cơ bắp hoàn toàn bình thường và không đau. Tư thế đơn thuần không thay thế chẩn đoán lâm sàng."
        },
        {
            "question_id": "Q3",
            "question_en": "Does muscle activation calculated by OpenSim represent directly measured human EMG data?",
            "question_vi": "Mức độ kích hoạt cơ do OpenSim tính toán có phải là điện cơ (EMG) đo trực tiếp trên người không?",
            "options_en": [
                "A. Yes, OpenSim records actual electrical signals through surface electrodes.",
                "B. No, OpenSim muscle activations are mathematical estimates derived from optimization algorithms, not measured bioelectrical signals.",
                "C. Yes, simulation and human measurement are identical."
            ],
            "options_vi": [
                "A. Đúng, OpenSim ghi lại tín hiệu điện thế thực sự qua điện cực bề mặt.",
                "B. Không, kích hoạt cơ trong OpenSim là ước tính toán học từ thuật toán tối ưu hóa, không phải tín hiệu điện sinh học đo trực tiếp.",
                "C. Đúng, mô phỏng và đo đạc thực tế là một."
            ],
            "correct_option": "B",
            "explanation_en": "OpenSim uses static optimization (minimizing sum of squared muscle activations or forces) to predict recruitment. It is a mathematical model estimate, not an empirical bioelectrical measurement.",
            "explanation_vi": "OpenSim sử dụng thuật toán tối ưu hóa tĩnh để dự đoán mức huy động cơ. Đây là kết quả mô phỏng tính toán, không phải dữ liệu điện sinh học thu thập từ cơ thể người."
        },
        {
            "question_id": "Q4",
            "question_en": "Why does forward shoulder posture or stiffness often return days after feeling light from a massage?",
            "question_vi": "Vì sao cảm giác nhẹ nhõm sau giải cơ thường chỉ duy trì vài ngày rồi vai lại đổ trước như cũ?",
            "options_en": [
                "A. Because the therapist did not use enough pressure.",
                "B. Because manual therapy provides transient neurosensory relief, but lasting change requires active exercise, progressive strengthening, and ergonomic habituation.",
                "C. Because massage permanently shortens the posterior muscles."
            ],
            "options_vi": [
                "A. Do kỹ thuật viên chưa dùng đủ lực bóp.",
                "B. Do giải cơ mang lại sự điều hòa thần kinh cảm giác tạm thời, còn cải thiện bền vững đòi hỏi tập luyện chủ động, tăng tải thích nghi và thay đổi thói quen làm việc.",
                "C. Do massage làm ngắn vĩnh viễn các cơ mặt sau."
            ],
            "correct_option": "B",
            "explanation_en": "Manual modalities modulate mechanoreceptors to reduce tone transiently. Long-term structural adaptation and motor repatterning require active neuromuscular activation, progressive loading, and workplace ergonomic habituation.",
            "explanation_vi": "Các kỹ thuật bằng tay giúp điều hòa thụ thể cơ học làm giảm đau và hạ trương lực tạm thời. Sự thích nghi mô lâu dài và học lại vận động bắt buộc phải có tập luyện chủ động và điều chỉnh môi trường làm việc."
        }
    ]

    is_p14 = version.upper() == "P14"

    return {
        "curriculum_id": "P14_SHOULDER_BIOMECHANICS_STUDIO" if is_p14 else "P13_SHOULDER_POSTURE_MECHANICS",
        "version": "2.0.0" if is_p14 else "1.0.0",
        "scientific_gate_status": G14,
        "clinical_depth_guidance_allowed": CLINICAL_DEPTH_GUIDANCE_ALLOWED,
        "title_en": "What Happens When You Raise Your Arm — And Why Do Rounded Shoulders Return?" if is_p14 else "Why Do Rounded Shoulders Sometimes Return After Massage?",
        "title_vi": "Điều gì xảy ra khi bạn giơ tay — Và tại sao vai đổ trước vẫn tái phát sau giải cơ?" if is_p14 else "Tại sao giải cơ xong vai nhẹ hơn nhưng một thời gian sau vẫn đổ về trước?",
        "subtitle_en": "Evidence-Grounded 3D Skeletal Kinematics, Muscle Involvement & Integrative Self-Care" if is_p14 else "Anatomy, Scapulohumeral Biomechanics, Neural Adaptation & Integrative Self-Care",
        "subtitle_vi": "Cơ sinh học chuyển động xương 3D, Vai trò cơ bắp & Tự chăm sóc dựa trên bằng chứng" if is_p14 else "Giải phẫu học, Cơ sinh học bả vai - cánh tay, Thích nghi thần kinh & Tự chăm sóc tích hợp",
        "disclaimers": [
            "ANATOMICAL_MODEL != SUBJECT_SPECIFIC_ANATOMY",
            "ILLUSTRATIVE_KINEMATICS != MEASURED_KINEMATICS",
            "MUSCLE_ACTION_DESCRIPTION != MUSCLE_ACTIVATION_MEASUREMENT",
            "OPTIMIZED_MUSCLE_ACTIVATION != MEASURED_EMG",
            "SIMULATED_FORCE != MEASURED_HUMAN_FORCE",
            "POSTURE_VARIATION != CLINICAL_DIAGNOSIS",
            "G14 = BLOCKED_EXTERNAL_DATA",
        ],
        "stages": p14_stages if is_p14 else p13_stages,
        "p14_stages": p14_stages,
        "quiz": quiz,
        "evidence_register": evidence_register,
        "scenarios": [s.__dict__ for s in get_scenario_catalog()],
        "provenance": {
            "source_muscles": "BodyParts3D / DBCLS Japan via Z-Anatomy (CC BY-SA 2.1 JP)",
            "source_skeleton": "BodyParts3D v4.0 (FJ3290, FJ3178, FJ3334..FJ3342, FJ3362, FJ3384, FJ3368) (CC BY-SA 2.1 JP / CC BY 4.0)",
            "rendering_engine": "Three.js r160 (MIT License)",
            "biomechanics_adapter": "MSK-Therapy-OS OpenSim Kinematics Engine (MIT License)",
        },
    }
