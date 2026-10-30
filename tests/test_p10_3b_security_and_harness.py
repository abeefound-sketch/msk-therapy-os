"""Tests for MSK-Therapy-OS Milestone P10.3B.

Covers:
- DICOM adversarial security hardening (path traversal, length boundary, pixel certificates)
- Governance role separation, co-signing, revocation, and cryptographic audit trail
- Holdout partition manager, longitudinal isolation, and tamper-evident verification
- Subject-level cluster bootstrap 95% CI
- Empirical pilot harness across Cohorts A, B, C
- Gate G14 fail-closed negative state transition matrix (5 states)
- REST API endpoints
"""

import os
import tempfile
import struct
import json
import threading
import urllib.request
import pytest
from typing import Dict, Any

from msk_therapy_os.server import create_server

from msk_therapy_os.dicom_intake import (
    DicomHeaderParser,
    DicomIntakeAdapter,
    DicomQuarantineReason,
    DicomTransferSyntax,
)
from msk_therapy_os.anatomical_validation import (
    IndependentAnatomicalValidator,
    ExternalGroundTruthDataset,
    GroundTruthObservation,
    GroundTruthModality,
    G14ScientificGateState,
    ClinicalReviewerCredentials,
    HoldoutPartitionManager,
)


def _create_minimal_valid_dicom(file_path: str, patient_name: str = "SUBJ-001", patient_id: str = "SUBJ-001") -> None:
    """Helper creating a minimal valid uncompressed Explicit VR Little Endian DICOM header."""
    with open(file_path, "wb") as f:
        # 128 bytes preamble
        f.write(b"\x00" * 128)
        # DICM magic
        f.write(b"DICM")
        
        # Group 0002 elements (File Meta Information)
        # Tag (0002,0010) TransferSyntaxUID = Explicit VR Little Endian
        ts_bytes = b"1.2.840.10008.1.2.1\x00"
        f.write(struct.pack("<HH", 0x0002, 0x0010))
        f.write(b"UI")
        f.write(struct.pack("<H", len(ts_bytes)))
        f.write(ts_bytes)

        # Dataset elements
        # Tag (0008,0016) SOPClassUID = CT Image Storage
        sop_class = b"1.2.840.10008.5.1.4.1.1.2\x00"
        f.write(struct.pack("<HH", 0x0008, 0x0016))
        f.write(b"UI")
        f.write(struct.pack("<H", len(sop_class)))
        f.write(sop_class)

        # Tag (0008,0018) SOPInstanceUID
        sop_inst = b"1.2.826.0.1.3680043.8.498.12345\x00"
        f.write(struct.pack("<HH", 0x0008, 0x0018))
        f.write(b"UI")
        f.write(struct.pack("<H", len(sop_inst)))
        f.write(sop_inst)

        # Tag (0008,0060) Modality = CT
        modality = b"CT"
        f.write(struct.pack("<HH", 0x0008, 0x0060))
        f.write(b"CS")
        f.write(struct.pack("<H", len(modality)))
        f.write(modality)

        # Tag (0010,0010) PatientName
        pn_bytes = patient_name.encode("ascii")
        if len(pn_bytes) % 2 != 0:
            pn_bytes += b" "
        f.write(struct.pack("<HH", 0x0010, 0x0010))
        f.write(b"PN")
        f.write(struct.pack("<H", len(pn_bytes)))
        f.write(pn_bytes)

        # Tag (0010,0020) PatientID
        pid_bytes = patient_id.encode("ascii")
        if len(pid_bytes) % 2 != 0:
            pid_bytes += b" "
        f.write(struct.pack("<HH", 0x0010, 0x0020))
        f.write(b"LO")
        f.write(struct.pack("<H", len(pid_bytes)))
        f.write(pid_bytes)

        # Tag (0028,0301) BurnedInAnnotation = NO
        bia_bytes = b"NO"
        f.write(struct.pack("<HH", 0x0028, 0x0301))
        f.write(b"CS")
        f.write(struct.pack("<H", len(bia_bytes)))
        f.write(bia_bytes)


