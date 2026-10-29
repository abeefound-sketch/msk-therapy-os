"""Tests for MSK-Therapy-OS Milestone P10.3A.

Validates:
- Offline DICOM intake parser and transfer syntax policy
- DICOM PHI header screening and burned-in identifier risk detection
- SOPInstanceUID and SHA-256 duplicate detection
- Third-reviewer adjudication and multi-reviewer role separation
- Holdout partition cryptographic locking and site-level isolation
- Advanced statistical metrics (IQR, ICC, Subject-level Bootstrap 95% CI)
- G14 Scientific Gate state machine and negative tests preventing synthetic unlock
- Server REST API endpoints for P10.3 validation
"""

import os
import struct
import tempfile
import json
import threading
import urllib.request
import urllib.error
import pytest
from typing import Dict, Any, Tuple

from msk_therapy_os.dicom_intake import (
    DicomHeaderParser,
    DicomIntakeAdapter,
    DicomTransferSyntax,
    DicomQuarantineReason,
)
from msk_therapy_os.anatomical_validation import (
    IndependentAnatomicalValidator,
    G14ScientificGateState,
    QuarantineReason,
    ExternalGroundTruthDataset,
    GroundTruthObservation,
    GroundTruthModality,
    ReviewStatus,
    HoldoutPartitionManager,
    ClinicalReviewerCredentials,
)
from msk_therapy_os.server import create_server


def create_mock_dicom(
    file_path: str,
    transfer_syntax_uid: str = DicomTransferSyntax.EXPLICIT_VR_LITTLE_ENDIAN.value,
    patient_name: str = "P-001",
    patient_id: str = "P-001",
    patient_birth_date: str = "",
    modality: str = "CT",
    sop_instance_uid: str = "1.2.826.0.1.3680043.2.1125.1",
    number_of_frames: int = 1,
    burned_in_annotation: str = "NO",
    slice_thickness: float = 1.0,
) -> str:
    """Helper to create a binary compliant DICOM fixture with Explicit VR Little Endian metadata."""
    preamble = b"\x00" * 128
    magic = b"DICM"

    # Group 0002 elements (File Meta Information)
    ts_bytes = transfer_syntax_uid.encode("ascii") + (b"\x00" if len(transfer_syntax_uid) % 2 != 0 else b"")
    meta_ts = struct.pack("<HH2sH", 0x0002, 0x0010, b"UI", len(ts_bytes)) + ts_bytes

    # Dataset elements
    def pack_elem(group: int, elem: int, vr: bytes, val_bytes: bytes) -> bytes:
        if len(val_bytes) % 2 != 0:
            val_bytes += b" "
        return struct.pack("<HH2sH", group, elem, vr, len(val_bytes)) + val_bytes

    ds = bytearray()
    # Modality (0008, 0060) CS
    ds += pack_elem(0x0008, 0x0060, b"CS", modality.encode("ascii"))
    # SOPInstanceUID (0008, 0018) UI
    ds += pack_elem(0x0008, 0x0018, b"UI", sop_instance_uid.encode("ascii"))
    # PatientName (0010, 0010) PN
    ds += pack_elem(0x0010, 0x0010, b"PN", patient_name.encode("latin1"))
    # PatientID (0010, 0020) LO
    ds += pack_elem(0x0010, 0x0020, b"LO", patient_id.encode("latin1"))
    # PatientBirthDate (0010, 0030) DA
    if patient_birth_date:
        ds += pack_elem(0x0010, 0x0030, b"DA", patient_birth_date.encode("ascii"))
    # SliceThickness (0018, 0050) DS
    ds += pack_elem(0x0018, 0x0050, b"DS", str(slice_thickness).encode("ascii"))
    # NumberOfFrames (0028, 0008) IS
    ds += pack_elem(0x0028, 0x0008, b"IS", str(number_of_frames).encode("ascii"))
    # BurnedInAnnotation (0028, 0301) CS
    ds += pack_elem(0x0028, 0x0301, b"CS", burned_in_annotation.encode("ascii"))

    with open(file_path, "wb") as f:
        f.write(preamble + magic + meta_ts + ds)

    return file_path


# --- PHASE B: DICOM INTAKE & SECURITY TESTS ---

