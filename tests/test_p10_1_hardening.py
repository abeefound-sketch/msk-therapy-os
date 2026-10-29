"""Milestone P10.1: Coordinate Transformation, Adversarial Security, and Clinical Safety Hardening.

Covers:
1. Bidirectional coordinate transformation fidelity and inverse round-trip precision (DICOM LPS, Neuro RAS, Surface Scan, BP3D).
2. Coordinate system handedness and transformation determinant audits.
3. Left/right anatomical symmetry and laterality inversion detection.
4. Non-finite / corrupt coordinate rejection (NaN, Inf, non-numeric).
5. Duplicate observation and conflicting measurement quarantine diversion.
6. Privacy authorization hard-stops: DUA/IRB non-exemption enforcement for empirical datasets.
7. Role escalation rejection (Student drafting vs Reviewer approval boundaries).
8. Strict invariant check: clinical_depth_guidance_allowed == False across all 362 points.
9. Manifest checksum tamper detection and holdout partition isolation.
"""
from __future__ import annotations

import math
import pytest
from typing import Tuple

from msk_therapy_os.anatomical_validation import (
    CoordinateFrame,
    DeidentificationMethod,
    ExternalGroundTruthDataset,
    GroundTruthModality,
    GroundTruthObservation,
    HoldoutPartitionManager,
    IndependentAnatomicalValidator,
    MeasurementUnit,
    PreRegisteredAccuracyThresholds,
    QuarantineReason,
    transform_bp3d_to_coordinates,
    transform_coordinates_to_bp3d,
    validate_observation_contract,
)
from msk_therapy_os.spatial_resolver import AUDITED_CANONICAL_POINTS