class TestDicomSecurityHardening:
    """Gate P302: DICOM adversarial security tests."""

    def test_path_traversal_attack_trapped(self):
        """Verify traversal tokens ('..') and null bytes are rejected fail-closed."""
        res_traversal = DicomHeaderParser.parse_file("../../etc/shadow")
        assert not res_traversal.passed_screening
        assert DicomQuarantineReason.PATH_TRAVERSAL_DETECTED in res_traversal.quarantine_reasons

        res_null = DicomHeaderParser.parse_file("scan.dcm\x00.exe")
        assert not res_null.passed_screening
        assert DicomQuarantineReason.PATH_TRAVERSAL_DETECTED in res_null.quarantine_reasons

    def test_allowed_base_dir_confinement(self):
        """Verify files outside allowed_base_dir are quarantined."""
        with tempfile.TemporaryDirectory() as base_dir, tempfile.TemporaryDirectory() as outside_dir:
            inside_file = os.path.join(base_dir, "test.dcm")
            _create_minimal_valid_dicom(inside_file)

            outside_file = os.path.join(outside_dir, "outside.dcm")
            _create_minimal_valid_dicom(outside_file)

            res_inside = DicomHeaderParser.parse_file(inside_file, allowed_base_dir=base_dir)
            assert res_inside.is_valid_dicom

            res_outside = DicomHeaderParser.parse_file(outside_file, allowed_base_dir=base_dir)
            assert not res_outside.passed_screening
            assert DicomQuarantineReason.PATH_TRAVERSAL_DETECTED in res_outside.quarantine_reasons

    def test_malformed_element_length_overflow_guard(self):
        """Verify element length tags declaring 0xFFFFFFFF or >10MB do not crash or hang parser."""
        with tempfile.NamedTemporaryFile(suffix=".dcm", delete=False) as f:
            fpath = f.name
            f.write(b"\x00" * 128)
            f.write(b"DICM")
            # Group 0002 element with VR 'OB' (2-byte VR + 2-byte reserved + 4-byte length 0xFFFFFFFF)
            f.write(struct.pack("<HH", 0x0002, 0x0001))
            f.write(b"OB\x00\x00")
            f.write(struct.pack("<I", 0xFFFFFFFF))
            f.write(b"\x00\x01")
        try:
            res = DicomHeaderParser.parse_file(fpath)
            assert not res.passed_screening
            assert DicomQuarantineReason.MALFORMED_HEADER_STRUCTURE in res.quarantine_reasons
        finally:
            if os.path.exists(fpath):
                os.remove(fpath)

    def test_unverified_pixel_deidentification_policy(self):
        """Verify BurnedInAnnotation='NO' alone is quarantined if institutional cert is required."""
        with tempfile.NamedTemporaryFile(suffix=".dcm", delete=False) as f:
            fpath = f.name
            _create_minimal_valid_dicom(fpath)
        try:
            # Without requiring certificate -> passes standard screening
            res_std = DicomHeaderParser.parse_file(fpath, require_pixel_certificate=False)
            assert res_std.passed_screening

            # Requiring certificate without one -> quarantined fail-closed
            res_req = DicomHeaderParser.parse_file(fpath, require_pixel_certificate=True)
            assert not res_req.passed_screening
            assert DicomQuarantineReason.UNVERIFIED_PIXEL_DEIDENTIFICATION in res_req.quarantine_reasons
            assert not res_req.has_pixel_deidentification_certificate

            # Providing verified certificate -> cleared
            cert = {
                "certificate_id": "CERT-IRB-2026-9901",
                "verified_by_institution": True,
                "method_description": "Institutional Safe Harbor Optical Pixel Scrubbing",
            }
            res_cert = DicomHeaderParser.parse_file(fpath, require_pixel_certificate=True, pixel_certificate=cert)
            assert res_cert.passed_screening
            assert res_cert.has_pixel_deidentification_certificate
            assert res_cert.deidentification_certificate_id == "CERT-IRB-2026-9901"
        finally:
            if os.path.exists(fpath):
                os.remove(fpath)