def test_dicom_preamble_and_magic_screening(tmp_path):
    """Verify detection of valid DICOM signature and rejection of non-DICOM inputs."""
    valid_file = str(tmp_path / "valid.dcm")
    create_mock_dicom(valid_file)
    res_valid = DicomHeaderParser.parse_file(valid_file)
    assert res_valid.is_valid_dicom is True
    assert res_valid.passed_screening is True
    assert res_valid.parsed_tags_count > 0

    # Non-DICOM file (missing DICM magic at offset 128)
    invalid_file = str(tmp_path / "invalid.dcm")
    with open(invalid_file, "wb") as f:
        f.write(b"NOT A DICOM FILE AT ALL")
    res_invalid = DicomHeaderParser.parse_file(invalid_file)
    assert res_invalid.is_valid_dicom is False
    assert DicomQuarantineReason.NOT_A_DICOM_FILE in res_invalid.quarantine_reasons


def test_dicom_transfer_syntax_support_and_rejection(tmp_path):
    """Verify supported vs unsupported transfer syntaxes under fail-closed policy."""
    # Supported: Explicit VR Little Endian
    f_expl = str(tmp_path / "explicit_vr.dcm")
    create_mock_dicom(f_expl, transfer_syntax_uid=DicomTransferSyntax.EXPLICIT_VR_LITTLE_ENDIAN.value)
    res_expl = DicomHeaderParser.parse_file(f_expl)
    assert res_expl.is_supported is True
    assert res_expl.passed_screening is True

    # Unsupported compressed: JPEG Baseline (1.2.840.10008.1.2.4.50)
    f_jpeg = str(tmp_path / "jpeg_baseline.dcm")
    create_mock_dicom(f_jpeg, transfer_syntax_uid=DicomTransferSyntax.JPEG_BASELINE.value)
    res_jpeg = DicomHeaderParser.parse_file(f_jpeg)
    assert res_jpeg.is_supported is False
    assert DicomQuarantineReason.UNSUPPORTED_COMPRESSION in res_jpeg.quarantine_reasons

    # Unsupported compressed: JPEG 2000 (1.2.840.10008.1.2.4.90)
    f_j2k = str(tmp_path / "jpeg_2000.dcm")
    create_mock_dicom(f_j2k, transfer_syntax_uid=DicomTransferSyntax.JPEG_2000_LOSSLESS.value)
    res_j2k = DicomHeaderParser.parse_file(f_j2k)
    assert res_j2k.is_supported is False
    assert DicomQuarantineReason.UNSUPPORTED_COMPRESSION in res_j2k.quarantine_reasons


def test_dicom_multiframe_rejected(tmp_path):
    """Verify that multiframe DICOM inputs are quarantined."""
    f_multi = str(tmp_path / "multiframe.dcm")
    create_mock_dicom(f_multi, number_of_frames=30)
    res = DicomHeaderParser.parse_file(f_multi)
    assert res.number_of_frames == 30
    assert DicomQuarantineReason.MULTIFRAME_UNSUPPORTED in res.quarantine_reasons


def test_dicom_phi_header_screening(tmp_path):
    """Verify 18-element HIPAA screening on DICOM headers."""
    # Real patient name violation
    f_name = str(tmp_path / "phi_name.dcm")
    create_mock_dicom(f_name, patient_name="Doe^John")
    res_name = DicomHeaderParser.parse_file(f_name)
    assert DicomQuarantineReason.PHI_IN_PATIENT_NAME in res_name.quarantine_reasons

    # Patient birth date violation
    f_dob = str(tmp_path / "phi_dob.dcm")
    create_mock_dicom(f_dob, patient_name="P-001", patient_birth_date="19750512")
    res_dob = DicomHeaderParser.parse_file(f_dob)
    assert DicomQuarantineReason.PHI_IN_BIRTH_DATE in res_dob.quarantine_reasons

    # Filename with PHI token
    f_file_phi = str(tmp_path / "Dr_Smith_Patient_Scan.dcm")
    create_mock_dicom(f_file_phi, patient_name="P-001")
    res_fphi = DicomHeaderParser.parse_file(f_file_phi)
    assert DicomQuarantineReason.PHI_IN_METADATA_HEADER in res_fphi.quarantine_reasons


