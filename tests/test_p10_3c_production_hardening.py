"""MSK-Therapy-OS P10.3C Production Hardening & Adversarial Verification Test Suite.

Milestone: P10.3C
Validates:
- Gates P309-P316
- DICOM bounded streaming, 1GB file size limit, symlink sandbox containment
- 4x4 Affine spatial transform and orthonormality verification
- Private tag text PHI screening
- Cryptographically verifiable DeidentificationTrustAuthority (HMAC-SHA256, manifest hash binding)
- Persistent SQLite governance audit trail and tamper-evident hash chain
- Multi-party administrative sign-off, separation of duties, and session validation
- Longitudinal holdout partition isolation and zero data leakage
"""

import os
import struct
import tempfile
import time
import json
import sqlite3
import pytest

from msk_therapy_os.dicom_intake import (
    DicomHeaderParser,
    DicomIntakeAdapter,
    DicomQuarantineReason,
    DicomPreflightResult,
    MAX_DICOM_FILE_SIZE,
    MAX_METADATA_ELEMENT_LENGTH,
    MAX_PIXEL_DATA_LENGTH,
)
from msk_therapy_os.deidentification_trust import (
    DeidentificationAttestation,
    DeidentificationTrustAuthority,
)
from msk_therapy_os.anatomical_validation import (
    IndependentAnatomicalValidator,
    ExternalGroundTruthDataset,
    ClinicalReviewerCredentials,
    GroundTruthModality,
    HoldoutPartitionManager,
)
from msk_therapy_os.auth import (
    create_user,
    create_session,
    init_auth_tables,
)


def _create_minimal_dicom(
    file_path: str,
    modality: str = "CT",
    patient_id: str = "SUBJ-TEST-001",
    patient_name: str = "SUBJ-TEST-001",
    iop: str = "1\\0\\0\\0\\1\\0",
    pixel_spacing: str = "0.5\\0.5",
    ipp: str = "-100\\-100\\50",
    slice_thickness: str = "1.5",
    extra_elements: bytes = b"",
    pixel_bytes: bytes = b"\x00" * 512,
) -> None:
    """Create a synthetically valid Explicit VR Little Endian DICOM binary fixture."""
    with open(file_path, "wb") as f:
        # 128 bytes preamble + DICM magic
        f.write(b"\x00" * 128)
        f.write(b"DICM")

        # Group 0002 File Meta Information
        # TransferSyntaxUID (0002, 0010) = Explicit VR Little Endian (1.2.840.10008.1.2.1)
        ts_bytes = b"1.2.840.10008.1.2.1\x00"
        f.write(struct.pack("<HH", 0x0002, 0x0010))
        f.write(b"UI")
        f.write(struct.pack("<H", len(ts_bytes)))
        f.write(ts_bytes)

        # Modality (0008, 0060)
        m_bytes = modality.encode("ascii")
        if len(m_bytes) % 2 == 1:
            m_bytes += b" "
        f.write(struct.pack("<HH", 0x0008, 0x0060))
        f.write(b"CS")
        f.write(struct.pack("<H", len(m_bytes)))
        f.write(m_bytes)

        # SOPInstanceUID (0008, 0018)
        sop_bytes = b"1.2.3.4.5.6.7.8.9\x00"
        f.write(struct.pack("<HH", 0x0008, 0x0018))
        f.write(b"UI")
        f.write(struct.pack("<H", len(sop_bytes)))
        f.write(sop_bytes)

        # PatientName (0010, 0010)
        pn_bytes = patient_name.encode("latin1")
        if len(pn_bytes) % 2 == 1:
            pn_bytes += b" "
        f.write(struct.pack("<HH", 0x0010, 0x0010))
        f.write(b"PN")
        f.write(struct.pack("<H", len(pn_bytes)))
        f.write(pn_bytes)

        # PatientID (0010, 0020)
        pid_bytes = patient_id.encode("latin1")
        if len(pid_bytes) % 2 == 1:
            pid_bytes += b" "
        f.write(struct.pack("<HH", 0x0010, 0x0020))
        f.write(b"LO")
        f.write(struct.pack("<H", len(pid_bytes)))
        f.write(pid_bytes)

        # ImageOrientationPatient (0020, 0037)
        if iop:
            iop_b = iop.encode("ascii")
            if len(iop_b) % 2 == 1:
                iop_b += b" "
            f.write(struct.pack("<HH", 0x0020, 0x0037))
            f.write(b"DS")
            f.write(struct.pack("<H", len(iop_b)))
            f.write(iop_b)

        # PixelSpacing (0028, 0030)
        if pixel_spacing:
            ps_b = pixel_spacing.encode("ascii")
            if len(ps_b) % 2 == 1:
                ps_b += b" "
            f.write(struct.pack("<HH", 0x0028, 0x0030))
            f.write(b"DS")
            f.write(struct.pack("<H", len(ps_b)))
            f.write(ps_b)

        # ImagePositionPatient (0020, 0032)
        if ipp:
            ipp_b = ipp.encode("ascii")
            if len(ipp_b) % 2 == 1:
                ipp_b += b" "
            f.write(struct.pack("<HH", 0x0020, 0x0032))
            f.write(b"DS")
            f.write(struct.pack("<H", len(ipp_b)))
            f.write(ipp_b)

        # SliceThickness (0018, 0050)
        if slice_thickness:
            st_b = slice_thickness.encode("ascii")
            if len(st_b) % 2 == 1:
                st_b += b" "
            f.write(struct.pack("<HH", 0x0018, 0x0050))
            f.write(b"DS")
            f.write(struct.pack("<H", len(st_b)))
            f.write(st_b)

        # Write any extra elements
        if extra_elements:
            f.write(extra_elements)

        # Pixel Data (7FE0, 0010)
        f.write(struct.pack("<HH", 0x7FE0, 0x0010))
        f.write(b"OW\x00\x00")
        f.write(struct.pack("<I", len(pixel_bytes)))
        f.write(pixel_bytes)