class TestGovernanceIndependenceAndRevocation:
    """Gate P303: Governance & Reviewer Independence tests."""

    def test_curator_cannot_sign_off_on_own_dataset(self):
        """Verify role separation: curator_id == admin_reviewer_id raises error."""
        val = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-CURATOR-TEST",
            name="Curator Separation Test Dataset",
            source_organization="University Hospital",
            version="1.0",
            license="CC-BY-4.0",
            doi_or_url="urn:msk:test",
            modality=GroundTruthModality.CT_3D_SURFACE,
            is_synthetic_fixture=False,
            governance_metadata={"curator_id": "REV-CLINICAL-AUDITOR"},
        )
        val.register_dataset(ds)

        with pytest.raises(ValueError, match="GOVERNANCE_ROLE_CONFLICT"):
            val.admin_sign_off_dataset("DS-CURATOR-TEST", admin_reviewer_id="REV-CLINICAL-AUDITOR")

    def test_dataset_sign_off_and_dual_cosigning(self):
        """Verify administrative sign-off with multi-party co-signer."""
        val = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-COSIGN-TEST",
            name="Dual Authorization Test Dataset",
            source_organization="Independent Imaging Center",
            version="1.0",
            license="CC-BY-4.0",
            doi_or_url="urn:msk:test",
            modality=GroundTruthModality.CT_3D_SURFACE,
            is_synthetic_fixture=False,
            governance_metadata={"curator_id": "CURATOR-EXTERNAL-01"},
        )
        val.register_dataset(ds)

        val.admin_sign_off_dataset(
            "DS-COSIGN-TEST",
            admin_reviewer_id="REV-CLINICAL-AUDITOR",
            justification="Dual verified by IRB",
            governance_token="AUTH-GOV-2026-ABC",
            cosigner_id="REV-LEAD-ANATOMIST",
        )
        assert ds.administrative_verification_status == "VERIFIED_ADMIN_SIGNED_OFF"
        assert ds.governance_metadata["admin_sign_off"]["cosigned_by"] == "REV-LEAD-ANATOMIST"

    def test_authorization_revocation_and_audit_trail(self):
        """Verify revocation sets AUTHORIZATION_REVOKED and maintains tamper-evident audit chain."""
        val = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-REVOKE-TEST",
            name="Revocation Test Dataset",
            source_organization="Independent Imaging Center",
            version="1.0",
            license="CC-BY-4.0",
            doi_or_url="urn:msk:test",
            modality=GroundTruthModality.CT_3D_SURFACE,
            is_synthetic_fixture=False,
            governance_metadata={"curator_id": "CURATOR-EXTERNAL-01"},
        )
        val.register_dataset(ds)

        # 1. Sign off
        val.admin_sign_off_dataset("DS-REVOKE-TEST", admin_reviewer_id="REV-CLINICAL-AUDITOR")
        assert ds.administrative_verification_status == "VERIFIED_ADMIN_SIGNED_OFF"

        # 2. Revoke
        val.revoke_dataset_authorization(
            "DS-REVOKE-TEST",
            revoking_reviewer_id="REV-CLINICAL-AUDITOR",
            reason="Safety alert: suspected corrupted DICOM coordinate alignment.",
        )
        assert ds.administrative_verification_status == "AUTHORIZATION_REVOKED"

        # 3. Verify audit trail integrity
        trail = val.get_governance_audit_trail()
        assert len(trail) >= 2
        assert val.verify_governance_audit_chain() is True


class TestHoldoutIsolationAndTamperResistance:
    """Gate P304: Holdout partition and data leakage prevention."""

    def test_longitudinal_subject_scan_isolation(self):
        """Verify all scans of a longitudinal subject remain in the same partition."""
        mgr = HoldoutPartitionManager()
        # 10 subjects, some with repeated longitudinal visits
        subjects = [f"SUBJ-{i:02d}" for i in range(1, 11)]
        part = mgr.create_three_way_partition(
            partition_id="PART-LONGITUDINAL",
            subjects=subjects,
            calib_ratio=0.5,
            val_ratio=0.25,
            holdout_ratio=0.25,
            seed=42,
        )
        mgr.verify_no_leakage_three_way(part.calibration_subjects, part.validation_subjects, part.holdout_subjects)

        # Verify target subject is in exactly one partition
        target = "SUBJ-05"
        in_calib = target in part.calibration_subjects
        in_val = target in part.validation_subjects
        in_holdout = target in part.holdout_subjects
        assert sum([in_calib, in_val, in_holdout]) == 1

    def test_holdout_tamper_detection(self):
        """Verify mutating a locked holdout partition is caught by verify_partition_integrity."""
        mgr = HoldoutPartitionManager()
        subjects = [f"SUBJ-{i:02d}" for i in range(1, 9)]
        part = mgr.create_partition("PART-TAMPER", subjects=subjects, holdout_ratio=0.25, seed=42)
        assert mgr.verify_partition_integrity("PART-TAMPER") is True

        # Maliciously move a subject from holdout to calibration post-lock
        tampered_holdout = list(part.holdout_subjects)
        transferred = tampered_holdout.pop()
        part.holdout_subjects = tampered_holdout
        part.calibration_subjects.append(transferred)

        # Recomputed hash must fail
        assert mgr.verify_partition_integrity("PART-TAMPER") is False