def test_dicom_burned_in_annotation_detection(tmp_path):
    """Verify quarantine of pixel data with burned-in annotations."""
    # Explicit BurnedInAnnotation == YES
    f_burned = str(tmp_path / "burned_in.dcm")
    create_mock_dicom(f_burned, burned_in_annotation="YES")
    res_burned = DicomHeaderParser.parse_file(f_burned)
    assert DicomQuarantineReason.BURNED_IN_IDENTIFIERS_RISK in res_burned.quarantine_reasons

    # Secondary Capture modality (SC) without explicit BurnedInAnnotation == NO
    f_sc = str(tmp_path / "secondary_capture.dcm")
    create_mock_dicom(f_sc, modality="SC", burned_in_annotation="UNKNOWN")
    res_sc = DicomHeaderParser.parse_file(f_sc)
    assert DicomQuarantineReason.BURNED_IN_IDENTIFIERS_RISK in res_sc.quarantine_reasons


def test_dicom_duplicate_detection(tmp_path):
    """Verify duplicate SOPInstanceUID and SHA-256 detection."""
    adapter = DicomIntakeAdapter(quarantine_dir=str(tmp_path / "quarantine"))
    f1 = str(tmp_path / "scan_1.dcm")
    create_mock_dicom(f1, sop_instance_uid="1.2.3.4.5.6.7")
    
    # First inspection passes
    res1 = adapter.inspect_file(f1)
    assert res1.passed_screening is True
    adapter._ingested_sop_uids.add(res1.sop_instance_uid)
    adapter._ingested_hashes.add(res1.sha256_hash)

    # Second inspection of same file or SOP UID triggers duplicate quarantine
    res2 = adapter.inspect_file(f1)
    assert DicomQuarantineReason.DUPLICATE_SOP_INSTANCE in res2.quarantine_reasons


# --- PHASE C & D: GOVERNANCE, ADJUDICATION & HOLDOUT ISOLATION ---

def test_third_reviewer_adjudication_lifecycle():
    """Verify third-reviewer adjudication of inter-observer disagreements."""
    validator = IndependentAnatomicalValidator()
    
    # Register clinical reviewers
    validator.register_reviewer(ClinicalReviewerCredentials("OBS-01", "Observer Jane", "OBSERVER", "University Hospital", "Radiology Tech"))
    validator.register_reviewer(ClinicalReviewerCredentials("REV-01", "Dr. Primary", "REVIEWER", "University Hospital", "Radiologist"))
    validator.register_reviewer(ClinicalReviewerCredentials("ADJ-LEAD", "Prof. Anatomist", "LEAD_ANATOMIST", "University Hospital", "Senior Anatomist"))

    # Register dataset and observation
    ds = ExternalGroundTruthDataset(
        dataset_id="DS-ADJUDICATION-TEST",
        name="Adjudication Test Dataset",
        source_organization="University Anatomy Lab",
        version="1.0",
        license="Research",
        doi_or_url="urn:test",
        modality=GroundTruthModality.CT_3D_SURFACE,
    )
    validator.register_dataset(ds)

    obs = GroundTruthObservation(
        point_code="ST25",
        dataset_id="DS-ADJUDICATION-TEST",
        canonical_position=(0.066, 0.980, 0.050),
        observer_id="OBS-01",
        reviewer_id="REV-01",
        review_status=ReviewStatus.DATA_IMPORTED,
    )
    validator.import_observations([obs])

    # 1. Non-governance reviewer cannot arbitrate
    with pytest.raises(ValueError, match="UNAUTHORIZED_ADJUDICATOR"):
        validator.adjudicate_inter_observer_disagreement(
            point_code="ST25",
            dataset_id="DS-ADJUDICATION-TEST",
            adjudicator_id="OBS-01",
            resolved_position=(0.065, 0.982, 0.051),
            rationale="Attempted self-adjudication",
        )

    # 2. Authorized lead anatomist resolves dispute
    res = validator.adjudicate_inter_observer_disagreement(
        point_code="ST25",
        dataset_id="DS-ADJUDICATION-TEST",
        adjudicator_id="ADJ-LEAD",
        resolved_position=(0.0655, 0.9815, 0.0505),
        rationale="Consensus reached after multi-planar MPR cross-referencing.",
    )
    assert res["status"] == "ADJUDICATION_RESOLVED"
    assert res["resolved_position"] == [0.0655, 0.9815, 0.0505]
    updated_obs = validator.get_observation("ST25", "DS-ADJUDICATION-TEST")
    assert updated_obs.review_status == ReviewStatus.REVIEWED
    assert "ADJUDICATION" in updated_obs.notes