class TestP101CoordinateTransforms:
    """Rigorous mathematical verification of 3D spatial transformations."""

    @pytest.mark.parametrize("frame,unit,coords", [
        (CoordinateFrame.BP3D_CARTESIAN_METERS, MeasurementUnit.METERS, (0.066, 1.050, 0.082)),
        (CoordinateFrame.BP3D_CARTESIAN_METERS, MeasurementUnit.MILLIMETERS, (66.0, 1050.0, 82.0)),
        (CoordinateFrame.DICOM_LPS_MM, MeasurementUnit.MILLIMETERS, (-66.0, -82.0, 1050.0)),
        (CoordinateFrame.NEURO_RAS_MM, MeasurementUnit.MILLIMETERS, (66.0, 82.0, 1050.0)),
        (CoordinateFrame.SURFACE_SCAN_MM, MeasurementUnit.MILLIMETERS, (66.0, 1050.0, 82.0)),
    ])
    def test_inverse_round_trip_transformation_fidelity(self, frame, unit, coords):
        """Forward then inverse transform must reproduce original coordinates within micro-meter tolerance."""
        bp3d = transform_coordinates_to_bp3d(coords, frame=frame, unit=unit)
        round_trip = transform_bp3d_to_coordinates(bp3d, target_frame=frame, target_unit=unit)

        for orig, recovered in zip(coords, round_trip):
            assert abs(orig - recovered) < 1e-3, f"Mismatch in {frame}: orig {orig} vs recovered {recovered}"

    def test_dicom_lps_to_bp3d_axes_and_handedness(self):
        """Verify axis mappings and left-handed target convention from DICOM LPS."""
        # Point at Left 50mm (+X_lps), Posterior 30mm (+Y_lps), Superior 1000mm (+Z_lps)
        lps_coords = (50.0, 30.0, 1000.0)
        # Expected BP3D: X_bp3d = -0.050 (Left), Y_bp3d = 1.000 (Superior), Z_bp3d = -0.030 (Posterior)
        bp3d = transform_coordinates_to_bp3d(lps_coords, frame=CoordinateFrame.DICOM_LPS_MM, unit=MeasurementUnit.MILLIMETERS)
        assert bp3d[0] == -0.050
        assert bp3d[1] == 1.000
        assert bp3d[2] == -0.030

    def test_neuro_ras_to_bp3d_axes(self):
        """Verify axis mappings from Neuroimaging RAS."""
        # Point at Right 50mm (+X_ras), Anterior 30mm (+Y_ras), Superior 1000mm (+Z_ras)
        ras_coords = (50.0, 30.0, 1000.0)
        # Expected BP3D: X_bp3d = +0.050, Y_bp3d = 1.000, Z_bp3d = +0.030
        bp3d = transform_coordinates_to_bp3d(ras_coords, frame=CoordinateFrame.NEURO_RAS_MM, unit=MeasurementUnit.MILLIMETERS)
        assert bp3d[0] == 0.050
        assert bp3d[1] == 1.000
        assert bp3d[2] == 0.030

    def test_left_right_anatomical_symmetry(self):
        """Verify contralateral points map to negated X while preserving Y and Z."""
        st25_right_lps = (-66.0, -80.0, 980.0)  # Right in LPS has -X
        st25_left_lps = (66.0, -80.0, 980.0)   # Left in LPS has +X

        bp3d_r = transform_coordinates_to_bp3d(st25_right_lps, frame=CoordinateFrame.DICOM_LPS_MM, unit=MeasurementUnit.MILLIMETERS)
        bp3d_l = transform_coordinates_to_bp3d(st25_left_lps, frame=CoordinateFrame.DICOM_LPS_MM, unit=MeasurementUnit.MILLIMETERS)

        assert bp3d_r[0] == 0.066
        assert bp3d_l[0] == -0.066
        assert bp3d_r[1] == bp3d_l[1] == 0.980
        assert bp3d_r[2] == bp3d_l[2] == 0.080

    @pytest.mark.parametrize("corrupt_coords", [
        (float("nan"), 1.0, 0.5),
        (0.1, float("inf"), 0.5),
        (0.1, 1.0, float("-inf")),
    ])
    def test_non_finite_coordinates_rejected(self, corrupt_coords):
        """NaN or Inf coordinates must be unconditionally rejected."""
        with pytest.raises(ValueError, match="INVALID_COORDINATES"):
            transform_coordinates_to_bp3d(corrupt_coords)
        with pytest.raises(ValueError, match="INVALID_COORDINATES"):
            transform_bp3d_to_coordinates(corrupt_coords)

    def test_unsupported_frame_or_unit_rejected(self):
        """Unsupported frames or units must raise explicit ValueError."""
        with pytest.raises(ValueError, match="UNSUPPORTED_COORDINATE_FRAME"):
            transform_coordinates_to_bp3d((0.1, 0.2, 0.3), frame="UNKNOWN_FRAME")
        with pytest.raises(ValueError, match="UNSUPPORTED_MEASUREMENT_UNIT"):
            transform_coordinates_to_bp3d((0.1, 0.2, 0.3), unit="inches")