class TestDicomStreamingAndSecurity:
    """Gate P310: Bounded streaming parser, file size limits, coordinate affine transforms, private tag screening."""

    def test_file_size_limit_quarantine(self):
        """Verify files exceeding 1GB limit trigger immediate quarantine."""
        with tempfile.NamedTemporaryFile(suffix=".dcm", delete=False) as f:
            fpath = f.name
            _create_minimal_dicom(fpath)
        try:
            # Test with mock MAX_DICOM_FILE_SIZE threshold
            import msk_therapy_os.dicom_intake as di
            orig_max = di.MAX_DICOM_FILE_SIZE
            try:
                di.MAX_DICOM_FILE_SIZE = 50  # Set low limit to test enforcement
                res = DicomHeaderParser.parse_file(fpath)
                assert not res.passed_screening
                assert DicomQuarantineReason.FILE_SIZE_EXCEEDS_LIMIT in res.quarantine_reasons
                assert res.file_size_bytes > 50
            finally:
                di.MAX_DICOM_FILE_SIZE = orig_max
        finally:
            if os.path.exists(fpath):
                os.remove(fpath)

    def test_symlink_traversal_confinement(self):
        """Verify symlinks pointing outside allowed base directory are caught."""
        with tempfile.TemporaryDirectory() as base_dir:
            inside_file = os.path.join(base_dir, "legit.dcm")
            _create_minimal_dicom(inside_file)

            with tempfile.TemporaryDirectory() as external_dir:
                external_file = os.path.join(external_dir, "outside.dcm")
                _create_minimal_dicom(external_file)

                symlink_file = os.path.join(base_dir, "symlink_outside.dcm")
                try:
                    os.symlink(external_file, symlink_file)
                    has_symlink = True
                except (OSError, NotImplementedError):
                    has_symlink = False

                if has_symlink:
                    res = DicomHeaderParser.parse_file(symlink_file, allowed_base_dir=base_dir)
                    assert not res.passed_screening
                    assert DicomQuarantineReason.PATH_TRAVERSAL_DETECTED in res.quarantine_reasons

    def test_pixel_data_boundary_overflow_detection(self):
        """Verify declared pixel data extending past file boundary triggers quarantine."""
        with tempfile.NamedTemporaryFile(suffix=".dcm", delete=False) as f:
            fpath = f.name
            # Write header with declared PixelData length 100,000 bytes, but write only 50 bytes
            f.write(b"\x00" * 128 + b"DICM")
            ts = b"1.2.840.10008.1.2.1\x00"
            f.write(struct.pack("<HH", 0x0002, 0x0010) + b"UI" + struct.pack("<H", len(ts)) + ts)
            f.write(struct.pack("<HH", 0x7FE0, 0x0010) + b"OW\x00\x00")
            f.write(struct.pack("<I", 100_000))
            f.write(b"\x00" * 50)
        try:
            res = DicomHeaderParser.parse_file(fpath)
            assert not res.passed_screening
            assert DicomQuarantineReason.MALFORMED_HEADER_STRUCTURE in res.quarantine_reasons
        finally:
            if os.path.exists(fpath):
                os.remove(fpath)

    def test_spatial_affine_matrix_computation(self):
        """Verify accurate calculation of 4x4 Affine Spatial Transformation matrix."""
        with tempfile.NamedTemporaryFile(suffix=".dcm", delete=False) as f:
            fpath = f.name
            _create_minimal_dicom(
                fpath,
                iop="1\\0\\0\\0\\1\\0",
                pixel_spacing="0.75\\0.75",
                ipp="-50.0\\-100.0\\25.0",
                slice_thickness="2.5",
            )
        try:
            res = DicomHeaderParser.parse_file(fpath)
            assert res.passed_screening
            assert res.image_orientation_patient == (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
            assert res.spatial_affine_matrix_4x4 is not None
            aff = res.spatial_affine_matrix_4x4
            assert len(aff) == 4 and len(aff[0]) == 4
            # Column direction (dc = 0.75): [0.75, 0, 0, -50.0]
            assert aff[0][0] == 0.75
            assert aff[0][3] == -50.0
            # Row direction (dr = 0.75): [0, 0.75, 0, -100.0]
            assert aff[1][1] == 0.75
            assert aff[1][3] == -100.0
            # Normal Z direction (ds = 2.5): [0, 0, 2.5, 25.0]
            assert aff[2][2] == 2.5
            assert aff[2][3] == 25.0
            assert aff[3] == [0.0, 0.0, 0.0, 1.0]
        finally:
            if os.path.exists(fpath):
                os.remove(fpath)

    def test_non_orthogonal_spatial_coordinates_quarantined(self):
        """Verify non-orthogonal direction cosines trigger MALFORMED_SPATIAL_COORDINATES."""
        with tempfile.NamedTemporaryFile(suffix=".dcm", delete=False) as f:
            fpath = f.name
            # Vectors X=[1,0,0] and Y=[0.707, 0.707, 0] (angle 45 deg, dot product ~0.707 != 0)
            _create_minimal_dicom(fpath, iop="1.0\\0.0\\0.0\\0.7071\\0.7071\\0.0")
        try:
            res = DicomHeaderParser.parse_file(fpath)
            assert not res.passed_screening
            assert DicomQuarantineReason.MALFORMED_SPATIAL_COORDINATES in res.quarantine_reasons
        finally:
            if os.path.exists(fpath):
                os.remove(fpath)

    def test_private_tag_phi_detection(self):
        """Verify odd-group private tags containing PHI tokens are quarantined."""
        # Create private tag (0019, 1010) with SSN string in standard 2-byte VR 'LO'
        phi_text = b"Confidential SSN 123-45-6789 Patient Record"
        if len(phi_text) % 2 == 1:
            phi_text += b" "
        priv_elem = struct.pack("<HH", 0x0019, 0x1010) + b"LO" + struct.pack("<H", len(phi_text)) + phi_text

        with tempfile.NamedTemporaryFile(suffix=".dcm", delete=False) as f:
            fpath = f.name
            _create_minimal_dicom(fpath, extra_elements=priv_elem)
        try:
            res = DicomHeaderParser.parse_file(fpath)
            assert not res.passed_screening
            assert DicomQuarantineReason.PRIVATE_TAG_PHI_DETECTED in res.quarantine_reasons
        finally:
            if os.path.exists(fpath):
                os.remove(fpath)


class TestDeidentificationTrustSubsystem:
    """Gate P311: Cryptographically verifiable de-identification trust authority."""

    def test_attestation_lifecycle_and_verification(self):
        """Verify full attestation issuance, HMAC signing, manifest binding, and verification."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as db_f:
            db_path = db_f.name

        try:
            auth = DeidentificationTrustAuthority(db_path=db_path)
            dataset_id = "DS-P10-3C-COHORT-A"
            file_records = [("slice_001.dcm", "abc123sha"), ("slice_002.dcm", "def456sha")]
            manifest_hash = auth.compute_dataset_manifest_hash(file_records)

            att = auth.issue_attestation(
                dataset_id=dataset_id,
                manifest_sha256=manifest_hash,
                issuing_institution="Hopital Universitaire de Geneve",
                irb_protocol_number="IRB-2026-MSK-0841",
                attestor_user_id="USR-AUDITOR-01",
                attestor_role="CLINICAL_SAFETY_AUDITOR",
                expiration_date="2027-12-31",
            )

            assert att.status == "ACTIVE"
            assert len(att.hmac_signature) == 64

            # Verify active attestation against matching manifest
            valid, msg, rec = auth.verify_dataset_attestation(dataset_id, manifest_hash)
            assert valid
            assert msg == "ATTESTATION_VERIFIED_ACTIVE"
            assert rec.attestation_id == att.attestation_id

            # Verify fail-closed on modified manifest hash
            tampered_manifest = "deadbeef" * 8
            valid_t, msg_t, _ = auth.verify_dataset_attestation(dataset_id, tampered_manifest)
            assert not valid_t
            assert "MANIFEST_HASH_MISMATCH" in msg_t

            # Verify revocation
            auth.revoke_attestation(att.attestation_id, "USR-AUDITOR-01", "Security breach suspected in source scan batch")
            valid_r, msg_r, _ = auth.verify_dataset_attestation(dataset_id, manifest_hash)
            assert not valid_r
            assert "ATTESTATION_REVOKED" in msg_r
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_unauthorized_attestor_role_rejected(self):
        """Verify that unauthorized roles cannot issue de-identification attestations."""
        auth = DeidentificationTrustAuthority()
        with pytest.raises(ValueError, match="UNAUTHORIZED_ATTESTOR"):
            auth.issue_attestation(
                dataset_id="DS-UNAUTH-01",
                manifest_sha256="0" * 64,
                issuing_institution="Unvetted Lab",
                irb_protocol_number="NONE",
                attestor_user_id="USR-STUDENT-01",
                attestor_role="student",
                expiration_date="2027-12-31",
            )


class TestGovernanceSQLiteAuditAndSignOff:
    """Gate P312: Persistent SQLite governance audit log, multi-party dual sign-off, role separation."""

    def test_governance_audit_chain_persistence_across_restarts(self):
        """Verify governance audit trail survives restart and maintains cryptographic integrity."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as db_f:
            db_path = db_f.name

        try:
            # 1. Initialize validator with db and record actions
            val1 = IndependentAnatomicalValidator(db_path=db_path)
            ds = ExternalGroundTruthDataset(
                dataset_id="DS-AUDIT-PERSIST-01",
                name="Audit Persistence Test Dataset",
                source_organization="MSK Independent QA",
                version="1.0-P10",
                license="MIT",
                doi_or_url="doi:10.1000/persist01",
                modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
            )
            val1.register_dataset(ds)
            val1.admin_sign_off_dataset("DS-AUDIT-PERSIST-01", "REV-CLINICAL-AUDITOR", justification="Initial approval")
            trail1 = val1.get_governance_audit_trail()
            assert len(trail1) >= 1
            assert val1.verify_governance_audit_chain()

            # 2. Re-instantiate new validator pointing to same db (simulating process restart)
            val2 = IndependentAnatomicalValidator(db_path=db_path)
            trail2 = val2.get_governance_audit_trail()
            assert len(trail2) == len(trail1)
            assert trail2[-1]["entry_hash"] == trail1[-1]["entry_hash"]
            assert val2.verify_governance_audit_chain()
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_governance_role_conflict_curator_self_sign_off(self):
        """Verify data curator cannot sign off on their own dataset."""
        val = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-CONFLICT-01",
            name="Conflict Test Dataset",
            source_organization="MSK QA",
            version="1.0",
            license="MIT",
            doi_or_url="doi:10.1000/conflict",
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
            governance_metadata={"curator_id": "REV-CLINICAL-AUDITOR"}
        )
        val.register_dataset(ds)

        with pytest.raises(ValueError, match="GOVERNANCE_ROLE_CONFLICT"):
            val.admin_sign_off_dataset("DS-CONFLICT-01", "REV-CLINICAL-AUDITOR")

    def test_governance_dual_cosigning_must_be_distinct(self):
        """Verify co-signer must be a distinct individual."""
        val = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-COSIGN-01",
            name="Co-sign Test Dataset",
            source_organization="MSK QA",
            version="1.0",
            license="MIT",
            doi_or_url="doi:10.1000/cosign",
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
        )
        val.register_dataset(ds)

        with pytest.raises(ValueError, match="CO_SIGNER_CONFLICT"):
            val.admin_sign_off_dataset("DS-COSIGN-01", "REV-CLINICAL-AUDITOR", cosigner_id="REV-CLINICAL-AUDITOR")

        # Distinct co-signer succeeds
        success = val.admin_sign_off_dataset("DS-COSIGN-01", "REV-CLINICAL-AUDITOR", cosigner_id="REV-LEAD-ANATOMIST")
        assert success
        assert val.verify_governance_audit_chain()

    def test_governance_session_authentication_enforcement(self):
        """Verify administrative sign-off validates active admin session token when auth db provided."""
        val = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-AUTH-SESS-01",
            name="Auth Session Test Dataset",
            source_organization="MSK QA",
            version="1.0",
            license="MIT",
            doi_or_url="doi:10.1000/authsess",
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
        )
        val.register_dataset(ds)

        # Create temporary auth db in memory
        auth_conn = sqlite3.connect(":memory:")
        init_auth_tables(auth_conn)
        admin_user = create_user(
            auth_conn, username="admin_gov", password="StrongPassword123!",
            role="admin", display_name="Admin Governance Officer"
        )
        admin_sess = create_session(auth_conn, admin_user["user_id"])
        
        student_user = create_user(
            auth_conn, username="student_gov", password="StudentPassword123!",
            role="student", display_name="Student Researcher"
        )
        student_sess = create_session(auth_conn, student_user["user_id"])

        # Signing off with student session fails
        with pytest.raises(ValueError, match="INVALID_SESSION_AUTH"):
            val.admin_sign_off_dataset(
                "DS-AUTH-SESS-01", "REV-CLINICAL-AUDITOR",
                session_token=student_sess["session_token"], auth_db=auth_conn
            )

        # Signing off with admin session succeeds
        success = val.admin_sign_off_dataset(
            "DS-AUTH-SESS-01", "REV-CLINICAL-AUDITOR",
            session_token=admin_sess["session_token"], auth_db=auth_conn
        )
        assert success
        assert val.verify_governance_audit_chain()


class TestHoldoutIsolationAndLongitudinalLeakage:
    """Gate P314: Longitudinal holdout partition isolation and zero leakage."""

    def test_holdout_partition_longitudinal_isolation(self):
        """Verify multiple scans for the same patient are strictly confined to one partition."""
        mgr = HoldoutPartitionManager()
        # 30 subjects: SUBJ-001 through SUBJ-030
        subjects = [f"SUBJ-{i:03d}" for i in range(1, 31)]
        partition = mgr.create_partition("DS-LONGITUDINAL-01", subjects, holdout_ratio=0.3, seed=20261030)

        # Check total count and disjointness
        assert len(partition.calibration_subjects) + len(partition.holdout_subjects) == 30
        cal_set = set(partition.calibration_subjects)
        hold_set = set(partition.holdout_subjects)
        assert cal_set.isdisjoint(hold_set)

        # Verify longitudinal containment: each subject is in exactly one partition
        for s in subjects:
            in_cal = s in cal_set
            in_hold = s in hold_set
            assert in_cal ^ in_hold  # Exclusive OR: exactly one must be True