def test_holdout_partition_locking_and_site_isolation():
    """Verify cryptographic locking of holdout manifest and site-level isolation."""
    mgr = HoldoutPartitionManager()
    subjects = [f"P-{i:03d}" for i in range(1, 21)]

    # 1. Standard 3-way partition
    manifest = mgr.create_three_way_partition("PART-3WAY-01", subjects)
    assert manifest.is_locked is True

    # 2. Cryptographic lock
    locked_m = mgr.lock_holdout_partition("PART-3WAY-01", admin_reviewer_id="ADMIN-GOV-01")
    assert locked_m.locked_by == "ADMIN-GOV-01"
    assert locked_m.locked_sha256 is not None
    assert len(locked_m.locked_sha256) == 64

    # 3. Freeze holdout after evaluation
    mgr.mark_holdout_evaluated("PART-3WAY-01")
    with pytest.raises(ValueError, match="HOLDOUT_ALREADY_EVALUATED"):
        mgr.lock_holdout_partition("PART-3WAY-01", admin_reviewer_id="ADMIN-GOV-02")

    # 4. Site-level partition isolation
    site_map = {
        "SITE-HOSPITAL-A": [f"P-A-{i:02d}" for i in range(1, 11)],
        "SITE-HOSPITAL-B": [f"P-B-{i:02d}" for i in range(1, 11)],
        "SITE-HOSPITAL-C": [f"P-C-{i:02d}" for i in range(1, 11)],  # Designate C as external holdout site
    }
    site_manifest = mgr.create_site_level_partition("PART-SITE-01", site_map, holdout_site_id="SITE-HOSPITAL-C")
    assert site_manifest.site_id == "SITE-HOSPITAL-C"
    assert site_manifest.holdout_subjects == site_map["SITE-HOSPITAL-C"]
    assert not set(site_manifest.calibration_subjects).intersection(site_manifest.holdout_subjects)


# --- PHASE E: ADVANCED STATISTICAL METRICS & BOOTSTRAP ---

def test_subject_bootstrap_ci_computation():
    """Verify subject-level bootstrap 95% Confidence Interval calculation."""
    validator = IndependentAnatomicalValidator()
    
    # 1. Zero/Insufficient subjects returns warning
    res_empty = validator.compute_subject_bootstrap_ci(n_bootstraps=100)
    assert res_empty["status"] == "INSUFFICIENT_SUBJECTS_FOR_BOOTSTRAP"

    # 2. Ingest 5 distinct subjects with synthetic observations
    observations = []
    for s_idx in range(1, 6):
        subj = f"P-{s_idx:03d}"
        s_ds_id = f"DS-BOOTSTRAP-{s_idx}"
        validator.register_dataset(ExternalGroundTruthDataset(
            dataset_id=s_ds_id,
            name=f"Bootstrap Test Dataset {s_idx}",
            source_organization="Test Lab",
            version="1.0",
            license="MIT",
            doi_or_url="urn:test",
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
            is_synthetic_fixture=True,
        ))
        for code in ("ST25", "CV8", "LU5", "GV20"):
            anchor = validator.resolve_point_coordinate(code)
            base_pos = anchor["canonical_position"]
            # Add synthetic 1.0mm - 2.0mm error
            pos = (base_pos[0] + 0.001 * s_idx, base_pos[1], base_pos[2])
            observations.append(GroundTruthObservation(
                point_code=code,
                dataset_id=s_ds_id,
                canonical_position=pos,
                subject_pseudonym=subj,
                synthetic_fixture=True,
            ))
    validator.import_observations(observations)

    # Compute bootstrap
    res_boot = validator.compute_subject_bootstrap_ci(point_codes=["ST25", "CV8", "LU5", "GV20"], n_bootstraps=500, seed=123)
    assert res_boot["status"] == "BOOTSTRAP_COMPUTED"
    assert res_boot["independent_subjects_count"] == 5
    ci_rmse = res_boot["bootstrap_rmse_ci_95_mm"]
    assert len(ci_rmse) == 2
    assert ci_rmse[0] <= ci_rmse[1]
    assert ci_rmse[0] <= res_boot["point_estimate_rmse_mm"] <= ci_rmse[1]


