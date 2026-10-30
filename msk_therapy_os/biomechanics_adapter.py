"""MSK-Therapy-OS - OpenSim Biomechanics & Shoulder Kinematics Adapter.

Milestone P13: Open-Source Anatomy & Functional Biomechanics Integration.
Preserves non-negotiable boundaries:
    G14 = BLOCKED_EXTERNAL_DATA
    clinical_depth_guidance_allowed = False
    EDUCATIONAL_SIMULATION != PATIENT_SPECIFIC_MEASUREMENT
    MODEL_PREDICTION != EMPIRICALLY_VALIDATED_MOTION
    MUSCLE_HIGHLIGHT != MEASURED_MUSCLE_ACTIVATION
    POSTURAL_APPEARANCE != MEDICAL_DIAGNOSIS
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


# Invariant Declarations
G14: str = "BLOCKED_EXTERNAL_DATA"
CLINICAL_DEPTH_GUIDANCE_ALLOWED: bool = False
SHOULDER_MOTION_STATUS_UNAVAILABLE: str = "SHOULDER_MOTION_DATA_UNAVAILABLE"


# Recognized physiological ranges for scapular and glenohumeral degrees of freedom (degrees)
# Sourced from Ludewig & Cook 2000, McClure et al. 2001, Inman et al. 1944.
PHYSIOLOGICAL_RANGES_DEG: Dict[str, Tuple[float, float]] = {
    # Glenohumeral
    "arm_flexion": (-30.0, 180.0),
    "arm_elevation": (0.0, 180.0),
    "arm_rotation": (-90.0, 90.0),
    # Scapulothoracic
    "scapula_upward_rot": (-10.0, 60.0),
    "scapula_anterior_tilt": (-20.0, 40.0),
    "scapula_protraction": (-15.0, 45.0),
    # Clavicle
    "clavicle_elevation": (-10.0, 40.0),
    "clavicle_retraction": (-20.0, 40.0),
    # Head & Neck
    "head_forward_translation_mm": (-10.0, 80.0),
    "cervical_extension": (-40.0, 75.0),
}


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
    """Robust parser for OpenSim ASCII storage (.sto) and motion (.mot) files."""

    @classmethod
    def parse_text(cls, content: str, filename_hint: str = "motion.mot") -> OpenSimMotionData:
        lines = [line.strip() for line in content.splitlines()]
        if not lines:
            raise ValueError("OpenSim motion file is empty")

        metadata: Dict[str, str] = {}
        header_line_idx = -1
        in_degrees = True
        n_rows = 0
        n_columns = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            if not line or line.startswith("//") or line.startswith("#"):
                i += 1
                continue

            lower = line.lower()
            if "=" in line:
                k, v = line.split("=", 1)
                metadata[k.strip().lower()] = v.strip()
            elif lower.startswith("indegrees="):
                val = lower.split("=")[1].strip()
                in_degrees = (val == "yes" or val == "true")
            elif lower.startswith("ncolumns="):
                n_columns = int(lower.split("=")[1].strip())
            elif lower.startswith("nrows="):
                n_rows = int(lower.split("=")[1].strip())
            elif lower == "endheader":
                header_line_idx = i + 1
                break
            i += 1

        if header_line_idx == -1 or header_line_idx >= len(lines):
            # Fallback if no endheader token: look for row with 'time'
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

        if n_columns == 0:
            n_columns = len(col_headers)

        time_vals: List[float] = []
        channel_data: Dict[str, List[float]] = {ch: [] for ch in col_headers}

        # Parse numeric data rows
        for row_idx, line in enumerate(lines[header_line_idx + 1:], start=header_line_idx + 1):
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < len(col_headers):
                continue  # skip truncated/empty line
            
            try:
                t = float(parts[0])
                time_vals.append(t)
                for col_i, ch in enumerate(col_headers):
                    channel_data[ch].append(float(parts[col_i]))
            except ValueError as e:
                raise ValueError(f"Non-numeric data encountered at line {row_idx + 1}: {line}") from e

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
    ) -> Dict[str, Any]:
        """Compute the Scapulohumeral Rhythm ratio (GH elevation / ST upward rotation).

        Literature standard (Inman 1944, Ludewig 2009):
        - Classic 2:1 overall ratio (120 deg GH elevation + 60 deg ST upward rotation = 180 deg arm elevation).
        - Rounded shoulder / dyskinesis typically exhibits delayed or reduced scapular upward rotation (< 1.5:1 or > 2.8:1),
          excessive anterior tilt, and compensatory upper trapezius dominance.
        """
        if abs(scapular_upward_rotation_deg) < 1e-4:
            ratio = float("inf") if humeral_elevation_deg > 0 else 0.0
        else:
            ratio = humeral_elevation_deg / scapular_upward_rotation_deg

        # Classification
        if 1.6 <= ratio <= 2.4:
            classification = "PHYSIOLOGICAL_NORMAL_2_TO_1"
            explanation = "Normal scapulohumeral rhythm (~2:1 ratio) coordinated by serratus anterior and trapezius force couple."
        elif ratio > 2.4:
            classification = "SCAPULAR_HYPOMOBILITY_DYSKINESIA"
            explanation = "Reduced scapular upward rotation relative to humeral elevation. Common in rounded shoulders with pectoralis minor tightness and inhibited lower trapezius."
        elif ratio < 1.6 and ratio > 0.5:
            classification = "COMPENSATORY_EARLY_SHRUG"
            explanation = "Excessive early scapular elevation/upward rotation, typically driven by hyperactive upper trapezius and levator scapulae."
        else:
            classification = "ATYPICAL_OR_EXTREME_KINEMATICS"
            explanation = "Ratio outside normal functional movement boundaries."

        return {
            "humeral_elevation_deg": round(humeral_elevation_deg, 2),
            "scapular_upward_rotation_deg": round(scapular_upward_rotation_deg, 2),
            "ratio": round(ratio, 2) if ratio != float("inf") else "INF",
            "reference_standard": "2.0:1 (Inman 1944; Ludewig 2009)",
            "classification": classification,
            "explanation": explanation,
            "clinical_disclaimer": "EDUCATIONAL_SIMULATION_ONLY - NOT_FOR_DIAGNOSTIC_USE",
        }

    @staticmethod
    def evaluate_rounded_shoulder_posture(
        scapula_protraction_deg: float,
        scapula_anterior_tilt_deg: float,
        pectoralis_minor_strain_index: float,  # 0.0 to 1.0 (estimated shortening)
    ) -> Dict[str, Any]:
        """Evaluate postural indices of rounded shoulder posture (protraction + anterior tilt + internal rotation)."""
        # Baseline neutral: protraction ~ 15 deg, anterior tilt ~ 10 deg
        excess_protraction = max(0.0, scapula_protraction_deg - 15.0)
        excess_tilt = max(0.0, scapula_anterior_tilt_deg - 10.0)

        severity_score = (excess_protraction / 30.0) * 0.5 + (excess_tilt / 25.0) * 0.3 + (pectoralis_minor_strain_index * 0.2)
        severity_score = min(1.0, max(0.0, severity_score))

        if severity_score < 0.25:
            level = "NEUTRAL_BALANCED"
        elif severity_score < 0.55:
            level = "MILD_ROUNDED_SHOULDER"
        elif severity_score < 0.80:
            level = "MODERATE_ROUNDED_SHOULDER"
        else:
            level = "MARKED_ROUNDED_SHOULDER"

        return {
            "scapula_protraction_deg": round(scapula_protraction_deg, 2),
            "scapula_anterior_tilt_deg": round(scapula_anterior_tilt_deg, 2),
            "pectoralis_minor_shortening_index": round(pectoralis_minor_strain_index, 2),
            "postural_severity_score": round(severity_score, 3),
            "postural_level": level,
            "biomechanical_triad": [
                "Scapular protraction (anterior displacement on thoracic wall)",
                "Scapular anterior tilt (inferior angle moves away from ribcage)",
                "Humeral internal rotation with shortened pectoralis minor/major",
            ],
            "motion_status": SHOULDER_MOTION_STATUS_UNAVAILABLE,
            "disclaimer": "POSTURAL_APPEARANCE != MEDICAL_DIAGNOSIS",
        }


def get_shoulder_education_curriculum() -> Dict[str, Any]:
    """Deliver full bilingual (EN/VI) interactive curriculum for the Shoulder Studio:

    'Why Do Rounded Shoulders Sometimes Return After Massage?'
    ('Tại sao giải cơ xong vai nhẹ hơn nhưng một thời gian sau vẫn đổ về trước?')
    """
    return {
        "curriculum_id": "P13_SHOULDER_POSTURE_MECHANICS",
        "version": "1.0.0",
        "scientific_gate_status": G14,
        "clinical_depth_guidance_allowed": CLINICAL_DEPTH_GUIDANCE_ALLOWED,
        "title_en": "Why Do Rounded Shoulders Sometimes Return After Massage?",
        "title_vi": "Tại sao giải cơ xong vai nhẹ hơn nhưng một thời gian sau vẫn đổ về trước?",
        "subtitle_en": "Anatomy, Scapulohumeral Biomechanics, Neural Adaptation & Integrative Self-Care",
        "subtitle_vi": "Giải phẫu học, Cơ sinh học bả vai - cánh tay, Thích nghi thần kinh & Tự chăm sóc tích hợp",
        "disclaimers": [
            "EDUCATIONAL_SIMULATION != PATIENT_SPECIFIC_MEASUREMENT",
            "MODEL_PREDICTION != EMPIRICALLY_VALIDATED_MOTION",
            "MUSCLE_HIGHLIGHT != MEASURED_MUSCLE_ACTIVATION",
            "POSTURAL_APPEARANCE != MEDICAL_DIAGNOSIS",
            "G14 = BLOCKED_EXTERNAL_DATA",
        ],
        "stages": [
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
        ],
        "evidence_register": [
            {
                "id": "EV-01",
                "citation": "Inman VT, Saunders JB, Abbott LC. Observations on the function of the shoulder joint. J Bone Joint Surg Am. 1944;26(1):1-30.",
                "topic": "Foundational description of the 2:1 scapulohumeral rhythm.",
            },
            {
                "id": "EV-02",
                "citation": "Ludewig PM, Cook TM. Alterations in shoulder kinematics and associated muscle activity in people with symptoms of shoulder impingement. Phys Ther. 2000;80(3):276-291.",
                "topic": "Demonstrated reduced scapular upward rotation and increased anterior tilt in impingement and rounded posture.",
            },
            {
                "id": "EV-03",
                "citation": "Borstad JD, Ludewig PM. The effect of long versus short pectoralis minor resting length on scapular kinematics in healthy individuals. J Orthop Sports Phys Ther. 2005;35(4):227-238.",
                "topic": "Proved direct link between pectoralis minor shortness and altered scapular kinematics during elevation.",
            },
            {
                "id": "EV-04",
                "citation": "Kendall FP, McCreary EK, Provance PG. Muscles: Testing and Function with Posture and Pain. 5th ed. Baltimore: Lippincott Williams & Wilkins; 2005.",
                "topic": "Reciprocal inhibition and muscular length-tension relationships in upper crossed syndrome.",
            },
        ],
        "provenance": {
            "source_mesh": "BodyParts3D / DBCLS (CC BY-SA 2.1 JP)",
            "curator": "Z-Anatomy (CC BY-SA)",
            "rendering_engine": "Three.js r160 (MIT)",
            "biomechanics_adapter": "MSK-Therapy-OS Biomechanics Engine (MIT)",
        },
    }
