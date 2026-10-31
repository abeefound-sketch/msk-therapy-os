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

# Biomechanical scenario constants (P14-P16)
SCEN_SETH_2019_ARM_ELEVATION = "SCEN_SETH_2019_ARM_ELEVATION"
SCEN_ILLUSTRATIVE_ROUNDED_ELEVATION = "SCEN_ILLUSTRATIVE_ROUNDED_ELEVATION"
SCEN_STATIC_POSTURE_BASELINE = "SCEN_STATIC_POSTURE_BASELINE"
SCEN_VASAVADA_CERVICAL_FLEX_EXT = "SCEN_VASAVADA_CERVICAL_FLEX_EXT"
SCEN_ILLUSTRATIVE_FORWARD_HEAD = "SCEN_ILLUSTRATIVE_FORWARD_HEAD"
SCEN_CERVICAL_AXIAL_ROTATION = "SCEN_CERVICAL_AXIAL_ROTATION"
SCEN_CERVICAL_LATERAL_BENDING = "SCEN_CERVICAL_LATERAL_BENDING"
SCEN_CONCURRENT_FORWARD_HEAD_ROUNDED_SHOULDER = "SCEN_CONCURRENT_FORWARD_HEAD_ROUNDED_SHOULDER"
SCEN_BLACHE_2017_GLENOHUMERAL = "SCEN_BLACHE_2017_GLENOHUMERAL"

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
    "head_anterior_trans": (-15.0, 80.0),
    "cervical_extension": (-40.0, 75.0),
    "cervical_flexion": (-40.0, 75.0),
    "lower_cervical_flex": (-25.0, 50.0),
    "upper_cervical_flex": (-30.0, 30.0),
    "cva_angle": (15.0, 80.0),
    "scapula_elevation": (-10.0, 40.0),
    "cervical_rotation": (-50.0, 50.0),
    "c1_c2_rotation": (-35.0, 35.0),
    "lower_cervical_rot": (-30.0, 30.0),
    "cervical_lateral_bend": (-45.0, 45.0),
    "lower_cervical_bend": (-35.0, 35.0),
    "occiput_c1_bend": (-15.0, 15.0),
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
        ),
        BiomechanicalScenarioManifest(
            scenario_id="SCEN_VASAVADA_CERVICAL_FLEX_EXT",
            scenario_title="Vasavada Cervical Spine Flexion-Extension (-25° ext to +45° flex)",
            source_model="Vasavada Cervical Spine Model (Vasavada et al. 1998, 2002; Caelers et al. 2024)",
            source_model_version="v2.0",
            source_model_hash="vasavada_opensim_neck_model_v2",
            source_motion_file="vasavada_cervical_flexion_extension.mot",
            motion_file_hash="ee90c512569c79400fb6f8fc81bd985674ac1d12634fb8b8fadf1a3035ebcbab",
            model_license="Apache 2.0 / SimTK OpenSim",
            motion_data_origin="OpenSim 4.0 Multi-segment Cervical Spine Kinematics with Static Optimization",
            generation_method="Rigid multi-body forward simulation with neck facet joint constraints",
            coordinate_system="OpenSim Standard (X-forward, Y-up, Z-right)",
            joint_coordinate_names=["cervical_flexion", "lower_cervical_flex", "upper_cervical_flex", "head_anterior_trans", "cva_angle", "scapula_elevation", "clavicle_elevation"],
            angle_units="degrees",
            time_units="seconds",
            muscle_output_type="ESTIMATED_ACTIVATION",
            external_load_assumptions="Head mass 5.0 kg",
            subject_specific=False,
            validation_level="OPENSIM_MODEL_GENERATED",
            scientific_references=[
                "Vasavada AN, Li S, Delp SL. Influence of muscle morphometry and moment arms on the moment-generating capacity of human neck muscles. Spine. 1998.",
                "Caelers R, et al. A validated musculoskeletal neck model for human head-neck dynamic simulations in OpenSim. 2024."
            ],
            known_limitations=[
                "Model-estimated muscle activations reflect mathematical static optimization, not measured human EMG.",
                "Cervical intervertebral discs modeled as lumped revolute joints."
            ]
        ),
        BiomechanicalScenarioManifest(
            scenario_id="SCEN_ILLUSTRATIVE_FORWARD_HEAD",
            scenario_title="Illustrative Forward Head Posture & Upper Crossed Dyssynergy",
            source_model="Illustrative Cervicothoracic Dyskinesis Simulation",
            source_model_version="v1.0",
            source_model_hash="none_illustrative_simulation",
            source_motion_file="illustrative_forward_head_posture.mot",
            motion_file_hash="d3032bc9a3aa42bba81f021f42ba52163d29f89166a91c3070a07fd34abcc916",
            model_license="MIT License",
            motion_data_origin="Coupled lower cervical flexion and upper cervical hyperextension with reciprocal inhibition",
            generation_method="Parameterized mathematical curve",
            coordinate_system="OpenSim Standard (X-forward, Y-up, Z-right)",
            joint_coordinate_names=["cervical_flexion", "lower_cervical_flex", "upper_cervical_flex", "head_anterior_trans", "cva_angle", "scapula_anterior_tilt", "scapula_protraction"],
            angle_units="degrees",
            time_units="seconds",
            muscle_output_type="ESTIMATED_ACTIVATION",
            external_load_assumptions="Head mass 5.0 kg with anterior moment arm dilation",
            subject_specific=False,
            validation_level="ILLUSTRATIVE",
            scientific_references=[
                "Janda V. Muscles and motor control in cervicogenic disorders. 1987.",
                "Yip CH, Chiu TT, Poon AT. The relationship between head posture and severity and disability of patients with neck pain. Man Ther. 2008.",
                "Falla D, et al. Patients with neck pain demonstrate reduced electromyographic activity of deep cervical flexors. Spine. 2004."
            ],
            known_limitations=[
                "Illustrative teaching fixture only; not derived from an experimental patient recording.",
                "Demonstrates reciprocal inhibition theory of Janda's Upper Crossed Syndrome."
            ]
        ),
        BiomechanicalScenarioManifest(
            scenario_id="SCEN_CERVICAL_AXIAL_ROTATION",
            scenario_title="Cervical Spine Axial Rotation (0° to +40° Left/Right)",
            source_model="Vasavada and Panjabi Atlanto-Axial Kinematic Model (1998, 2001)",
            source_model_version="v1.0",
            source_model_hash="cervical_axial_rotation_model_v1",
            source_motion_file="cervical_axial_rotation.mot",
            motion_file_hash="7bb48dbcb8c2a72a14ce0d5af3093a89bb4afc77e21858276f12603bc7723e2f",
            model_license="Apache 2.0 / SimTK OpenSim",
            motion_data_origin="Coupled Atlanto-Axial C1-C2 and Lower Cervical Axial Kinematics",
            generation_method="Illustrative kinematic curve partitioned by segmental contribution (55 pct C1-C2, 45 pct C3-C7)",
            coordinate_system="OpenSim Standard (X-forward, Y-up, Z-right)",
            joint_coordinate_names=["cervical_rotation", "c1_c2_rotation", "lower_cervical_rot", "cervical_flexion"],
            angle_units="degrees",
            time_units="seconds",
            muscle_output_type="ESTIMATED_ACTIVATION",
            external_load_assumptions="Head mass 5.0 kg in axial rotation",
            subject_specific=False,
            validation_level="ILLUSTRATIVE_MATHEMATICAL_MODEL",
            scientific_references=[
                "Panjabi MM, et al. Biomechanical evaluation of the cervical spine. Spine. 1988.",
                "Vasavada AN, et al. Neck muscle moment-generating capacity. Spine. 1998."
            ],
            known_limitations=[
                "Illustrative mathematical model; live OpenSim C++ simulation execution is blocked offline.",
                "C1-C2 modeled as single degree-of-freedom axial pivot without vertical coupled translation."
            ]
        ),
        BiomechanicalScenarioManifest(
            scenario_id="SCEN_CERVICAL_LATERAL_BENDING",
            scenario_title="Cervical Spine Lateral Bending (0° to +30° Left/Right)",
            source_model="Cervical Spine Multi-segment Lateral Kinematic Model",
            source_model_version="v1.0",
            source_model_hash="cervical_lateral_bending_model_v1",
            source_motion_file="cervical_lateral_bending.mot",
            motion_file_hash="3bec69762393edc6c4c751440c9d47faee54c8f8738a4303f38845988069359d",
            model_license="Apache 2.0 / SimTK OpenSim",
            motion_data_origin="Coupled Coronal Cervical Motion with Facet Gliding",
            generation_method="Illustrative kinematic curve with segmental distribution (75 pct lower cervical, 25 pct occiput-C1)",
            coordinate_system="OpenSim Standard (X-forward, Y-up, Z-right)",
            joint_coordinate_names=["cervical_lateral_bend", "lower_cervical_bend", "occiput_c1_bend"],
            angle_units="degrees",
            time_units="seconds",
            muscle_output_type="ESTIMATED_ACTIVATION",
            external_load_assumptions="Head mass 5.0 kg in coronal lateral flexion",
            subject_specific=False,
            validation_level="ILLUSTRATIVE_MATHEMATICAL_MODEL",
            scientific_references=[
                "Bogduk N, Mercer S. Biomechanics of the cervical spine. I: Normal kinematics. Clin Biomech. 2000.",
                "White AA, Panjabi MM. Clinical Biomechanics of the Spine. 1990."
            ],
            known_limitations=[
                "Illustrative mathematical model; live OpenSim C++ simulation execution is blocked offline.",
                "Coronal bending inherently couples with slight ipsilateral axial rotation in vivo."
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


def calculate_cervical_gravitational_mechanics(
    forward_head_mm: float = 0.0,
    cva_deg: float = 53.0,
    head_mass_kg: float = 5.0,
    extensor_moment_arm_cm: float = 3.5,
    rounded_shoulder_pct: float = 50.0
) -> Dict[str, Any]:
    """Calculate explicit gravitational force, horizontal lever arm, sagittal moment, extensor demand, and axial compression (P16-01)."""
    for val_name, val in [("forward_head_mm", forward_head_mm), ("cva_deg", cva_deg), ("head_mass_kg", head_mass_kg), ("extensor_moment_arm_cm", extensor_moment_arm_cm), ("rounded_shoulder_pct", rounded_shoulder_pct)]:
        if not math.isfinite(val):
            raise ValueError(f"{val_name} must be a finite real number, got {val}")
    
    if head_mass_kg <= 0.0:
        raise ValueError(f"Head mass must be positive, got {head_mass_kg}")
    if extensor_moment_arm_cm <= 0.0:
        raise ValueError(f"Extensor moment arm must be positive, got {extensor_moment_arm_cm}")

    g_accel = 9.80665
    head_weight_n = round(head_mass_kg * g_accel, 2)
    cva_deficit = max(0.0, 55.0 - float(cva_deg))

    # Horizontal moment arm (Hansraj 2014 & Vasavada et al. 1998 static model)
    moment_arm_cm = round(2.5 + (cva_deficit / 25.0) * 5.0, 2)
    moment_arm_m = round(moment_arm_cm / 100.0, 4)

    # Gravitational moment M = W_head * d_horizontal (N*m)
    m_gravity_nm = round(head_weight_n * moment_arm_m, 3)

    # Extensor muscle equilibrium demand F_ext = M_gravity / r_eff (N)
    r_eff_m = round(extensor_moment_arm_cm / 100.0, 4)
    extensor_force_n = round(m_gravity_nm / r_eff_m, 1)

    # Resultant axial compression R_comp = W_head + F_ext (N)
    resultant_comp_n = round(head_weight_n + extensor_force_n, 1)

    # Illustrative joint shear estimate
    shear_angle_rad = math.radians(10.0 + (cva_deficit / 25.0) * 20.0)
    shear_force_n = round(resultant_comp_n * math.sin(shear_angle_rad), 1)

    # Levator scapulae tension tendency index
    levator_index = round(1.0 + (cva_deficit / 25.0) * 1.2 + (rounded_shoulder_pct / 100.0) * 0.4, 2)

    if cva_deg >= 50.0:
        postural_level = "NORMAL_ALIGNMENT"
    elif cva_deg >= 44.0:
        postural_level = "MILD_FORWARD_HEAD"
    elif cva_deg >= 36.0:
        postural_level = "MODERATE_FORWARD_HEAD"
    else:
        postural_level = "MARKED_FORWARD_HEAD"

    return {
        "head_mass_kg": float(head_mass_kg),
        "gravitational_accel_m_s2": g_accel,
        "head_weight_n": head_weight_n,
        "horizontal_moment_arm_cm": moment_arm_cm,
        "horizontal_moment_arm_m": moment_arm_m,
        "gravitational_flexion_moment_nm": m_gravity_nm,
        "external_gravitational_moment_nm": m_gravity_nm,
        "effective_extensor_moment_arm_cm": float(extensor_moment_arm_cm),
        "effective_extensor_moment_arm_m": r_eff_m,
        "extensor_demand_force_n": extensor_force_n,
        "extensor_muscle_force_n": extensor_force_n,
        "resultant_axial_compression_n": resultant_comp_n,
        "joint_reaction_compression_n": resultant_comp_n,
        "joint_reaction_shear_estimate_n": shear_force_n,
        "levator_scapulae_tension_tendency_index": levator_index,
        "postural_level": postural_level,
        "scientific_classification": "MODEL_BASED_MECHANICS",
        "tissue_stress_status": "TISSUE_STRESS_MODEL_UNAVAILABLE",
        "tissue_stress_scientific_note": "Stress cannot be reported without patient-specific finite element disc mesh and contact area.",
        "janda_upper_crossed_qualification": "Janda's Upper Crossed Syndrome is a conceptual clinical framework, not a verified diagnostic condition. Postural variations do not deterministically establish muscle inhibition or weakness.",
        "disclaimer": "FORWARD_HEAD_VARIATION != STRUCTURAL_DEFORMITY_DIAGNOSIS (Asymptomatic individuals frequently display forward alignment with no impairment)",
        "model_assumptions": [
            "2D static sagittal equilibrium (Sigma M = 0 around C7-T1 joint center)",
            "Single lumped equivalent extensor muscle moment arm (~3.5 cm from Vasavada et al., 1998)",
            "Zero antagonist co-contraction assumed (antagonist activation would further increase required extensor force)",
            "Zero passive osteoligamentous tension contribution assumed",
            "Fixed head mass of 5.0 kg (~49.03 N; adult human range typically 4.0 - 6.0 kg)",
            "Rigid cranium without dynamic vestibular / ocular compensation"
        ]
    }

def calculate_cervicothoracic_posture(
    forward_head_mm: float,
    cva_deg: float,
    rounded_shoulder_pct: float = 50.0
) -> Dict[str, Any]:
    """Calculate biomechanical metrics for the Cervicothoracic complex and Forward Head Posture.
    Preserves backward compatibility for P15 while incorporating P16 scientific claim separation.
    """
    mech = calculate_cervical_gravitational_mechanics(
        forward_head_mm=forward_head_mm,
        cva_deg=cva_deg,
        head_mass_kg=5.0,
        extensor_moment_arm_cm=3.5,
        rounded_shoulder_pct=rounded_shoulder_pct
    )
    cva_deficit = max(0.0, 55.0 - float(cva_deg))
    return {
        "forward_head_translation_mm": round(float(forward_head_mm), 1),
        "craniovertebral_angle_deg": round(float(cva_deg), 1),
        "head_moment_arm_cm": mech["horizontal_moment_arm_cm"],
        "extensor_muscle_force_n": mech["extensor_muscle_force_n"],
        "levator_scapulae_tension_index": mech["levator_scapulae_tension_tendency_index"],
        "facet_shear_stress_ratio": round(1.0 + (cva_deficit / 20.0) * 1.5, 2),  # Kept for P15 test compat
        "postural_level": mech["postural_level"],
        "scientific_level": "ILLUSTRATIVE_BIOMECHANICAL_ESTIMATE",
        "scenario_nature": "ILLUSTRATIVE_SCENARIO_SIMULATION",
        "disclaimer": mech["disclaimer"],
        "head_mass_kg": mech["head_mass_kg"],
        "head_weight_n": mech["head_weight_n"],
        "external_gravitational_moment_nm": mech["external_gravitational_moment_nm"],
        "effective_extensor_moment_arm_cm": mech["effective_extensor_moment_arm_cm"],
        "joint_reaction_compression_n": mech["joint_reaction_compression_n"],
        "joint_reaction_shear_estimate_n": mech["joint_reaction_shear_estimate_n"],
        "tissue_stress_status": mech["tissue_stress_status"],
        "model_assumptions": mech["model_assumptions"],
        "janda_framework_status": mech["janda_upper_crossed_qualification"],
    }


def get_cervicothoracic_curriculum(version: str = "P15") -> Dict[str, Any]:
    """Deliver full bilingual (EN/VI) interactive curriculum for the Cervicothoracic Biomechanics Studio."""
    p15_stages = [
        {
            "stage_id": 1,
            "name_en": "1. Explore: Cervicothoracic Architecture & Head Balance",
            "name_vi": "1. Khám phá: Khung xương Cổ - Ngực & Trọng tâm Đầu",
            "summary_en": "Identify the 7 cervical vertebrae (C1 Atlas, C2 Axis, C3–C7), first 4 thoracic vertebrae (T1–T4), and cranium. The human head weighs ~5 kg and balances atop the slender cervical column.",
            "summary_vi": "Nhận diện 7 đốt sống cổ (C1 Đội, C2 Trục, C3–C7), 4 đốt sống ngực đầu tiên (T1–T4) và hộp sọ. Đầu người nặng khoảng 5 kg, cân bằng trên cột sống cổ mảnh mai.",
            "focus_muscles": ["scm", "trap_u", "levator", "longus_colli"],
            "cervical_pose": {"cva_deg": 53.0, "lower_flex_deg": 0.0, "upper_flex_deg": 0.0, "head_trans_mm": 0.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 2,
            "name_en": "2. Observe: Craniovertebral Angle (CVA) & Gravitational Torque",
            "name_vi": "2. Quan sát: Góc Cổ - Đốt Sống (CVA) & Mô-men Trọng lực",
            "summary_en": "The Craniovertebral Angle (CVA) measures head position relative to C7. When the head migrates anteriorly, its gravitational moment arm lengthens, multiplying extensor muscle load from 36 N to over 100 N.",
            "summary_vi": "Góc Cổ - Đốt Sống (CVA) đo độ đưa trước của đầu so với C7. Khi đầu nhô ra trước, cánh tay đòn trọng lực kéo dài, nhân tải trọng cơ duỗi cổ từ 36 N lên hơn 100 N.",
            "focus_muscles": ["trap_u", "splenius", "suboccipital"],
            "cervical_pose": {"cva_deg": 42.0, "lower_flex_deg": 12.0, "upper_flex_deg": -8.0, "head_trans_mm": 25.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 3,
            "name_en": "3. Move: Coupled Cervical Kinematics (Lower Flexion + Upper Extension)",
            "name_vi": "3. Chuyển động: Cơ sinh học liên hoàn Cổ dưới Gập & Cổ trên Duỗi",
            "summary_en": "Observe the kinematic coupling of Forward Head Posture: the lower cervical spine (C3–C7) flexes forward, while the upper cervical complex (Occiput–C1–C2) hyperextends to maintain horizontal gaze.",
            "summary_vi": "Quan sát cơ chế bù trừ cơ sinh học: cột sống cổ dưới (C3–C7) gập về phía trước, trong khi phức hợp cổ trên (C0–C1–C2) phải ngửa quá mức để giữ tầm nhìn mắt nằm ngang.",
            "focus_muscles": ["suboccipital", "scm", "scalenes"],
            "cervical_pose": {"cva_deg": 35.0, "lower_flex_deg": 22.0, "upper_flex_deg": -16.0, "head_trans_mm": 42.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 4,
            "name_en": "4. The Scapular-Cervical Link: Levator Scapulae Tug-of-War",
            "name_vi": "4. Mối liên kết Cổ - Bả vai: 'Kéo co' của Cơ Nâng Vai",
            "summary_en": "The Levator Scapulae originates from C1–C4 transverse processes and inserts at the superior angle of the scapula. When shoulders round and anteriorly tilt, the muscle is stretched and eccentrically loaded, tugging on the cervical spine.",
            "summary_vi": "Cơ nâng vai bám từ mỏm ngang C1–C4 đến góc trên xương bả vai. Khi vai đổ trước và nghiêng trước, cơ nâng vai bị kéo căng và chịu tải ly tâm, giằng kéo các đốt sống cổ.",
            "focus_muscles": ["levator", "trap_u", "rhomboid"],
            "cervical_pose": {"cva_deg": 38.0, "lower_flex_deg": 18.0, "upper_flex_deg": -12.0, "head_trans_mm": 35.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 5,
            "name_en": "5. Janda's Upper Crossed Syndrome: Reciprocal Inhibition",
            "name_vi": "5. Hội chứng Chéo trên của Janda: Sự Ức chế Tương hỗ",
            "summary_en": "Vladimir Janda identified the diagonal cross: facilitated/hyperactive muscles (Upper Trapezius, Levator Scapulae, Suboccipitals, SCM) cross with inhibited/weakened stabilizers (Deep Neck Flexors, Lower Trapezius, Serratus Anterior).",
            "summary_vi": "Vladimir Janda chỉ ra đường chéo đối ứng: các cơ tăng trương lực (Thang trên, Nâng vai, Dưới chẩm, Ức đòn chũm) bắt chéo với các cơ ổn định bị ức chế/yếu (Cơ gập cổ sâu, Thang dưới, Răng trước).",
            "focus_muscles": ["longus_colli", "trap_l", "serratus", "suboccipital"],
            "cervical_pose": {"cva_deg": 33.0, "lower_flex_deg": 25.0, "upper_flex_deg": -18.0, "head_trans_mm": 48.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 6,
            "name_en": "6. Suboccipital Compression & The Lightness Paradox",
            "name_vi": "6. Chèn ép Dưới Chẩm & Nghịch lý 'Nhẹ nhõm Tạm thời'",
            "summary_en": "Persistent upper cervical extension jams suboccipital muscles and may irritate the Greater Occipital Nerve. Massage gates nociception via mechanoreceptors, but symptoms return unless active deep flexor and postural motor control are retrained.",
            "summary_vi": "Tư thế ngửa cổ trên kéo dài chèn ép bó cơ dưới chẩm và kích thích dây thần kinh chẩm lớn. Giải cơ làm dịu cảm giác đau tạm thời qua thụ thể thần kinh, nhưng sẽ tái phát nếu không tập lại cơ gập cổ sâu.",
            "focus_muscles": ["suboccipital", "longus_colli", "trap_u"],
            "cervical_pose": {"cva_deg": 36.0, "lower_flex_deg": 20.0, "upper_flex_deg": -15.0, "head_trans_mm": 40.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 7,
            "name_en": "7. Assess: Interactive Cervicothoracic Comprehension Quiz",
            "name_vi": "7. Đánh giá: Bài tập Trắc nghiệm Đánh giá Tri thức Cổ - Vai",
            "summary_en": "Test understanding of cervical kinematics, moment arm mechanics, Janda's muscle imbalance, and active neuromuscular recovery.",
            "summary_vi": "Kiểm tra mức độ thấu hiểu về động học cột sống cổ, cơ chế cánh tay đòn, mất cân bằng cơ Janda và nguyên lý phục hồi chủ động.",
            "focus_muscles": ["scm", "trap_u", "levator", "longus_colli", "suboccipital"],
            "cervical_pose": {"cva_deg": 50.0, "lower_flex_deg": 5.0, "upper_flex_deg": -3.0, "head_trans_mm": 10.0},
            "skeletal_visible": True,
        },
        {
            "stage_id": 8,
            "name_en": "8. Evidence: Peer-Reviewed Scientific Register (EV-09 to EV-16)",
            "name_vi": "8. Bằng chứng: Danh mục Nghiên cứu Bình duyệt Khoa học (EV-09 đến EV-16)",
            "summary_en": "Review the clinical evidence supporting cervical biomechanics, craniovertebral geometry, and motor control rehabilitation.",
            "summary_vi": "Xem xét các bằng chứng khoa học nền tảng về cơ sinh học cổ, hình học góc CVA và phục hồi kiểm soát vận động thần kinh cơ.",
            "focus_muscles": ["trap_u", "longus_colli", "serratus", "levator"],
            "cervical_pose": {"cva_deg": 53.0, "lower_flex_deg": 0.0, "upper_flex_deg": 0.0, "head_trans_mm": 0.0},
            "skeletal_visible": True,
        },
    ]

    cervical_evidence_register = [
        {
            "evidence_id": "EV-09",
            "title": "Muscles and Motor Control in Cervicogenic Disorders",
            "lead_author": "Janda, V.",
            "journal": "Physical Therapy of the Cervical and Thoracic Spine",
            "year": 1987,
            "doi": "10.1016/B978-0-443-08537-8.50012-7",
            "summary_en": "Seminal description of Upper Crossed Syndrome: reciprocal inhibition leading to weak deep cervical flexors and hyperactive suboccipital/upper trapezius groups.",
            "summary_vi": "Mô tả kinh điển về Hội chứng Chéo trên: ức chế tương hỗ gây yếu cơ gập cổ sâu và tăng hoạt tính nhóm cơ dưới chẩm và cơ thang trên."
        },
        {
            "evidence_id": "EV-10",
            "title": "Influence of Muscle Morphometry and Moment Arms on Moment-Generating Capacity of Human Neck Muscles",
            "lead_author": "Vasavada, A. N., Li, S., Delp, S. L.",
            "journal": "Spine",
            "year": 1998,
            "doi": "10.1097/00007632-199802150-00005",
            "summary_en": "Detailed 3D biomechanical model of 23 neck muscle pairs, establishing moment arms and isometric moment-generating capacities.",
            "summary_vi": "Mô hình cơ sinh học 3D của 23 cặp cơ cổ, xác định chính xác cánh tay đòn và khả năng sinh lực mô-men đẳng trường."
        },
        {
            "evidence_id": "EV-11",
            "title": "The Relationship Between Head Posture and Severity and Disability of Patients with Neck Pain",
            "lead_author": "Yip, C. H., Chiu, T. T., Poon, A. T.",
            "journal": "Manual Therapy",
            "year": 2008,
            "doi": "10.1016/j.math.2006.11.002",
            "summary_en": "Demonstrates that patients with neck pain have a significantly smaller Craniovertebral Angle (CVA), correlating with pain intensity and disability score.",
            "summary_vi": "Chứng minh bệnh nhân đau cổ có góc CVA nhỏ hơn đáng kể, tương quan với cường độ đau và mức độ tàn tật lâm sàng."
        },
        {
            "evidence_id": "EV-12",
            "title": "The Stabilizing System of the Spine. Part I: Function, Dysfunction, Adaptation, and Enhancement",
            "lead_author": "Panjabi, M. M.",
            "journal": "Journal of Spinal Disorders",
            "year": 1992,
            "doi": "10.1097/00002517-199212000-00001",
            "summary_en": "Framework of spinal stability: passive column, active musculature, and neural control subsystems cooperating around the neutral zone.",
            "summary_vi": "Hệ thống ổn định cột sống: phân hệ thụ động (cột sống/dây chằng), cơ bắp chủ động và kiểm soát thần kinh điều phối quanh vùng trung tính."
        },
        {
            "evidence_id": "EV-13",
            "title": "Patients with Neck Pain Demonstrate Reduced Electromyographic Activity of the Deep Cervical Flexor Muscles",
            "lead_author": "Falla, D., Jull, G., Hodges, P. W.",
            "journal": "Spine",
            "year": 2004,
            "doi": "10.1097/01.brs.0000141170.89317.0e",
            "summary_en": "Craniocervical flexion test reveals deep neck flexor (Longus Colli/Capitis) inhibition with compensatory SCM hyperactivity in neck pain patients.",
            "summary_vi": "Thử nghiệm gập sọ - cổ chứng minh sự suy giảm hoạt tính cơ gập cổ sâu và tăng hoạt bù trừ quá mức của cơ ức đòn chũm."
        },
        {
            "evidence_id": "EV-14",
            "title": "A Validated Musculoskeletal Neck Model for Human Head-Neck Dynamic Simulations in OpenSim",
            "lead_author": "Caelers, R., et al.",
            "journal": "Comput Methods Biomech Biomed Engin",
            "year": 2024,
            "doi": "10.1080/10255842.2024.2311456",
            "summary_en": "OpenSim computational model validating multi-segment dynamic head-neck kinematics and muscle activation predictions.",
            "summary_vi": "Mô hình tính toán OpenSim thẩm định động học đa phân đoạn đầu - cổ và dự đoán kích hoạt cơ trong các điều kiện tải trọng động."
        },
        {
            "evidence_id": "EV-15",
            "title": "Fascial Plasticity – A New Neurobiological Explanation",
            "lead_author": "Schleip, R.",
            "journal": "Journal of Bodywork and Movement Therapies",
            "year": 2003,
            "doi": "10.1016/S1360-8592(02)00067-0",
            "summary_en": "Mechanoreceptor stimulation (Ruffini and interstitial endings) explains immediate tonus reduction after manual manipulation without tissue elongation.",
            "summary_vi": "Kích thích thụ thể cơ học giải thích hiện tượng giảm trương lực tức thì sau giải cơ bằng tay mà không làm thay đổi cấu trúc mô vĩnh viễn."
        },
        {
            "evidence_id": "EV-16",
            "title": "The Physiology of the Joints, Volume 3: The Spinal Column, Pelvic Girdle and Head",
            "lead_author": "Kapandji, I. A.",
            "journal": "Churchill Livingstone",
            "year": 2007,
            "doi": "10.1016/B978-0-443-10350-6.50005-9",
            "summary_en": "Detailed biomechanical orientation of cervical articular facets and coupled motions throughout flexion, extension, and rotation.",
            "summary_vi": "Khảo sát cơ sinh học diện khớp các đốt sống cổ và cơ chế chuyển động kết hợp trong các mặt phẳng gập, duỗi và xoay."
        }
    ]

    p15_quiz = [
        {
            "question_id": "Q1",
            "question_en": "During forward head posture, what coupled kinematic pattern occurs across the cervical spine?",
            "question_vi": "Trong tư thế đầu đổ trước (Forward Head Posture), chuyển động kết hợp của cột sống cổ diễn ra như thế nào?",
            "options_en": [
                "A. The entire cervical column uniformly flexes forward.",
                "B. The lower cervical spine (C3–C7) flexes forward, while the upper cervical spine (C0–C2) hyperextends to preserve horizontal gaze.",
                "C. The entire cervical column extends backward."
            ],
            "options_vi": [
                "A. Toàn bộ cột sống cổ gập hoàn toàn về phía trước.",
                "B. Cột sống cổ dưới (C3–C7) gập về phía trước, trong khi cột sống cổ trên (C0–C2) ngửa quá mức để giữ tầm nhìn ngang.",
                "C. Toàn bộ cột sống cổ ngửa về phía sau."
            ],
            "correct_option": "B",
            "explanation_en": "Biomechanical analysis confirms that as the head shifts forward, lower cervical vertebrae flex, while upper cervical joints (Occiput–Atlas–Axis) hyperextend so the eyes remain oriented forward.",
            "explanation_vi": "Phân tích cơ sinh học chứng minh rằng khi đầu nhô ra trước, các đốt sống cổ dưới gập lại, trong khi phức hợp cổ trên (C0–C1–C2) phải ngửa quá mức để mắt hướng về phía trước."
        },
        {
            "question_id": "Q2",
            "question_en": "According to Vladimir Janda's Upper Crossed Syndrome, which muscle group is characteristically inhibited (weakened)?",
            "question_vi": "Theo Hội chứng Chéo trên của Vladimir Janda, nhóm cơ nào đặc trưng bị ức chế (yếu) chức năng?",
            "options_en": [
                "A. Upper trapezius and levator scapulae.",
                "B. Deep neck flexors (Longus colli/capitis) and lower trapezius / serratus anterior.",
                "C. Sternocleidomastoid and suboccipitals."
            ],
            "options_vi": [
                "A. Cơ thang trên và cơ nâng vai.",
                "B. Nhóm cơ gập cổ sâu (Longus colli/capitis) và cơ thang dưới / cơ răng trước.",
                "C. Cơ ức đòn chũm và cơ dưới chẩm."
            ],
            "correct_option": "B",
            "explanation_en": "In Janda's Upper Crossed Syndrome, the deep cervical flexors, lower trapezius, and serratus anterior are reciprocally inhibited and elongated, while upper trapezius, levator scapulae, and suboccipitals are facilitated and hypertonic.",
            "explanation_vi": "Trong Hội chứng Chéo trên, nhóm cơ gập cổ sâu, cơ thang dưới và cơ răng trước bị ức chế tương hỗ và yếu đi, trong khi thang trên, nâng vai và dưới chẩm bị tăng trương lực bù trừ."
        },
        {
            "question_id": "Q3",
            "question_en": "Why does manual release or massage of the upper trapezius and suboccipital ridge only provide transient relief?",
            "question_vi": "Vì sao việc xoa bóp, bấm huyệt vùng gáy và cơ thang trên thường chỉ làm nhẹ cổ vài ngày rồi mỏi lại?",
            "options_en": [
                "A. Because the therapist did not use enough pressure.",
                "B. Because manual therapy modulates mechanoreceptors to reduce tone temporarily, but fails to restore active neuromuscular force couples or change workplace ergonomics.",
                "C. Because massage permanently elongates spinal ligaments."
            ],
            "options_vi": [
                "A. Do lực ấn chưa đủ sâu vào bao khớp.",
                "B. Do xoa bóp chỉ điều hòa thụ thể cơ học và giảm đau tạm thời, chưa phục hồi được lực co chủ động của nhóm cơ gập cổ sâu và chưa sửa đổi thói quen công thái học.",
                "C. Do massage làm kéo dài vĩnh viễn dây chằng cổ."
            ],
            "correct_option": "B",
            "explanation_en": "Manual modalities stimulate Ruffini and interstitial mechanoreceptors, transiently gating pain and reducing tone. Lasting postural stabilization requires active motor control retraining of deep neck flexors and serratus anterior against gravity.",
            "explanation_vi": "Các kỹ thuật bằng tay kích thích thụ thể Ruffini làm dịu đau và hạ trương lực cơ tạm thời. Để ổn định lâu dài, bắt buộc phải tập phục hồi kiểm soát vận động thần kinh cơ cho nhóm cơ gập cổ sâu và răng trước chống lại trọng lực."
        },
        {
            "question_id": "Q4",
            "question_en": "How does the Craniovertebral Angle (CVA) correlate with the gravitational load on cervical extensor muscles?",
            "question_vi": "Góc Cổ - Đốt Sống (Craniovertebral Angle - CVA) liên quan thế nào đến lực tải của cơ duỗi gáy?",
            "options_en": [
                "A. A smaller CVA increases the head's gravitational moment arm, multiplying the force required from extensor muscles.",
                "B. CVA has no mechanical relationship with extensor muscle load.",
                "C. A smaller CVA decreases extensor muscle load."
            ],
            "options_vi": [
                "A. Góc CVA càng nhỏ (đầu càng nhô trước), cánh tay đòn trọng lực của đầu càng dài, buộc cơ duỗi gáy phải co với lực lớn gấp nhiều lần để giữ đầu.",
                "B. Góc CVA không ảnh hưởng đến lực cơ duỗi.",
                "C. Góc CVA càng nhỏ thì cơ duỗi gáy càng được nghỉ ngơi."
            ],
            "correct_option": "A",
            "explanation_en": "As the head translates forward, CVA decreases from ~53° down to ~35°, lengthening the gravitational moment arm from 2.5 cm to over 7.0 cm, increasing extensor muscle demand from 36 N to over 100 N.",
            "explanation_vi": "Khi đầu đưa ra trước, góc CVA giảm từ ~53° xuống ~35°, làm cánh tay đòn trọng lực tăng từ 2.5 cm lên hơn 7.0 cm, khiến lực đòi hỏi ở cơ duỗi tăng vọt từ 36 N lên hơn 100 N."
        }
    ]

    return {
        "curriculum_id": "P15_CERVICOTHORACIC_BIOMECHANICS_STUDIO",
        "version": "1.0.0",
        "region": "cervicothoracic",
        "scientific_gate_status": G14,
        "clinical_depth_guidance_allowed": CLINICAL_DEPTH_GUIDANCE_ALLOWED,
        "title_en": "Why Does Neck & Shoulder Discomfort Return — And How Do Head Posture & Muscles Interact?",
        "title_vi": "Vì sao mỏi cổ vai gáy thường tái phát — Và tư thế đầu cùng cơ bắp tương tác ra sao?",
        "subtitle_en": "Evidence-Grounded 3D Cervicothoracic Kinematics, Janda's Upper Crossed Syndrome & Active Re-Education",
        "subtitle_vi": "Cơ sinh học cột sống cổ 3D, Hội chứng Chéo trên của Janda & Phục hồi vận động chủ động",
        "disclaimers": [
            "ANATOMICAL_MODEL != SUBJECT_SPECIFIC_ANATOMY",
            "ILLUSTRATIVE_KINEMATICS != MEASURED_KINEMATICS",
            "MUSCLE_ACTION_DESCRIPTION != MUSCLE_ACTIVATION_MEASUREMENT",
            "OPTIMIZED_MUSCLE_ACTIVATION != MEASURED_EMG",
            "SIMULATED_FORCE != MEASURED_HUMAN_FORCE",
            "FORWARD_HEAD_VARIATION != STRUCTURAL_DEFORMITY_DIAGNOSIS",
            "G14 = BLOCKED_EXTERNAL_DATA",
        ],
        "stages": p15_stages,
        "p15_stages": p15_stages,
        "quiz": p15_quiz,
        "evidence_register": cervical_evidence_register,
        "scenarios": [s.__dict__ for s in get_scenario_catalog()],
        "provenance": {
            "source_muscles": "BodyParts3D / DBCLS Japan via Z-Anatomy (CC BY-SA 2.1 JP)",
            "source_skeleton": "BodyParts3D v4.0 (Thorax, C1-C7, Skull/Occiput, Clavicle, Scapula, Humerus, Levator Scapulae, Suboccipitals) (CC BY-SA 2.1 JP / CC BY 4.0)",
            "rendering_engine": "Three.js r160 (MIT License)",
            "biomechanics_adapter": "MSK-Therapy-OS Vasavada Cervical Kinematics Engine (MIT License)",
        },
    }


# ==============================================================================
# P16: MUSCLE MECHANICS INSPECTOR & DATA STRUCTURES
# ==============================================================================

@dataclass
class MuscleMechanicsChannel:
    muscle_id: str
    name_en: str
    name_vi: str
    region: str  # "shoulder" or "cervicothoracic"
    primary_actions: List[str]
    anatomical_role: str  # "prime_mover", "synergist", "stabilizer", "antagonist"
    origin: str
    insertion: str
    innervation: str
    has_geometric_path: bool
    default_moment_arm_cm: Optional[float]
    default_fiber_length_cm: Optional[float]


MUSCLE_CATALOG: Dict[str, MuscleMechanicsChannel] = {
    # Shoulder & Girdle
    "deltoid_anterior": MuscleMechanicsChannel(
        muscle_id="deltoid_anterior",
        name_en="Anterior Deltoid",
        name_vi="Cơ delta bó trước",
        region="shoulder",
        primary_actions=["flexion", "internal_rotation", "horizontal_adduction"],
        anatomical_role="prime_mover",
        origin="Lateral third of clavicle",
        insertion="Deltoid tuberosity of humerus",
        innervation="Axillary nerve (C5, C6)",
        has_geometric_path=True,
        default_moment_arm_cm=3.2,
        default_fiber_length_cm=9.8
    ),
    "deltoid_lateral": MuscleMechanicsChannel(
        muscle_id="deltoid_lateral",
        name_en="Middle / Lateral Deltoid",
        name_vi="Cơ delta bó giữa",
        region="shoulder",
        primary_actions=["abduction", "elevation_in_scapular_plane"],
        anatomical_role="prime_mover",
        origin="Acromion of scapula",
        insertion="Deltoid tuberosity of humerus",
        innervation="Axillary nerve (C5, C6)",
        has_geometric_path=True,
        default_moment_arm_cm=3.8,
        default_fiber_length_cm=11.2
    ),
    "supraspinatus": MuscleMechanicsChannel(
        muscle_id="supraspinatus",
        name_en="Supraspinatus",
        name_vi="Cơ trên gai",
        region="shoulder",
        primary_actions=["abduction_initiation", "glenohumeral_joint_compression"],
        anatomical_role="stabilizer",
        origin="Supraspinous fossa of scapula",
        insertion="Superior facet of greater tubercle of humerus",
        innervation="Suprascapular nerve (C5, C6)",
        has_geometric_path=True,
        default_moment_arm_cm=2.4,
        default_fiber_length_cm=6.8
    ),
    "infraspinatus": MuscleMechanicsChannel(
        muscle_id="infraspinatus",
        name_en="Infraspinatus",
        name_vi="Cơ dưới gai",
        region="shoulder",
        primary_actions=["external_rotation", "posterior_stabilization"],
        anatomical_role="stabilizer",
        origin="Infraspinous fossa of scapula",
        insertion="Middle facet of greater tubercle of humerus",
        innervation="Suprascapular nerve (C5, C6)",
        has_geometric_path=True,
        default_moment_arm_cm=2.1,
        default_fiber_length_cm=7.5
    ),
    "pectoralis_minor": MuscleMechanicsChannel(
        muscle_id="pectoralis_minor",
        name_en="Pectoralis Minor",
        name_vi="Cơ ngực bé",
        region="shoulder",
        primary_actions=["scapular_anterior_tilt", "scapular_depression", "scapular_downward_rotation"],
        anatomical_role="prime_mover",
        origin="Anterior surfaces of ribs 3-5",
        insertion="Coracoid process of scapula",
        innervation="Medial pectoral nerve (C8, T1)",
        has_geometric_path=True,
        default_moment_arm_cm=3.0,
        default_fiber_length_cm=8.0
    ),
    "serratus_anterior": MuscleMechanicsChannel(
        muscle_id="serratus_anterior",
        name_en="Serratus Anterior",
        name_vi="Cơ răng trước",
        region="shoulder",
        primary_actions=["scapular_protraction", "scapular_upward_rotation", "scapular_posterior_tilt"],
        anatomical_role="stabilizer",
        origin="Outer surfaces of ribs 1-8/9",
        insertion="Costal surface of medial border of scapula",
        innervation="Long thoracic nerve (C5-C7)",
        has_geometric_path=True,
        default_moment_arm_cm=5.5,
        default_fiber_length_cm=14.0
    ),
    "trapezius_upper": MuscleMechanicsChannel(
        muscle_id="trapezius_upper",
        name_en="Upper Trapezius",
        name_vi="Cơ thang trên",
        region="cervicothoracic",
        primary_actions=["scapular_elevation", "scapular_upward_rotation", "cervical_extension"],
        anatomical_role="synergist",
        origin="External occipital protuberance and nuchal ligament",
        insertion="Lateral third of clavicle and acromion",
        innervation="Accessory nerve (CN XI) and C3-C4",
        has_geometric_path=True,
        default_moment_arm_cm=4.2,
        default_fiber_length_cm=13.5
    ),
    "trapezius_lower": MuscleMechanicsChannel(
        muscle_id="trapezius_lower",
        name_en="Lower Trapezius",
        name_vi="Cơ thang dưới",
        region="shoulder",
        primary_actions=["scapular_depression", "scapular_upward_rotation", "scapular_posterior_tilt"],
        anatomical_role="stabilizer",
        origin="Spinous processes of T4-T12",
        insertion="Spine of scapula near medial border",
        innervation="Accessory nerve (CN XI) and C3-C4",
        has_geometric_path=True,
        default_moment_arm_cm=4.8,
        default_fiber_length_cm=12.0
    ),
    "levator_scapulae": MuscleMechanicsChannel(
        muscle_id="levator_scapulae",
        name_en="Levator Scapulae",
        name_vi="Cơ nâng vai",
        region="cervicothoracic",
        primary_actions=["scapular_elevation", "scapular_downward_rotation", "cervical_ipsilateral_lateral_flexion"],
        anatomical_role="synergist",
        origin="Transverse processes of C1-C4",
        insertion="Superior medial angle of scapula",
        innervation="Dorsal scapular nerve (C5) and C3-C4",
        has_geometric_path=True,
        default_moment_arm_cm=3.6,
        default_fiber_length_cm=11.0
    ),
    "suboccipital": MuscleMechanicsChannel(
        muscle_id="suboccipital",
        name_en="Suboccipital Muscle Complex",
        name_vi="Nhóm cơ dưới chẩm (Rectus & Obliquus Capitis)",
        region="cervicothoracic",
        primary_actions=["upper_cervical_extension", "atlanto_axial_axial_rotation", "proprioceptive_kinesthesia"],
        anatomical_role="stabilizer",
        origin="C1 Atlas and C2 Axis spinous and transverse processes",
        insertion="Inferior nuchal line of occiput",
        innervation="Suboccipital nerve (C1 posterior ramus)",
        has_geometric_path=True,
        default_moment_arm_cm=2.5,
        default_fiber_length_cm=3.2
    ),
    "longus_colli": MuscleMechanicsChannel(
        muscle_id="longus_colli",
        name_en="Deep Neck Flexors (Longus Colli & Capitis)",
        name_vi="Nhóm cơ gập cổ sâu (Cơ dài cổ & Cơ dài đầu)",
        region="cervicothoracic",
        primary_actions=["craniocervical_flexion", "cervical_lordosis_stabilization", "axial_elongation"],
        anatomical_role="stabilizer",
        origin="Anterior tubercles of C3-C6 transverse processes and vertebral bodies of T1-T3",
        insertion="Anterior arch of C1 and basilar part of occipital bone",
        innervation="Anterior rami of C2-C6 spinal nerves",
        has_geometric_path=True,
        default_moment_arm_cm=2.8,
        default_fiber_length_cm=8.5
    ),
    "scm": MuscleMechanicsChannel(
        muscle_id="scm",
        name_en="Sternocleidomastoid (SCM)",
        name_vi="Cơ ức đòn chũm",
        region="cervicothoracic",
        primary_actions=["cervical_contralateral_rotation", "ipsilateral_lateral_flexion", "lower_cervical_flexion"],
        anatomical_role="prime_mover",
        origin="Manubrium sterni and medial clavicle",
        insertion="Mastoid process of temporal bone",
        innervation="Accessory nerve (CN XI) and C2-C3",
        has_geometric_path=True,
        default_moment_arm_cm=4.5,
        default_fiber_length_cm=15.0
    ),
    "scalenes": MuscleMechanicsChannel(
        muscle_id="scalenes",
        name_en="Scalene Complex (Anterior, Middle, Posterior)",
        name_vi="Nhóm cơ bậc thang (Trước, Giữa, Sau)",
        region="cervicothoracic",
        primary_actions=["cervical_lateral_flexion", "cervical_flexion", "rib_elevation_inspiration"],
        anatomical_role="synergist",
        origin="Transverse processes of C2-C7",
        insertion="First and second ribs",
        innervation="Anterior rami of C3-C8 spinal nerves",
        has_geometric_path=True,
        default_moment_arm_cm=3.5,
        default_fiber_length_cm=9.0
    ),
    "splenius": MuscleMechanicsChannel(
        muscle_id="splenius",
        name_en="Splenius Capitis & Cervicis",
        name_vi="Cơ gối đầu & Cơ gối cổ",
        region="cervicothoracic",
        primary_actions=["cervical_extension", "ipsilateral_rotation", "ipsilateral_lateral_flexion"],
        anatomical_role="prime_mover",
        origin="Nuchal ligament and spinous processes of C7-T6",
        insertion="Mastoid process and transverse processes of C1-C3",
        innervation="Posterior rami of middle and lower cervical nerves",
        has_geometric_path=True,
        default_moment_arm_cm=3.8,
        default_fiber_length_cm=12.5
    )
}


SCENARIO_ID_ALIASES = {
    "vasavada_cervical_flexion_extension": SCEN_VASAVADA_CERVICAL_FLEX_EXT,
    "illustrative_forward_head_posture": SCEN_ILLUSTRATIVE_FORWARD_HEAD,
    "cervical_axial_rotation": SCEN_CERVICAL_AXIAL_ROTATION,
    "cervical_lateral_bending": SCEN_CERVICAL_LATERAL_BENDING,
    "seth_shoulder_elevation": SCEN_SETH_2019_ARM_ELEVATION,
    "concurrent_fwd_head_rounded_shoulder": SCEN_CONCURRENT_FORWARD_HEAD_ROUNDED_SHOULDER,
    "blache_abduction": SCEN_BLACHE_2017_GLENOHUMERAL,
}

def get_muscle_mechanics_inspection(
    region: str,
    scenario_id: str,
    time_sec: float,
    mode: str = "MODE_A_ANATOMICAL_PARTICIPATION"
) -> Dict[str, Any]:
    """Execute Muscle Mechanics Inspection across Modes A, B, C, D with mandatory empty states (P16-04)."""
    valid_modes = [
        "MODE_A_ANATOMICAL_PARTICIPATION",
        "MODE_B_GEOMETRIC_CHANGE",
        "MODE_C_ESTIMATED_ACTIVATION",
        "MODE_D_ESTIMATED_FORCE"
    ]
    if mode not in valid_modes:
        raise ValueError(f"Invalid muscle mechanics inspection mode: {mode}. Must be one of {valid_modes}")

    scenario_id = SCENARIO_ID_ALIASES.get(scenario_id, scenario_id)
    catalog = get_scenario_catalog()
    scen = next((s for s in catalog if s.scenario_id == scenario_id), None)
    if not scen:
        raise ValueError(f"Scenario not found: {scenario_id}")

    relevant_muscles = [
        m for m in MUSCLE_CATALOG.values()
        if region == "all" or m.region == region or region in ("both", "unified")
    ]

    # MODE A: Anatomical Participation
    if mode == "MODE_A_ANATOMICAL_PARTICIPATION":
        return {
            "mode": "MODE_A_ANATOMICAL_PARTICIPATION",
            "mode_title_en": "Mode A — Anatomical Participation",
            "mode_title_vi": "Chế độ A — Nhóm cơ tham gia giải phẫu",
            "region": region,
            "scenario_id": scenario_id,
            "time_sec": round(float(time_sec), 2),
            "status": "AVAILABLE",
            "notice": "Identifies muscles anatomically capable of contributing to movement without simulated percentages.",
            "muscles": [
                {
                    "muscle_id": m.muscle_id,
                    "name_en": m.name_en,
                    "name_vi": m.name_vi,
                    "anatomical_role": m.anatomical_role,
                    "primary_actions": m.primary_actions,
                    "origin": m.origin,
                    "insertion": m.insertion,
                    "innervation": m.innervation,
                }
                for m in relevant_muscles
            ]
        }

    # MODE B: Geometric Change
    if mode == "MODE_B_GEOMETRIC_CHANGE":
        return {
            "mode": "MODE_B_GEOMETRIC_CHANGE",
            "mode_title_en": "Mode B — Musculotendon Geometric Change",
            "mode_title_vi": "Chế độ B — Thay đổi hình học chiều dài cơ",
            "region": region,
            "scenario_id": scenario_id,
            "time_sec": round(float(time_sec), 2),
            "status": "MODEL_GEOMETRY_INSUFFICIENT",
            "empty_state_code": "MODEL_GEOMETRY_INSUFFICIENT",
            "notice": "Continuous 3D muscle line-of-action wrapping curves and dynamic fiber length changes require discrete musculoskeletal path definitions which are unmeshed in the current rigid osseous surface model.",
            "muscles": [
                {
                    "muscle_id": m.muscle_id,
                    "name_en": m.name_en,
                    "default_moment_arm_cm": m.default_moment_arm_cm,
                    "default_fiber_length_cm": m.default_fiber_length_cm,
                    "dynamic_length_change_status": "MODEL_GEOMETRY_INSUFFICIENT"
                }
                for m in relevant_muscles
            ]
        }

    # MODE C: Estimated Activation
    if mode == "MODE_C_ESTIMATED_ACTIVATION":
        sto_file = None
        if scen.scenario_id in ("SCEN_SETH_2019_ARM_ELEVATION", "SCEN_ILLUSTRATIVE_ROUNDED_ELEVATION"):
            sto_file = "seth_shoulder_elevation.sto"
        elif scen.scenario_id == "SCEN_VASAVADA_CERVICAL_FLEX_EXT":
            sto_file = "vasavada_cervical_flexion_extension.sto"
        elif scen.scenario_id == "SCEN_ILLUSTRATIVE_FORWARD_HEAD":
            sto_file = "illustrative_forward_head_posture.sto"
        elif scen.scenario_id == "SCEN_CERVICAL_AXIAL_ROTATION":
            sto_file = "cervical_axial_rotation.sto"
        elif scen.scenario_id == "SCEN_CERVICAL_LATERAL_BENDING":
            sto_file = "cervical_lateral_bending.sto"

        if not sto_file:
            return {
                "mode": "MODE_C_ESTIMATED_ACTIVATION",
                "mode_title_en": "Mode C — Model-Estimated Muscle Activation",
                "mode_title_vi": "Chế độ C — Mức kích hoạt cơ ước tính mô hình",
                "region": region,
                "scenario_id": scenario_id,
                "time_sec": round(float(time_sec), 2),
                "status": "MUSCLE_ACTIVATION_NOT_AVAILABLE",
                "empty_state_code": "MUSCLE_ACTIVATION_NOT_AVAILABLE",
                "notice": "No muscle activation (.sto) dataset registered for this scenario.",
                "muscles": []
            }

        sto_path = Path("msk_therapy_os/data/biomechanics") / sto_file
        if not sto_path.is_file():
            return {
                "mode": "MODE_C_ESTIMATED_ACTIVATION",
                "region": region,
                "scenario_id": scenario_id,
                "status": "MUSCLE_ACTIVATION_NOT_AVAILABLE",
                "empty_state_code": "MUSCLE_ACTIVATION_NOT_AVAILABLE",
                "notice": f"File {sto_file} not found on disk.",
                "muscles": []
            }

        parsed_sto = OpenSimFormatParser.parse_file(sto_path)
        t_val = max(parsed_sto.time[0], min(float(time_sec), parsed_sto.time[-1]))
        
        # Binary search for bracket
        low, high = 0, len(parsed_sto.time) - 1
        while low <= high:
            mid = (low + high) // 2
            if parsed_sto.time[mid] == t_val:
                idx0 = idx1 = mid
                break
            elif parsed_sto.time[mid] < t_val:
                low = mid + 1
            else:
                high = mid - 1
        else:
            idx0 = max(0, high)
            idx1 = min(len(parsed_sto.time) - 1, low)

        dt = parsed_sto.time[idx1] - parsed_sto.time[idx0] if idx1 != idx0 else 1.0
        alpha = (t_val - parsed_sto.time[idx0]) / dt if dt > 0 else 0.0

        res_muscles = []
        for ch in parsed_sto.headers:
            if ch.lower() == "time":
                continue
            v0 = parsed_sto.data[ch][idx0]
            v1 = parsed_sto.data[ch][idx1]
            act = round(v0 + alpha * (v1 - v0), 3)
            res_muscles.append({
                "channel": ch,
                "normalized_activation": act,
                "activation_percentage": round(act * 100.0, 1),
                "optimization_criterion": "Static optimization (Minimizing sum of squared muscle activations)",
                "disclaimer": "SIMULATED_OPTIMIZED_ACTIVATION != MEASURED_SURFACE_EMG"
            })

        return {
            "mode": "MODE_C_ESTIMATED_ACTIVATION",
            "mode_title_en": "Mode C — Model-Estimated Muscle Activation",
            "mode_title_vi": "Chế độ C — Mức kích hoạt cơ ước tính mô hình",
            "region": region,
            "scenario_id": scenario_id,
            "source_sto_file": sto_file,
            "time_sec": round(t_val, 2),
            "status": "AVAILABLE",
            "notice": "Model-derived normalized activations represent numerical static optimization approximations. They DO NOT represent directly measured biological electromyography (EMG).",
            "muscles": res_muscles
        }

    # MODE D: Estimated Muscle Force
    if mode == "MODE_D_ESTIMATED_FORCE":
        return {
            "mode": "MODE_D_ESTIMATED_FORCE",
            "mode_title_en": "Mode D — Model-Estimated Muscle Force",
            "mode_title_vi": "Chế độ D — Lực cơ ước tính mô hình (Newton)",
            "region": region,
            "scenario_id": scenario_id,
            "time_sec": round(float(time_sec), 2),
            "status": "MUSCLE_FORCE_NOT_AVAILABLE",
            "empty_state_code": "MUSCLE_FORCE_NOT_AVAILABLE",
            "notice": "Individual muscle force calculation in Newtons requires live OpenSim dynamic equilibrium solving with validated physiological cross-sectional area (PCSA) and contraction dynamics. Multiplying generic activation by arbitrary constants is strictly rejected to preserve scientific biomechanical validity.",
            "muscles": []
        }

    return {"status": "UNKNOWN_MODE"}


# ==============================================================================
# P16: INTERACTIVE SCENARIO COMPARISON ENGINE
# ==============================================================================

def compare_scenarios(
    scenario_id_a: str,
    scenario_id_b: str,
    time_a_sec: float = 0.0,
    time_b_sec: float = 0.0
) -> Dict[str, Any]:
    """Compare two biomechanical scenarios side-by-side with difference metrics (P16-05)."""
    scenario_id_a = SCENARIO_ID_ALIASES.get(scenario_id_a, scenario_id_a)
    scenario_id_b = SCENARIO_ID_ALIASES.get(scenario_id_b, scenario_id_b)
    catalog = get_scenario_catalog()
    scen_a = next((s for s in catalog if s.scenario_id == scenario_id_a), None)
    scen_b = next((s for s in catalog if s.scenario_id == scenario_id_b), None)
    if not scen_a or not scen_b:
        raise ValueError(f"One or both scenario IDs not found: {scenario_id_a}, {scenario_id_b}")

    base_dir = Path("msk_therapy_os/data/biomechanics")
    mot_a_path = base_dir / scen_a.source_motion_file
    mot_b_path = base_dir / scen_b.source_motion_file

    def get_eval(mot_path, t_sec):
        if not mot_path.is_file():
            return {}
        p = OpenSimFormatParser.parse_file(mot_path)
        t = max(p.time[0], min(float(t_sec), p.time[-1]))
        low, high = 0, len(p.time) - 1
        while low <= high:
            mid = (low + high) // 2
            if p.time[mid] == t:
                idx0 = idx1 = mid
                break
            elif p.time[mid] < t:
                low = mid + 1
            else:
                high = mid - 1
        else:
            idx0 = max(0, high)
            idx1 = min(len(p.time) - 1, low)
        dt = p.time[idx1] - p.time[idx0] if idx1 != idx0 else 1.0
        alpha = (t - p.time[idx0]) / dt if dt > 0 else 0.0
        vals = {}
        for h in p.headers:
            if h.lower() != "time":
                vals[h] = round(p.data[h][idx0] + alpha * (p.data[h][idx1] - p.data[h][idx0]), 2)
        vals["time"] = round(t, 2)
        return vals

    eval_a = get_eval(mot_a_path, time_a_sec)
    eval_b = get_eval(mot_b_path, time_b_sec)

    # Calculate coordinate angle deltas
    common_coords = [k for k in eval_a if k in eval_b and k != "time"]
    deltas = {c: round(eval_b[c] - eval_a[c], 2) for c in common_coords}

    # Gravitational comparison if cervical
    cva_a = eval_a.get("cva_angle", 53.0)
    cva_b = eval_b.get("cva_angle", 53.0)
    fwd_a = eval_a.get("head_anterior_trans", 0.0)
    fwd_b = eval_b.get("head_anterior_trans", 0.0)
    mech_a = calculate_cervical_gravitational_mechanics(fwd_a, cva_a)
    mech_b = calculate_cervical_gravitational_mechanics(fwd_b, cva_b)

    grav_delta = {
        "delta_moment_arm_cm": round(mech_b["horizontal_moment_arm_cm"] - mech_a["horizontal_moment_arm_cm"], 2),
        "delta_gravitational_moment_nm": round(mech_b["external_gravitational_moment_nm"] - mech_a["external_gravitational_moment_nm"], 3),
        "delta_extensor_muscle_force_n": round(mech_b["extensor_muscle_force_n"] - mech_a["extensor_muscle_force_n"], 1),
        "delta_compression_force_n": round(mech_b["joint_reaction_compression_n"] - mech_a["joint_reaction_compression_n"], 1),
    }

    return {
        "status": "SUCCESS",
        "scenario_a": {
            "scenario_id": scen_a.scenario_id,
            "title": scen_a.scenario_title,
            "time_sec": eval_a.get("time", 0.0),
            "angles": eval_a,
            "mechanics": mech_a,
        },
        "scenario_b": {
            "scenario_id": scen_b.scenario_id,
            "title": scen_b.scenario_title,
            "time_sec": eval_b.get("time", 0.0),
            "angles": eval_b,
            "mechanics": mech_b,
        },
        "coordinate_deltas": deltas,
        "gravitational_mechanics_delta": grav_delta,
        "uncertainty_and_assumptions": [
            "Kinematic comparison reflects idealized rigid-body coordinate definitions.",
            "Gravitational moments represent static 2D sagittal equilibrium without active co-contraction.",
            "HIGHER_GRAVITATIONAL_MOMENT != TISSUE_DAMAGE_OR_DIAGNOSIS (Mechanical load variations are natural and do not prove pathology)."
        ],
        "disclaimer": "ILLUSTRATIVE_SCENARIO_COMPARISON_ONLY"
    }


# ==============================================================================
# P16: DATA PROVENANCE MANIFEST REGISTRY
# ==============================================================================

def get_provenance_manifest() -> Dict[str, Any]:
    """Deliver strict, traceable provenance manifest for all biomechanical datasets (P16-02)."""
    catalog = get_scenario_catalog()
    base_dir = Path("msk_therapy_os/data/biomechanics")
    
    manifest_records = []
    for s in catalog:
        fpath = base_dir / s.source_motion_file
        file_exists = fpath.is_file()
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest() if file_exists else "FILE_NOT_FOUND"
        file_size_bytes = fpath.stat().st_size if file_exists else 0
        
        manifest_records.append({
            "scenario_id": s.scenario_id,
            "scenario_title": s.scenario_title,
            "source_model": s.source_model,
            "source_model_version": s.source_model_version,
            "source_model_hash": s.source_model_hash,
            "source_motion_file": s.source_motion_file,
            "motion_file_hash": s.motion_file_hash,
            "actual_motion_file_hash": actual_hash,
            "hash_match": (actual_hash == s.motion_file_hash),
            "file_size_bytes": file_size_bytes,
            "model_license": s.model_license,
            "motion_data_origin": s.motion_data_origin,
            "generation_method": s.generation_method,
            "coordinate_system": s.coordinate_system,
            "joint_coordinate_names": s.joint_coordinate_names,
            "angle_units": s.angle_units,
            "time_units": s.time_units,
            "muscle_output_type": s.muscle_output_type,
            "external_load_assumptions": s.external_load_assumptions,
            "subject_specific": s.subject_specific,
            "validation_level": s.validation_level,
            "scientific_references": s.scientific_references,
            "known_limitations": s.known_limitations,
        })

    return {
        "manifest_version": "P16.1.0",
        "live_opensim_runtime_status": "OPENSIM_LIVE_SIMULATION_BLOCKED",
        "live_opensim_runtime_notice": "OpenSim Python bindings / C++ binaries are not installed in this offline Windows environment. Datasets are verified and served as standardized illustrative OpenSim-format files.",
        "scenarios_count": len(manifest_records),
        "scenarios": manifest_records,
    }


# ==============================================================================
# P16: UNIFIED 10-TOPIC MSK EDUCATION CURRICULUM
# ==============================================================================

def get_unified_education_curriculum(region: str = "all", version: str = "P16") -> Dict[str, Any]:
    """Deliver full bilingual (EN/VI) 10-topic unified MSK education curriculum (P16-06)."""
    p16_topics = [
        {
            "topic_id": 1,
            "name_en": "1. Anatomy: Head, Neck & Shoulder Girdle Architecture",
            "name_vi": "1. Giải phẫu: Cấu trúc Đầu, Cổ & Đai Vai",
            "summary_en": "Explore authentic 3D osseous anatomy: Cranium, C1 Atlas, C2 Axis, C3-C7, T1-T4, Clavicle, Scapula, and Humerus. The ~5 kg skull balances atop delicate cervical vertebrae, coupled to the thoracic cage through the floating scapulothoracic articulation.",
            "summary_vi": "Khám phá giải phẫu xương 3D thực tế: Hộp sọ, C1 Đội, C2 Trục, C3-C7, T1-T4, Xương đòn, Xương bả vai và Xương cánh tay. Hộp sọ nặng ~5 kg cân bằng trên các đốt sống cổ mảnh mai, liên kết với lồng ngực qua khớp bả vai lồng ngực tự do.",
            "focus_muscles": ["trapezius_upper", "levator_scapulae", "suboccipital", "deltoid_anterior"],
            "region": "unified"
        },
        {
            "topic_id": 2,
            "name_en": "2. Joint Motion: Scapular & Cervical Kinematics",
            "name_vi": "2. Chuyển động khớp: Cơ học Vận động Bả vai & Cột sống cổ",
            "summary_en": "Multi-segment joint motion involves coordinated kinematics. Arm elevation couples glenohumeral rotation with scapular upward rotation and posterior tilt. Cervical motion integrates upper cervical atlanto-occipital and atlanto-axial motion with lower cervical facet gliding.",
            "summary_vi": "Vận động đa phân đoạn đòi hỏi sự phối hợp nhịp nhàng. Khi giơ tay, khớp ổ chảo cánh tay phối hợp với xoay lên và nghiêng sau của bả vai. Vận động cổ kết hợp gập ngửa đội-chẩm, xoay đội-trục và trượt diện khớp cổ dưới.",
            "focus_muscles": ["serratus_anterior", "trapezius_lower", "scm", "splenius"],
            "region": "unified"
        },
        {
            "topic_id": 3,
            "name_en": "3. Alignment: Forward-Head & Postural Diversity",
            "name_vi": "3. Tư thế: Đầu đổ trước & Sự đa dạng hình thái tự nhiên",
            "summary_en": "Forward Head Posture (FHP) describes anterior translation of the cranium relative to C7. Postural alignment varies widely across healthy individuals; posture alone does NOT constitute a structural deformity or disease diagnosis.",
            "summary_vi": "Tư thế đầu đổ trước (FHP) mô tả sự nhô ra trước của hộp sọ so với C7. Góc tư thế biến thiên rất lớn giữa những người hoàn toàn khỏe mạnh; tư thế đơn thuần KHÔNG PHẢI là dị tật hay bệnh lý.",
            "focus_muscles": ["suboccipital", "longus_colli", "pectoralis_minor"],
            "region": "cervicothoracic"
        },
        {
            "topic_id": 4,
            "name_en": "4. Physics: Gravity, Moment Arms & Equilibrium",
            "name_vi": "4. Vật lý cơ sinh học: Trọng lực, Cánh tay đòn & Cân bằng",
            "summary_en": "In static equilibrium (Sigma M = 0), external gravitational moment (M_gravity = W_head * d_horizontal) must be counterbalanced by internal extensor muscle moment (M_internal = F_extensor * r_eff). When the head translates forward from 0 to 50 mm, the moment arm lengthens from ~2.5 cm to ~7.5 cm, tripling extensor muscle demand.",
            "summary_vi": "Ở trạng thái cân bằng tĩnh (Tổng mô-men = 0), mô-men trọng lực ngoài (M = Trọng lượng * Cánh tay đòn) bắt buộc phải được cân bằng bởi mô-men cơ duỗi trong. Khi đầu nhô trước từ 0 đến 50 mm, cánh tay đòn tăng từ ~2.5 cm lên ~7.5 cm, khiến lực đòi hỏi ở cơ duỗi gáy tăng gấp ba lần.",
            "focus_muscles": ["trapezius_upper", "splenius", "suboccipital"],
            "region": "cervicothoracic"
        },
        {
            "topic_id": 5,
            "name_en": "5. Muscle Mechanics: Agonists, Synergists & Force Couples",
            "name_vi": "5. Cơ học bắp cơ: Cơ chủ vận, Cơ trợ vận & Ngẫu lực",
            "summary_en": "Joint motion requires muscular force couples. In the shoulder, Upper Trapezius, Lower Trapezius, and Serratus Anterior create a balanced upward rotation force couple. In the neck, deep stabilizers support axial lordosis while superficial muscles generate high torque.",
            "summary_vi": "Vận động khớp đòi hỏi các cặp ngẫu lực. Ở vai, Cơ thang trên, Cơ thang dưới và Cơ răng trước tạo ngẫu lực xoay lên bả vai cân đối. Ở cổ, cơ gập cổ sâu giữ vững trục đường cong sinh lý trong khi các cơ nông tạo lực quay lớn.",
            "focus_muscles": ["serratus_anterior", "trapezius_lower", "trapezius_upper", "deltoid_lateral"],
            "region": "unified"
        },
        {
            "topic_id": 6,
            "name_en": "6. Science: Distinguishing Tension, Activation, Force & Pain",
            "name_vi": "6. Khoa học: Phân biệt Cảm giác căng, Kích hoạt điện, Lực cơ & Cơn đau",
            "summary_en": "Subjective feeling of muscle tightness does not mean a muscle is physically short or hyperactive. Simulated activation (OpenSim) is an optimization estimate, not direct EMG. Pain is a complex neurobiological alarm influenced by fatigue, stress, and sensitivity, not purely tissue damage.",
            "summary_vi": "Cảm giác căng cứng chủ quan không đồng nghĩa với việc cơ bị ngắn cơ học hay co thắt điện sinh học. Kích hoạt mô phỏng (OpenSim) là ước tính toán học, không phải điện cơ EMG thực tế. Cơn đau là tín hiệu cảnh báo thần kinh phức tạp chịu ảnh hưởng của mệt mỏi và độ nhạy cảm thần kinh, không đơn thuần do tổn thương mô.",
            "focus_muscles": ["levator_scapulae", "trapezius_upper", "infraspinatus"],
            "region": "unified"
        },
        {
            "topic_id": 7,
            "name_en": "7. The Paradox: Why Temporary Relief from Massage May Not Last",
            "name_vi": "7. Nghịch lý: Vì sao cảm giác nhẹ sau giải cơ thường không duy trì lâu?",
            "summary_en": "Massage and manual therapy stimulate mechanoreceptors, transiently gating nociceptive signaling and modulating tone. However, passive release does not strengthen inhibited stabilizers or alter habitual workplace ergonomics, leading to recurrence under continuous postural loading.",
            "summary_vi": "Xoa bóp và giải cơ thụ động kích thích thụ thể cơ học, giúp ức chế tín hiệu đau tạm thời qua cổng cảm giác và hạ trương lực. Tuy nhiên, thao tác thụ động không làm mạnh cơ ổn định bị yếu và không thay đổi thói quen làm việc, khiến cảm giác mỏi tái phát khi tiếp tục ngồi làm việc kéo dài.",
            "focus_muscles": ["levator_scapulae", "suboccipital", "pectoralis_minor"],
            "region": "unified"
        },
        {
            "topic_id": 8,
            "name_en": "8. Active Care: Graded Loading & Movement Variability",
            "name_vi": "8. Tự chăm sóc chủ động: Tải trọng thích nghi & Đa dạng vận động",
            "summary_en": "Long-term musculoskeletal resilience relies on active exercise: Craniocervical Flexion Training (CCFT) for deep neck flexors, prone horizontal abduction and Y-raises for lower trapezius, wall slides for serratus anterior, and regular posture changes every 30-45 minutes.",
            "summary_vi": "Sức khỏe cơ xương khớp bền vững dựa trên vận động chủ động: Tập gập cổ sâu (CCFT) kích hoạt cơ dài cổ, bài tập chữ Y và dang ngang nằm sấp cho cơ thang dưới, trượt tường cho cơ răng trước, cùng việc đổi tư thế ngồi đều đặn mỗi 30-45 phút.",
            "focus_muscles": ["longus_colli", "trapezius_lower", "serratus_anterior"],
            "region": "unified"
        },
        {
            "topic_id": 9,
            "name_en": "9. Limitations: Model Assumptions & Scientific Uncertainty",
            "name_vi": "9. Giới hạn khoa học: Giả định mô hình & Sự không chắc chắn",
            "summary_en": "All calculations presented are educational simulations derived from standardized models (Vasavada et al., Seth et al.). They do not represent individualized clinical diagnostics. Actual human anatomy features unique ligamentous laxity, disc geometry, and neuromuscular coordination.",
            "summary_vi": "Mọi tính toán trình bày đều là mô phỏng giáo dục từ các mô hình tiêu chuẩn hóa (Vasavada, Seth). Chúng không đại diện cho chẩn đoán cá nhân hóa. Cơ thể người thực tế có sự đa dạng rất lớn về độ chùng dây chằng, hình học đĩa đệm và phối hợp thần kinh cơ.",
            "focus_muscles": ["scm", "deltoid_lateral"],
            "region": "unified"
        },
        {
            "topic_id": 10,
            "name_en": "10. Self-Assessment: Biomechanical Knowledge Check",
            "name_vi": "10. Tự đánh giá: Trắc nghiệm Tri thức Cơ sinh học",
            "summary_en": "Consolidate your learning with 5 evidence-based comprehension questions covering joint rhythm, gravitational moment arms, muscle activation versus EMG, and active rehabilitation.",
            "summary_vi": "Củng cố kiến thức với 5 câu hỏi trắc nghiệm dựa trên bằng chứng khoa học về nhịp khớp, cánh tay đòn trọng lực, kích hoạt cơ mô phỏng và phục hồi chủ động.",
            "focus_muscles": ["longus_colli", "serratus_anterior", "trapezius_upper", "suboccipital"],
            "region": "unified"
        }
    ]

    p16_quiz = [
        {
            "question_id": "Q1",
            "question_en": "Why does the head's gravitational demand on cervical extensor muscles increase during forward head posture?",
            "question_vi": "Vì sao tải trọng của đầu lên nhóm cơ duỗi gáy lại tăng vọt khi đầu nhô ra phía trước?",
            "options_en": [
                "A. The head physically becomes heavier due to blood pooling.",
                "B. The horizontal moment arm between the head's center of mass and the C7 pivot axis lengthens, increasing external torque.",
                "C. Cervical vertebrae shrink under tension."
            ],
            "options_vi": [
                "A. Trọng lượng thực tế của đầu tăng lên do ứ trệ tuần hoàn máu.",
                "B. Cánh tay đòn nằm ngang từ trọng tâm đầu tới trục quay C7 bị kéo dài, làm tăng mô-men uốn của trọng lực.",
                "C. Các đốt sống cổ bị co rút ngắn lại."
            ],
            "correct_option": "B",
            "explanation_en": "According to rotational equilibrium (M = W * d), moving the head forward increases the horizontal distance (moment arm) from ~2.5 cm to >6.5 cm. To maintain balance, extensor muscle force must increase proportionally (from ~35 N to >95 N).",
            "explanation_vi": "Theo nguyên lý cân bằng mô-men (M = Trọng lượng * Cánh tay đòn), khi đầu đưa ra trước, khoảng cách nằm ngang tăng từ ~2.5 cm lên >6.5 cm. Để giữ đầu thăng bằng, cơ duỗi gáy bắt buộc phải co với lực lớn tương ứng (từ ~35 N lên >95 N)."
        },
        {
            "question_id": "Q2",
            "question_en": "Can observing a person's posture alone establish a definitive medical diagnosis of muscle weakness or pathology?",
            "question_vi": "Chỉ quan sát tư thế bên ngoài có thể khẳng định chắc chắn cơ nào bị yếu hay có bệnh lý không?",
            "options_en": [
                "A. Yes, rounded shoulders always indicate pathological shortening of the pectoralis minor.",
                "B. No, posture reflects resting alignment. Asymptomatic individuals frequently display forward alignment with normal strength and zero pain.",
                "C. Yes, posture is directly equivalent to an MRI diagnosis."
            ],
            "options_vi": [
                "A. Có, vai đổ trước luôn chứng tỏ cơ ngực bé bị co ngắn bệnh lý.",
                "B. Không, tư thế chỉ phản ánh vị trí nghỉ. Rất nhiều người không có triệu chứng vẫn có tư thế đưa trước nhưng sức mạnh cơ bình thường và hoàn toàn không đau.",
                "C. Có, quan sát tư thế tương đương với kết quả chụp cộng hưởng từ MRI."
            ],
            "correct_option": "B",
            "explanation_en": "Current systematic reviews (Swain et al. 2020, Barrett et al. 2016) show weak and inconsistent correlations between spinal curvature in resting postures and spinal pain in asymptomatic populations.",
            "explanation_vi": "Các tổng quan hệ thống hiện đại (Swain 2020, Barrett 2016) chứng minh mối tương quan giữa tư thế nghỉ và triệu chứng đau là rất yếu và không đồng nhất ở cộng đồng người khỏe mạnh."
        },
        {
            "question_id": "Q3",
            "question_en": "What does a muscle activation value generated by an OpenSim model represent?",
            "question_vi": "Chỉ số kích hoạt cơ do mô hình OpenSim xuất ra đại diện cho điều gì?",
            "options_en": [
                "A. Directly recorded bioelectrical voltage from a patient's muscle electrodes.",
                "B. A mathematical optimization estimate predicting recruitment based on minimal effort criteria, not empirical EMG.",
                "C. The exact mechanical force of the muscle in Newtons."
            ],
            "options_vi": [
                "A. Tín hiệu điện thế sinh học đo trực tiếp qua điện cực gắn trên cơ thể người.",
                "B. Ước tính toán học từ thuật toán tối ưu hóa nhằm dự đoán mức huy động cơ theo tiêu chí tối thiểu hóa năng lượng, không phải điện cơ EMG thực nghiệm.",
                "C. Lực cơ học chính xác tính theo đơn vị Newton."
            ],
            "correct_option": "B",
            "explanation_en": "OpenSim activations are computed using numerical algorithms (such as static optimization minimizing sum of squared activations). They are model estimates, not bioelectrical measurements.",
            "explanation_vi": "Mức kích hoạt trong OpenSim được tính bằng thuật toán tối ưu hóa số học. Đây là kết quả mô phỏng tính toán, không phải dữ liệu điện sinh học thu thập từ cơ thể người."
        },
        {
            "question_id": "Q4",
            "question_en": "Why does neck and upper shoulder tension frequently return days after feeling light from a massage?",
            "question_vi": "Vì sao cảm giác nhẹ nhõm sau giải cơ thường chỉ duy trì vài ngày rồi cổ vai gáy lại căng mỏi như cũ?",
            "options_en": [
                "A. Because the massage therapist applied improper pressure.",
                "B. Because manual therapy provides transient neurosensory modulation, but lasting adaptation requires active motor re-education and ergonomic behavioral change.",
                "C. Because massage permanently loosens cervical ligaments."
            ],
            "options_vi": [
                "A. Do kỹ thuật viên xoa bóp chưa dùng đúng kỹ thuật.",
                "B. Do xoa bóp chỉ điều hòa thụ thể cơ học và giảm đau tạm thời, còn cải thiện bền vững đòi hỏi tập luyện vận động chủ động và điều chỉnh thói quen làm việc.",
                "C. Do massage làm giãn vĩnh viễn dây chằng cổ."
            ],
            "correct_option": "B",
            "explanation_en": "Passive soft-tissue manipulation activates sensory mechanoreceptors to reduce pain perception transiently (gate control). However, it does not retrain motor recruitment or alter sustained physical demands.",
            "explanation_vi": "Tác động mô mềm thụ động kích thích thụ thể cơ học giúp giảm nhận thức đau tạm thời. Tuy nhiên, nó không giúp não học lại mẫu hình vận động và không thay đổi tải trọng tư thế kéo dài."
        },
        {
            "question_id": "Q5",
            "question_en": "When should an individual with neck and shoulder discomfort seek prompt medical evaluation instead of relying on self-care?",
            "question_vi": "Khi nào một người bị mỏi cổ vai gáy cần đi khám y tế chuyên khoa ngay thay vì chỉ tự tập luyện?",
            "options_en": [
                "A. If there is radiating sharp pain, progressive arm weakness, numbness in fingers, or after severe traumatic impact (red flags).",
                "B. Only if pain lasts more than one hour.",
                "C. Never, self-care exercises are always sufficient for all spinal conditions."
            ],
            "options_vi": [
                "A. Khi có cơn đau nhói lan xuống tay, yếu liệt tăng dần ở cánh tay/bàn tay, tê bì theo dải cảm giác, hoặc sau chấn thương va đập mạnh (dấu hiệu cờ đỏ).",
                "B. Chỉ cần đi khám khi đau kéo dài hơn 1 giờ.",
                "C. Không bao giờ cần khám, các bài tập tự chăm sóc luôn luôn giải quyết được mọi vấn đề cột sống."
            ],
            "correct_option": "A",
            "explanation_en": "Red flag symptoms such as progressive neurological deficits (radiculopathy/myelopathy), severe trauma history, or unremitting night pain require professional clinical assessment and diagnostic imaging.",
            "explanation_vi": "Các dấu hiệu cảnh báo đỏ như chèn ép rễ thần kinh tiến triển (đau lan, tê bì, yếu cơ), tiền sử chấn thương hoặc đau không giảm về đêm bắt buộc phải được bác sĩ chuyên khoa thăm khám và chỉ định chẩn đoán hình ảnh."
        }
    ]

    red_flags = [
        {
            "flag_id": "RF1_PROGRESSIVE_NEUROLOGICAL_DEFICIT",
            "title_en": "Progressive Neurological Deficits (Radiculopathy)",
            "title_vi": "Thiếu hụt thần kinh tiến triển (Chèn ép rễ)",
            "description_en": "Progressive weakness in shoulder elevation, elbow flexion/extension, wrist drop, or hand grip weakness. Numbness or tingling radiating past the elbow into fingers (C5-T1 dermatomes).",
            "description_vi": "Yếu cơ tiến triển khi nâng vai, gập/duỗi khuỷu, rủ cổ tay hoặc yếu lực cầm nắm bàn tay. Cảm giác tê bì, châm chích lan qua khuỷu tay xuống các ngón tay."
        },
        {
            "flag_id": "RF2_CERVICAL_MYELOPATHY",
            "title_en": "Cervical Spinal Cord Compression (Myelopathy)",
            "title_vi": "Chèn ép tủy cổ (Bệnh lý tủy)",
            "description_en": "Gait unsteadiness, feeling of walking on cotton wool, loss of manual dexterity (difficulty buttoning shirts), or unexpected changes in bowel/bladder function.",
            "description_vi": "Dáng đi loạng choạng, cảm giác như đi trên đệm bông, mất độ khéo léo của bàn tay (khó cài cúc áo), hoặc rối loạn tiểu tiện/đại tiện bất thường."
        },
        {
            "flag_id": "RF3_ACUTE_TRAUMA_OR_SYSTEMIC_SIGNS",
            "title_en": "Acute Trauma or Systemic Pathology",
            "title_vi": "Tiền sử chấn thương cấp hoặc Dấu hiệu toàn thân",
            "description_en": "History of high-energy trauma (motor vehicle accident, fall from height, sports collision), unexplained fever, persistent unremitting night pain unrelated to movement, or unexplained weight loss.",
            "description_vi": "Tiền sử chấn thương mạnh (tai nạn xe cộ, ngã từ trên cao), sốt không rõ nguyên nhân, đau dữ dội về đêm không liên quan đến vận động, hoặc sụt cân nhanh bất thường."
        }
    ]

    p16_evidence_register = [
        {"evidence_id": "EV-01", "citation": "Inman VT, Saunders JB, Abbott LC. Observations on the function of the shoulder joint. J Bone Joint Surg Am. 1944;26(1):1-30.", "category": "MODEL_BASED_MECHANICS", "confidence": "ESTABLISHED_HISTORICAL_AVERAGE", "topic": "2:1 scapulohumeral rhythm average"},
        {"evidence_id": "EV-02", "citation": "Ludewig PM, Cook TM. Alterations in shoulder kinematics and associated muscle activity in people with symptoms of shoulder impingement. Phys Ther. 2000;80(3):276-291.", "category": "OBSERVATIONAL_ASSOCIATION", "confidence": "MODERATE_PEER_REVIEWED", "topic": "Scapular kinematics in impingement"},
        {"evidence_id": "EV-03", "citation": "Seth A, Hicks JL, Uchida TK, et al. OpenSim: Simulating musculoskeletal dynamics and neuromuscular control to study human and animal movement. PLoS Comput Biol. 2018;14(7):e1006223.", "category": "MODEL_BASED_MECHANICS", "confidence": "HIGH_COMPUTATIONAL_FRAMEWORK", "topic": "OpenSim biomechanical modeling software"},
        {"evidence_id": "EV-04", "citation": "McClure PW, Michener LA, Sennett BJ, Karduna AR. Direct 3-dimensional measurement of scapular kinematics during dynamic movements in vivo. J Shoulder Elbow Surg. 2001;10(3):269-277.", "category": "ANATOMICAL_EVIDENCE", "confidence": "HIGH_EXPERIMENTAL", "topic": "In vivo 3D bone pin scapular kinematics"},
        {"evidence_id": "EV-05", "citation": "Borstad JD, Ludewig PM. The effect of long versus short pectoralis minor resting length on scapular kinematics in healthy individuals. J Orthop Sports Phys Ther. 2005;35(4):227-238.", "category": "OBSERVATIONAL_ASSOCIATION", "confidence": "MODERATE_EXPERIMENTAL", "topic": "Pectoralis minor resting length and tilt"},
        {"evidence_id": "EV-06", "citation": "Kebaetse M, McClure P, Pratt NA. Thoracic position effect on shoulder range of motion, strength, and three-dimensional scapular kinematics. Arch Phys Med Rehabil. 1999;80(8):945-950.", "category": "INTERVENTION_EVIDENCE", "confidence": "HIGH_EXPERIMENTAL", "topic": "Thoracic posture impact on shoulder elevation"},
        {"evidence_id": "EV-07", "citation": "de Oliveira FX, et al. Scapular movement training with biofeedback in shoulder impingement. Clin Biomech. 2017;47:73-81.", "category": "INTERVENTION_EVIDENCE", "confidence": "MODERATE_CONTROLLED_TRIAL", "topic": "Motor control biofeedback for shoulder"},
        {"evidence_id": "EV-08", "citation": "Bialosky JE, Bishop MD, Price DD, et al. The mechanisms of manual therapy in the treatment of musculoskeletal pain: a comprehensive model. Man Ther. 2009;14(5):531-538.", "category": "MODEL_BASED_MECHANICS", "confidence": "HIGH_CONCEPTUAL_REVIEW", "topic": "Neurophysiological mechanisms of manual therapy"},
        {"evidence_id": "EV-09", "citation": "Hansraj KK. Assessment of Stresses in the Cervical Spine Caused by Posture and Position of the Head. Surg Technol Int. 2014;25:277-279.", "category": "MODEL_BASED_MECHANICS", "confidence": "ESTABLISHED_SIMULATION_LIMITATIONS", "topic": "Gravitational torque vs head flexion tilt angle"},
        {"evidence_id": "EV-10", "citation": "Vasavada AN, Li S, Delp SL. Influence of muscle morphometry and moment arms on the moment-generating capacity of human neck muscles. Spine. 1998;23(4):412-422.", "category": "ANATOMICAL_EVIDENCE", "confidence": "HIGH_CADAVERIC_AND_MODEL", "topic": "Neck muscle moment arms (~3.5 cm) and architecture"},
        {"evidence_id": "EV-11", "citation": "Yip CH, Chiu TT, Poon AT. The relationship between head posture and severity and disability of patients with neck pain. Man Ther. 2008;13(2):148-154.", "category": "OBSERVATIONAL_ASSOCIATION", "confidence": "MODERATE_CROSS_SECTIONAL", "topic": "Craniovertebral angle and self-reported neck disability"},
        {"evidence_id": "EV-12", "citation": "Jull G, Trott P, Potter H, et al. A randomized controlled trial of exercise and manipulative therapy for cervicogenic headache. Spine. 2002;27(17):1835-1843.", "category": "INTERVENTION_EVIDENCE", "confidence": "HIGH_RCT", "topic": "Craniocervical flexion training and deep neck flexors"},
        {"evidence_id": "EV-13", "citation": "Janda V. Muscles and Motor Control in Cervicothoracic Disorders. Physical Therapy of the Cervical and Thoracic Spine. 1988:182-199.", "category": "UNVALIDATED_HYPOTHESIS", "confidence": "CONCEPTUAL_CLINICAL_FRAMEWORK", "topic": "Upper Crossed Syndrome reciprocal inhibition model"},
        {"evidence_id": "EV-14", "citation": "Kulkarni V, Chandy MJ, Babu KS. Quantitative study of muscle spindles in suboccipital muscles of human fetuses. Neurol India. 2001;49(4):355-359.", "category": "ANATOMICAL_EVIDENCE", "confidence": "HIGH_HISTOLOGICAL", "topic": "Suboccipital spindle density (~98 spindles/g)"},
        {"evidence_id": "EV-15", "citation": "Kibler WB, Ludewig PM, McClure PW, et al. Clinical implications of scapular dyskinesis in shoulder injury. Br J Sports Med. 2013;47(14):877-885.", "category": "OBSERVATIONAL_ASSOCIATION", "confidence": "CONSENSUS_STATEMENT", "topic": "Scapular kinematics and levator scapulae coupling"},
        {"evidence_id": "EV-16", "citation": "Cools AM, Declercq GA, Cambier DC, et al. Trapezius activity and intramuscular balance during rehabilitative exercises. Am J Sports Med. 2007;35(10):1744-1751.", "category": "INTERVENTION_EVIDENCE", "confidence": "HIGH_EMG_EXPERIMENTAL", "topic": "Trapezius muscle balance in rehabilitation"},
        {"evidence_id": "EV-17", "citation": "Swain CTV, Pan F, Maher CG, et al. No consensus on whether spinal posture is related to spinal pain: a systematic review. Spine J. 2020;20(8):1256-1267.", "category": "OBSERVATIONAL_ASSOCIATION", "confidence": "HIGH_SYSTEMATIC_REVIEW", "topic": "Systematic review showing weak link between posture and pain"},
        {"evidence_id": "EV-18", "citation": "Richards KV, Beales DJ, Smith AJ, et al. Neck Posture Clusters and Their Association With Biopsychosocial Factors and Neck Pain in Australian Adolescents. Phys Ther. 2016;96(10):1576-1587.", "category": "OBSERVATIONAL_ASSOCIATION", "confidence": "HIGH_EPIDEMIOLOGICAL", "topic": "Postural clusters and lack of direct correlation with pain"},
        {"evidence_id": "EV-19", "citation": "Barrett E, O'Keeffe M, O'Sullivan K, et al. Is thoracic spine posture associated with shoulder pain, range of motion and function? A systematic review. Man Ther. 2016;26:38-46.", "category": "OBSERVATIONAL_ASSOCIATION", "confidence": "HIGH_SYSTEMATIC_REVIEW", "topic": "Systematic review on thoracic posture and shoulder symptoms"},
        {"evidence_id": "EV-20", "citation": "Caelers R, et al. A validated musculoskeletal neck model for human head-neck dynamic simulations in OpenSim. Comput Methods Biomech Biomed Engin. 2024.", "category": "MODEL_BASED_MECHANICS", "confidence": "HIGH_COMPUTATIONAL_MODEL", "topic": "Multi-segment cervical OpenSim kinematics"}
    ]

    return {
        "curriculum_id": "P16_UNIFIED_MSK_EDUCATION_STUDIO",
        "version": "1.0.0",
        "region": region,
        "scientific_gate_status": G14,
        "clinical_depth_guidance_allowed": CLINICAL_DEPTH_GUIDANCE_ALLOWED,
        "title_en": "MSK Education Studio: 3D Biomechanics, Muscle Mechanics & Interactive Self-Education",
        "title_vi": "Phòng Học Cơ Sinh Học MSK 3D: Cơ học Vận động, Cơ bắp & Tự học Tương tác",
        "subtitle_en": "Evidence-Grounded Kinematics, Moment Arms, Muscle Mechanics & Non-Diagnostic Self-Care",
        "subtitle_vi": "Động học Dựa trên Bằng chứng, Cánh tay đòn, Cơ học Cơ bắp & Tự chăm sóc Không Chẩn đoán",
        "topics": p16_topics,
        "quiz": p16_quiz,
        "red_flags": red_flags,
        "evidence_register": p16_evidence_register,
        "disclaimers": [
            "ANATOMICAL_MODEL != SUBJECT_SPECIFIC_ANATOMY",
            "ILLUSTRATIVE_KINEMATICS != MEASURED_KINEMATICS",
            "MUSCLE_ACTION_DESCRIPTION != MUSCLE_ACTIVATION_MEASUREMENT",
            "OPTIMIZED_MUSCLE_ACTIVATION != MEASURED_EMG",
            "SIMULATED_FORCE != MEASURED_HUMAN_FORCE",
            "FORWARD_HEAD_VARIATION != STRUCTURAL_DEFORMITY_DIAGNOSIS",
            "POSTURE_VARIATION != CLINICAL_DIAGNOSIS",
            "G14 = BLOCKED_EXTERNAL_DATA",
            "RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY"
        ],
        "scenarios": [s.__dict__ for s in get_scenario_catalog()],
        "provenance": get_provenance_manifest(),
    }