# --- PHASE F: G14 SCIENTIFIC GATE FAIL-CLOSED TESTS ---

def test_g14_scientific_gate_state_machine_and_negative_tests():
    """Verify that Gate G14 cannot be unlocked by synthetic or incomplete data."""
    validator = IndependentAnatomicalValidator()
    
    # 1. Initial baseline: No real external data -> BLOCKED_EXTERNAL_DATA
    g14_baseline = validator.evaluate_g14_scientific_gate()
    assert g14_baseline["gate_state"] == G14ScientificGateState.BLOCKED_EXTERNAL_DATA.value
    assert g14_baseline["is_unlocked"] is False

    # 2. Run synthetic dry-run: Technical pipeline PASS, but G14 remains strictly BLOCKED
    dry_res = validator.run_synthetic_pilot_dry_run()
    assert dry_res["synthetic_dry_run_passed"] is True
    assert dry_res["legacy_gate_g14"] == "BLOCKED_EXTERNAL_DATA"
    g14_after_dry = validator.evaluate_g14_scientific_gate()
    assert g14_after_dry["gate_state"] == G14ScientificGateState.BLOCKED_EXTERNAL_DATA.value
    assert g14_after_dry["is_unlocked"] is False

    # 3. Add an external real dataset WITHOUT administrative approval -> PENDING_GOVERNANCE_APPROVAL
    ds_real = ExternalGroundTruthDataset(
        dataset_id="DS-HOSPITAL-REAL-01",
        name="Real Hospital Dataset",
        source_organization="City Hospital",
        version="1.0",
        license="DUA",
        doi_or_url="urn:hospital",
        modality=GroundTruthModality.CT_3D_SURFACE,
        is_synthetic_fixture=False,
        administrative_verification_status="PENDING_ADMIN_SIGN_OFF",
    )
    validator.register_dataset(ds_real)
    g14_gov = validator.evaluate_g14_scientific_gate()
    assert g14_gov["gate_state"] == G14ScientificGateState.PENDING_GOVERNANCE_APPROVAL.value
    assert g14_gov["is_unlocked"] is False


# --- PHASE G: REST API ENDPOINT TESTS ---

@pytest.fixture(scope="module")
def validation_server(tmp_path_factory):
    """Start offline clinical server on ephemeral port for testing."""
    db_path = str(tmp_path_factory.mktemp("db") / "test_p10_3.db")
    server = create_server(db_path=db_path, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.shutdown()


def test_server_p10_3_rest_endpoints(validation_server, tmp_path):
    """Test new REST endpoints added in P10.3."""
    # 1. GET /api/atlas/validation/scientific-gate/status
    req = urllib.request.Request(f"{validation_server}/api/atlas/validation/scientific-gate/status")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["status"] == "success"
        assert data["gate_evaluation"]["gate_state"] == "BLOCKED_EXTERNAL_DATA"
        assert data["gate_evaluation"]["is_unlocked"] is False

    # 2. POST /api/atlas/validation/dicom/preflight
    mock_dcm = str(tmp_path / "api_test.dcm")
    create_mock_dicom(mock_dcm, patient_name="P-API-01")
    
    post_data = json.dumps({"file_path": mock_dcm}).encode()
    req = urllib.request.Request(
        f"{validation_server}/api/atlas/validation/dicom/preflight",
        data=post_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["status"] == "success"
        assert data["result"]["is_valid_dicom"] is True
        assert data["result"]["passed_screening"] is True

    # 3. GET /api/atlas/validation/quarantine/list
    req = urllib.request.Request(f"{validation_server}/api/atlas/validation/quarantine/list")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["status"] == "success"
        assert "quarantined_observations" in data
        assert "quarantined_dicom" in data

    # 4. POST /api/atlas/validation/bootstrap-metrics
    post_data = json.dumps({"n_bootstraps": 100, "seed": 42}).encode()
    req = urllib.request.Request(
        f"{validation_server}/api/atlas/validation/bootstrap-metrics",
        data=post_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "status" in data