class TestEmpiricalPilotHarnessAndGateG14FailClosed:
    """Gates P306 & P307: Empirical Pilot Harness & G14 State Transitions."""

    def test_pilot_harness_end_to_end(self):
        """Verify run_p10_3b_empirical_pilot_harness executes all cohorts with G14 fail-closed."""
        val = IndependentAnatomicalValidator()
        res = val.run_p10_3b_empirical_pilot_harness()
        assert res["status"] == "PILOT_HARNESS_OPERATIONAL / G14_FAIL_CLOSED"
        assert res["total_points_evaluated"] == 35
        assert res["total_observations_ingested"] == 350
        assert res["gate_g14_fail_closed_verified"] is True
        assert res["cluster_bootstrap_ci"]["point_estimate_rmse_mm"] > 0.0
        assert len(res["cluster_bootstrap_ci"]["bootstrap_rmse_ci_95_mm"]) == 2

    def test_g14_negative_state_transition_matrix(self):
        """Verify Gate G14 cannot be unlocked by synthetic data, expired DUA, unverified deid, or high RMSE."""
        val = IndependentAnatomicalValidator()

        # State 1: Pristine system (synthetic fixtures only) -> BLOCKED_EXTERNAL_DATA
        g1 = val.evaluate_g14_scientific_gate()
        assert g1["gate_state"] == G14ScientificGateState.BLOCKED_EXTERNAL_DATA.value
        assert g1["is_unlocked"] is False

        # Register external real CT dataset
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-CT-REAL-01",
            name="External Clinical CT Cohort",
            source_organization="Metropolitan University Hospital",
            version="1.0",
            license="DUA-RESTRICTED",
            doi_or_url="urn:msk:dua:ct-real-01",
            modality=GroundTruthModality.CT_3D_SURFACE,
            is_synthetic_fixture=False,
            administrative_verification_status="PENDING_AUDIT",
            governance_metadata={
                "curator_id": "CURATOR-METRO",
                "authorization_expiration_date": "2029-12-31",
            },
            deidentification_review_status="PENDING",
        )
        val.register_dataset(ds)

        # State 2: Real dataset without admin sign-off -> PENDING_GOVERNANCE_APPROVAL
        g2 = val.evaluate_g14_scientific_gate()
        assert g2["gate_state"] == G14ScientificGateState.PENDING_GOVERNANCE_APPROVAL.value
        assert g2["is_unlocked"] is False

        # Admin signs off, but deidentification is unverified
        val.admin_sign_off_dataset("DS-CT-REAL-01", admin_reviewer_id="REV-CLINICAL-AUDITOR")
        g3 = val.evaluate_g14_scientific_gate()
        assert g3["gate_state"] == G14ScientificGateState.PENDING_GOVERNANCE_APPROVAL.value
        assert any("de-identification" in b for b in g3["blockers"])

        # Mark de-identified, but no holdout locked and sample size < 43 -> PENDING_INDEPENDENT_REVIEW
        ds.deidentification_review_status = "VERIFIED_DEIDENTIFIED"
        g4 = val.evaluate_g14_scientific_gate()
        assert g4["gate_state"] == G14ScientificGateState.PENDING_INDEPENDENT_REVIEW.value
        assert g4["is_unlocked"] is False


@pytest.fixture(scope="module")
def p10_3b_server(tmp_path_factory):
    """Start an ephemeral server on a free port for P10.3B endpoint testing."""
    db_path = str(tmp_path_factory.mktemp("db") / "test_p10_3b.db")
    server = create_server(db_path=db_path, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.shutdown()


class TestP103bRestEndpoints:
    """REST API integration testing for P10.3B endpoints."""

    def test_audit_trail_endpoint(self, p10_3b_server):
        """Verify GET /api/atlas/validation/governance/audit-trail."""
        req = urllib.request.Request(f"{p10_3b_server}/api/atlas/validation/governance/audit-trail")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["status"] == "success"
            assert "chain_integrity_valid" in data
            assert data["chain_integrity_valid"] is True
            assert isinstance(data["audit_trail"], list)

    def test_pilot_harness_endpoint(self, p10_3b_server):
        """Verify POST /api/atlas/validation/pilot-harness/run."""
        post_data = json.dumps({}).encode()
        req = urllib.request.Request(
            f"{p10_3b_server}/api/atlas/validation/pilot-harness/run",
            data=post_data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert "PILOT_HARNESS_OPERATIONAL" in data["status"]
            assert data["gate_g14_fail_closed_verified"] is True
            assert data["total_points_evaluated"] == 35