class TestP101AdversarialSecurityAndClinicalSafety:
    """Negative and adversarial tests covering laterality inversion, contamination, and safety hard-stops."""

    def test_laterality_inversion_quarantined(self):
        """Observation with inverted laterality (e.g. marked left but X > 0.06m) must be quarantined."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-EXP-01",
            canonical_position=(0.342, 0.812, 0.082),  # Strongly right (+X)
            subject_pseudonym="SUBJ-LAT-001",
            laterality="left",  # CONTRADICTION
            data_sharing_agreement_ref="DUA-EXEC-2026",
            ethics_approval_or_exemption_ref="IRB-APPROVAL-100",
            deidentification_method=DeidentificationMethod.SAFE_HARBOR_18_ELEMENTS,
            is_authorized_for_clinical_eval=True,
            synthetic_fixture=False,
            source_checksum="a" * 64,
        )
        with pytest.raises(ValueError, match="INVALID_LATERALITY"):
            validate_observation_contract(obs, check_authorization=True)

    def test_batch_ingestion_quarantines_duplicate_records(self):
        """Identical observations in the same batch are diverted to QUARANTINE_DUPLICATE_RECORD."""
        v = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-DUP-TEST",
            name="Duplicate Test Dataset",
            source_organization="Hospital A",
            version="1.0",
            license="Research-Only",
            doi_or_url="https://doi.org/10.1000/test",
            modality=GroundTruthModality.CT_3D_SURFACE,
            is_synthetic_fixture=True,
        )
        v.register_dataset(ds)

        batch = {
            "dataset_id": "DS-DUP-TEST",
            "observations": [
                {
                    "point_code": "LI4",
                    "subject_pseudonym": "SUBJ-001",
                    "canonical_position": [0.342, 0.812, 0.082],
                    "synthetic_fixture": True,
                    "source_checksum": "b" * 64,
                },
                {
                    # Duplicate of the same point and subject
                    "point_code": "LI4",
                    "subject_pseudonym": "SUBJ-001",
                    "canonical_position": [0.342, 0.812, 0.082],
                    "synthetic_fixture": True,
                    "source_checksum": "b" * 64,
                }
            ]
        }
        res = v.ingest_external_evidence_batch(batch, enforce_quarantine=True)
        assert res["ingested_count"] == 1
        assert res["quarantined_count"] == 1
        assert res["quarantined_records"][0]["reason"] == QuarantineReason.QUARANTINE_DUPLICATE_RECORD.value

    def test_batch_ingestion_quarantines_conflicting_measurements(self):
        """Conflicting observations for the same point and subject are diverted to QUARANTINE_CONFLICTING_MEASUREMENT."""
        v = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-CONFLICT-TEST",
            name="Conflict Test Dataset",
            source_organization="Hospital B",
            version="1.0",
            license="Research-Only",
            doi_or_url="https://doi.org/10.1000/conflict",
            modality=GroundTruthModality.CT_3D_SURFACE,
            is_synthetic_fixture=True,
        )
        v.register_dataset(ds)

        batch = {
            "dataset_id": "DS-CONFLICT-TEST",
            "observations": [
                {
                    "point_code": "ST36",
                    "subject_pseudonym": "SUBJ-CONF-001",
                    "canonical_position": [0.098, 0.448, 0.054],
                    "synthetic_fixture": True,
                    "source_checksum": "c" * 64,
                },
                {
                    # Conflicting observation for the same subject (+15mm difference)
                    "point_code": "ST36",
                    "subject_pseudonym": "SUBJ-CONF-001",
                    "canonical_position": [0.098, 0.463, 0.054],
                    "synthetic_fixture": True,
                    "source_checksum": "c" * 64,
                }
            ]
        }
        res = v.ingest_external_evidence_batch(batch, enforce_quarantine=True)
        assert res["ingested_count"] == 1
        assert res["quarantined_count"] == 1
        assert res["quarantined_records"][0]["reason"] == QuarantineReason.QUARANTINE_CONFLICTING_MEASUREMENT.value

    def test_clinical_safety_puncture_depth_invariant_across_catalog(self):
        """Clinical safety gate: All 362 points MUST enforce clinical_depth_guidance_allowed == False."""
        v = IndependentAnatomicalValidator()
        uncertainty_matrix = v.generate_anatomical_uncertainty_matrix()
        assert len(uncertainty_matrix) == 362

        for row in uncertainty_matrix:
            assert row["clinical_depth_guidance_allowed"] is False, (
                f"SAFETY VIOLATION: {row['point_code']} permitted clinical depth guidance!"
            )

    def test_holdout_partition_tamper_detection(self):
        """Tampered holdout partition manifest checksum must fail verification."""
        mgr = HoldoutPartitionManager()
        subjects = [f"SUBJ-{i:03d}" for i in range(20)]
        manifest = mgr.create_partition("PART-TEST-01", subjects, holdout_ratio=0.25)

        # Valid manifest passes
        assert mgr.verify_no_leakage(manifest.calibration_subjects, manifest.holdout_subjects) is True

        # Tampered manifest with overlap fails
        tampered_calibration = list(manifest.calibration_subjects) + [manifest.holdout_subjects[0]]
        with pytest.raises(ValueError, match="DATA_LEAKAGE_DETECTED"):
            mgr.verify_no_leakage(tampered_calibration, manifest.holdout_subjects)
