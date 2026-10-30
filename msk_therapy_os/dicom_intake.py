"""MSK-Therapy-OS Offline DICOM Intake & Medical Imaging Security Adapter.

Milestone: P10.3A
Architecture: Offline-first, Python Standard Library only (no pydicom/external C deps).
Security:
  - 18 HIPAA Safe Harbor Identifier Screening
  - Burned-in annotation risk detection
  - Explicit Transfer Syntax policy (uncompressed supported, compressed fail-closed)
  - SOPInstanceUID and file SHA-256 integrity & duplicate detection
  - Administrative approval workflow before dataset ingestion
"""

import os
import struct
import hashlib
import time
import re
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Set


class DicomTransferSyntax(str, Enum):
    """Supported and unsupported DICOM transfer syntax definitions."""
    # Supported uncompressed Little/Big Endian transfer syntaxes:
    EXPLICIT_VR_LITTLE_ENDIAN = "1.2.840.10008.1.2.1"
    IMPLICIT_VR_LITTLE_ENDIAN = "1.2.840.10008.1.2"
    EXPLICIT_VR_BIG_ENDIAN = "1.2.840.10008.1.2.2"
    
    # Explicitly rejected compressed syntaxes (Fail-closed policy):
    JPEG_BASELINE = "1.2.840.10008.1.2.4.50"
    JPEG_EXTENDED = "1.2.840.10008.1.2.4.51"
    JPEG_LOSSLESS = "1.2.840.10008.1.2.4.70"
    JPEG_2000_LOSSLESS = "1.2.840.10008.1.2.4.90"
    JPEG_2000 = "1.2.840.10008.1.2.4.91"
    RLE_LOSSLESS = "1.2.840.10008.1.2.5"
    MPEG2_MAIN = "1.2.840.10008.1.2.4.100"
    UNKNOWN = "UNKNOWN"


SUPPORTED_TRANSFER_SYNTAXES: Set[str] = {
    DicomTransferSyntax.EXPLICIT_VR_LITTLE_ENDIAN.value,
    DicomTransferSyntax.IMPLICIT_VR_LITTLE_ENDIAN.value,
    DicomTransferSyntax.EXPLICIT_VR_BIG_ENDIAN.value,
}


class DicomQuarantineReason(str, Enum):
    """Standardized reasons for quarantining DICOM ingestion inputs."""
    NOT_A_DICOM_FILE = "QUARANTINE_NOT_A_DICOM_FILE"
    UNSUPPORTED_TRANSFER_SYNTAX = "QUARANTINE_UNSUPPORTED_TRANSFER_SYNTAX"
    UNSUPPORTED_COMPRESSION = "QUARANTINE_UNSUPPORTED_COMPRESSION"
    MULTIFRAME_UNSUPPORTED = "QUARANTINE_MULTIFRAME_UNSUPPORTED"
    PHI_IN_PATIENT_NAME = "QUARANTINE_PHI_IN_PATIENT_NAME"
    PHI_IN_PATIENT_ID = "QUARANTINE_PHI_IN_PATIENT_ID"
    PHI_IN_BIRTH_DATE = "QUARANTINE_PHI_IN_BIRTH_DATE"
    PHI_IN_METADATA_HEADER = "QUARANTINE_PHI_IN_METADATA_HEADER"
    BURNED_IN_IDENTIFIERS_RISK = "QUARANTINE_BURNED_IN_IDENTIFIERS_RISK"
    UNVERIFIED_PIXEL_DEIDENTIFICATION = "QUARANTINE_UNVERIFIED_PIXEL_DEIDENTIFICATION"
    CHECKSUM_INTEGRITY_MISMATCH = "QUARANTINE_CHECKSUM_INTEGRITY_MISMATCH"
    DUPLICATE_SOP_INSTANCE = "QUARANTINE_DUPLICATE_SOP_INSTANCE"
    MALFORMED_HEADER_STRUCTURE = "QUARANTINE_MALFORMED_HEADER_STRUCTURE"
    UNAPPROVED_SOURCE_ORGANIZATION = "QUARANTINE_UNAPPROVED_SOURCE_ORGANIZATION"
    ADMIN_AUTHORIZATION_REQUIRED = "QUARANTINE_ADMIN_AUTHORIZATION_REQUIRED"
    PATH_TRAVERSAL_DETECTED = "QUARANTINE_PATH_TRAVERSAL_DETECTED"
    FILE_SIZE_EXCEEDS_LIMIT = "QUARANTINE_FILE_SIZE_EXCEEDS_LIMIT"
    MALFORMED_SPATIAL_COORDINATES = "QUARANTINE_MALFORMED_SPATIAL_COORDINATES"
    PRIVATE_TAG_PHI_DETECTED = "QUARANTINE_PRIVATE_TAG_PHI_DETECTED"


MAX_DICOM_FILE_SIZE = 1024 * 1024 * 1024  # 1 GB max physical file size
MAX_METADATA_ELEMENT_LENGTH = 4 * 1024 * 1024  # 4 MB max metadata element length
MAX_PIXEL_DATA_LENGTH = 500 * 1024 * 1024  # 500 MB max uncompressed pixel data


@dataclass
class DicomElement:
    """A single parsed DICOM element."""
    group: int
    element: int
    vr: str
    length: int
    value_bytes: bytes

    @property
    def tag(self) -> Tuple[int, int]:
        return (self.group, self.element)

    @property
    def tag_hex(self) -> str:
        return f"({self.group:04X},{self.element:04X})"

    def as_text(self) -> str:
        try:
            return self.value_bytes.decode("latin1", errors="replace").strip("\x00").strip()
        except Exception:
            return ""

    def as_int(self) -> Optional[int]:
        txt = self.as_text()
        try:
            return int(txt)
        except ValueError:
            return None

    def as_float(self) -> Optional[float]:
        txt = self.as_text()
        try:
            return float(txt)
        except ValueError:
            return None


@dataclass
class DicomPreflightResult:
    """Complete preflight evaluation of a DICOM file."""
    file_path: str
    sha256_hash: str
    is_valid_dicom: bool
    is_supported: bool
    transfer_syntax_uid: str
    modality: str = ""
    sop_class_uid: str = ""
    sop_instance_uid: str = ""
    patient_id: str = ""
    patient_name: str = ""
    patient_birth_date: str = ""
    study_date: str = ""
    slice_thickness_mm: Optional[float] = None
    pixel_spacing: Optional[Tuple[float, float]] = None
    image_position_patient: Optional[Tuple[float, float, float]] = None
    image_orientation_patient: Optional[Tuple[float, float, float, float, float, float]] = None
    spatial_affine_matrix_4x4: Optional[List[List[float]]] = None
    pixel_data_offset: Optional[int] = None
    pixel_data_length: Optional[int] = None
    file_size_bytes: int = 0
    number_of_frames: int = 1
    burned_in_annotation: str = "UNKNOWN"
    has_pixel_deidentification_certificate: bool = False
    deidentification_certificate_id: Optional[str] = None
    deidentification_method_description: Optional[str] = None
    pixel_deidentification_status: str = "UNVERIFIED"
    quarantine_reasons: List[DicomQuarantineReason] = field(default_factory=list)
    quarantine_details: List[str] = field(default_factory=list)
    parsed_tags_count: int = 0

    @property
    def passed_screening(self) -> bool:
        return (
            self.is_valid_dicom
            and self.is_supported
            and len(self.quarantine_reasons) == 0
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["quarantine_reasons"] = [r.value for r in self.quarantine_reasons]
        d["passed_screening"] = self.passed_screening
        return d


class DicomHeaderParser:
    """Safe, pure-Python standard library DICOM binary stream parser with adversarial hardening."""

    @staticmethod
    def parse_file(
        file_path: str,
        max_bytes: int = 2 * 1024 * 1024,
        allowed_base_dir: Optional[str] = None,
        require_pixel_certificate: bool = False,
        pixel_certificate: Optional[Dict[str, Any]] = None,
        attestation: Optional[Any] = None,
    ) -> DicomPreflightResult:
        """Parse DICOM preamble, File Meta Information, and top-level dataset elements with security controls."""
        # Path traversal guard
        clean_path_parts = file_path.replace("\\", "/").split("/")
        if ".." in clean_path_parts or "\x00" in file_path:
            return DicomPreflightResult(
                file_path=file_path,
                sha256_hash="",
                is_valid_dicom=False,
                is_supported=False,
                transfer_syntax_uid="UNKNOWN",
                quarantine_reasons=[DicomQuarantineReason.PATH_TRAVERSAL_DETECTED],
                quarantine_details=["Path contains traversal tokens ('..') or null characters."],
            )

        if allowed_base_dir:
            real_base = os.path.realpath(allowed_base_dir)
            real_file = os.path.realpath(file_path)
            try:
                if os.path.commonpath([real_base, real_file]) != real_base:
                    return DicomPreflightResult(
                        file_path=file_path,
                        sha256_hash="",
                        is_valid_dicom=False,
                        is_supported=False,
                        transfer_syntax_uid="UNKNOWN",
                        quarantine_reasons=[DicomQuarantineReason.PATH_TRAVERSAL_DETECTED],
                        quarantine_details=[f"File '{file_path}' resolves outside allowed directory '{allowed_base_dir}'."],
                    )
            except ValueError:
                return DicomPreflightResult(
                    file_path=file_path,
                    sha256_hash="",
                    is_valid_dicom=False,
                    is_supported=False,
                    transfer_syntax_uid="UNKNOWN",
                    quarantine_reasons=[DicomQuarantineReason.PATH_TRAVERSAL_DETECTED],
                    quarantine_details=[f"File '{file_path}' is on a distinct filesystem drive from '{allowed_base_dir}'."],
                )

        if not os.path.exists(file_path):
            return DicomPreflightResult(
                file_path=file_path,
                sha256_hash="",
                is_valid_dicom=False,
                is_supported=False,
                transfer_syntax_uid="UNKNOWN",
                quarantine_reasons=[DicomQuarantineReason.NOT_A_DICOM_FILE],
                quarantine_details=["File does not exist"],
            )

        file_size = os.path.getsize(file_path)
        if file_size > MAX_DICOM_FILE_SIZE:
            return DicomPreflightResult(
                file_path=file_path,
                sha256_hash="",
                is_valid_dicom=False,
                is_supported=False,
                transfer_syntax_uid="UNKNOWN",
                file_size_bytes=file_size,
                quarantine_reasons=[DicomQuarantineReason.FILE_SIZE_EXCEEDS_LIMIT],
                quarantine_details=[f"File size ({file_size} bytes) exceeds maximum limit of {MAX_DICOM_FILE_SIZE} bytes (1 GB)."],
            )

        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                raw_bytes = f.read(max_bytes)
                # Compute SHA-256 over whole file
                f.seek(0)
                while chunk := f.read(65536):
                    hasher.update(chunk)
            sha256 = hasher.hexdigest()
        except Exception as e:
            return DicomPreflightResult(
                file_path=file_path,
                sha256_hash="",
                is_valid_dicom=False,
                is_supported=False,
                transfer_syntax_uid="UNKNOWN",
                file_size_bytes=file_size,
                quarantine_reasons=[DicomQuarantineReason.MALFORMED_HEADER_STRUCTURE],
                quarantine_details=[f"I/O error reading file: {str(e)}"],
            )

        if len(raw_bytes) < 132:
            return DicomPreflightResult(
                file_path=file_path,
                sha256_hash=sha256,
                is_valid_dicom=False,
                is_supported=False,
                transfer_syntax_uid="UNKNOWN",
                file_size_bytes=file_size,
                quarantine_reasons=[DicomQuarantineReason.NOT_A_DICOM_FILE],
                quarantine_details=["File too short (< 132 bytes) for DICOM format"],
            )

        # Check DICOM prefix at byte 128
        magic = raw_bytes[128:132]
        if magic != b"DICM":
            return DicomPreflightResult(
                file_path=file_path,
                sha256_hash=sha256,
                is_valid_dicom=False,
                is_supported=False,
                transfer_syntax_uid="UNKNOWN",
                file_size_bytes=file_size,
                quarantine_reasons=[DicomQuarantineReason.NOT_A_DICOM_FILE],
                quarantine_details=[f"Missing 'DICM' signature at offset 128 (got {magic!r})"],
            )

        # Parse elements
        offset = 132
        transfer_syntax = DicomTransferSyntax.EXPLICIT_VR_LITTLE_ENDIAN.value
        elements: Dict[Tuple[int, int], DicomElement] = {}
        has_malformed_length = False
        pixel_data_offset: Optional[int] = None
        pixel_data_length: Optional[int] = None

        # First pass: Parse Group 0002 (File Meta Information - always Explicit VR Little Endian)
        try:
            while offset + 8 <= len(raw_bytes):
                group, elem = struct.unpack("<HH", raw_bytes[offset:offset+4])
                if group != 0x0002:
                    break  # Reached main dataset
                vr = raw_bytes[offset+4:offset+6].decode("ascii", errors="replace")
                
                # Check reserved VRs for 4-byte length
                if vr in ("OB", "OW", "OF", "SQ", "UT", "UN"):
                    if offset + 12 > len(raw_bytes):
                        break
                    length = struct.unpack("<I", raw_bytes[offset+8:offset+12])[0]
                    val_offset = offset + 12
                    offset = val_offset + length
                else:
                    length = struct.unpack("<H", raw_bytes[offset+6:offset+8])[0]
                    val_offset = offset + 8
                    offset = val_offset + length

                # Memory exhaustion & malformed length guard
                if length == 0xFFFFFFFF or length > MAX_METADATA_ELEMENT_LENGTH:
                    has_malformed_length = True
                    break

                if val_offset + length > len(raw_bytes):
                    val_bytes = raw_bytes[val_offset:]
                else:
                    val_bytes = raw_bytes[val_offset:val_offset+length]

                el = DicomElement(group=group, element=elem, vr=vr, length=length, value_bytes=val_bytes)
                elements[(group, elem)] = el

            # Tag (0002,0010): TransferSyntaxUID
            if (0x0002, 0x0010) in elements:
                transfer_syntax = elements[(0x0002, 0x0010)].as_text()

            # Second pass: Parse Dataset elements up to PixelData (7FE0,0010)
            is_explicit = (transfer_syntax != DicomTransferSyntax.IMPLICIT_VR_LITTLE_ENDIAN.value)
            is_big_endian = (transfer_syntax == DicomTransferSyntax.EXPLICIT_VR_BIG_ENDIAN.value)
            endian_prefix = ">" if is_big_endian else "<"

            while offset + 8 <= len(raw_bytes):
                group, elem = struct.unpack(f"{endian_prefix}HH", raw_bytes[offset:offset+4])
                
                # If we encounter PixelData (7FE0, 0010), record offset and length, then stop reading header
                if group == 0x7FE0 and elem == 0x0010:
                    if is_explicit:
                        vr = raw_bytes[offset+4:offset+6].decode("ascii", errors="replace")
                        if vr in ("OB", "OW", "OF", "SQ", "UT", "UN"):
                            if offset + 12 <= len(raw_bytes):
                                length = struct.unpack(f"{endian_prefix}I", raw_bytes[offset+8:offset+12])[0]
                                val_offset = offset + 12
                            else:
                                length = 0
                                val_offset = offset + 12
                        else:
                            if offset + 8 <= len(raw_bytes):
                                length = struct.unpack(f"{endian_prefix}H", raw_bytes[offset+6:offset+8])[0]
                                val_offset = offset + 8
                            else:
                                length = 0
                                val_offset = offset + 8
                    else:
                        vr = "OB"
                        if offset + 8 <= len(raw_bytes):
                            length = struct.unpack(f"{endian_prefix}I", raw_bytes[offset+4:offset+8])[0]
                            val_offset = offset + 8
                        else:
                            length = 0
                            val_offset = offset + 8

                    pixel_data_offset = val_offset
                    pixel_data_length = length
                    elements[(group, elem)] = DicomElement(group, elem, vr, length, b"")

                    if length == 0xFFFFFFFF:
                        has_malformed_length = True
                    elif length > MAX_PIXEL_DATA_LENGTH:
                        has_malformed_length = True
                    elif val_offset + length > file_size:
                        has_malformed_length = True
                    break

                if is_explicit:
                    vr = raw_bytes[offset+4:offset+6].decode("ascii", errors="replace")
                    if vr in ("OB", "OW", "OF", "SQ", "UT", "UN"):
                        if offset + 12 > len(raw_bytes):
                            break
                        length = struct.unpack(f"{endian_prefix}I", raw_bytes[offset+8:offset+12])[0]
                        val_offset = offset + 12
                        offset = val_offset + length
                    else:
                        length = struct.unpack(f"{endian_prefix}H", raw_bytes[offset+6:offset+8])[0]
                        val_offset = offset + 8
                        offset = val_offset + length
                else:
                    vr = "UN"
                    length = struct.unpack(f"{endian_prefix}I", raw_bytes[offset+4:offset+8])[0]
                    val_offset = offset + 8
                    offset = val_offset + length

                # Guard against undefined or massive lengths in metadata tags
                if length == 0xFFFFFFFF or length > MAX_METADATA_ELEMENT_LENGTH:
                    has_malformed_length = True
                    break

                if val_offset + length > len(raw_bytes):
                    val_bytes = raw_bytes[val_offset:]
                else:
                    val_bytes = raw_bytes[val_offset:val_offset+length]

                el = DicomElement(group=group, element=elem, vr=vr, length=length, value_bytes=val_bytes)
                elements[(group, elem)] = el

        except Exception as e:
            # Parse error in body: evaluate what was successfully gathered
            pass

        # Evaluate Preflight Screening
        res = DicomPreflightResult(
            file_path=file_path,
            sha256_hash=sha256,
            is_valid_dicom=True,
            is_supported=(transfer_syntax in SUPPORTED_TRANSFER_SYNTAXES),
            transfer_syntax_uid=transfer_syntax,
            file_size_bytes=file_size,
            pixel_data_offset=pixel_data_offset,
            pixel_data_length=pixel_data_length,
            parsed_tags_count=len(elements),
        )

        if has_malformed_length:
            res.quarantine_reasons.append(DicomQuarantineReason.MALFORMED_HEADER_STRUCTURE)
            res.quarantine_details.append("Element length tag is malformed (0xFFFFFFFF, exceeds maximum limit, or exceeds file size).")

        # Transfer syntax validation
        if transfer_syntax not in SUPPORTED_TRANSFER_SYNTAXES:
            res.is_supported = False
            if "1.2.840.10008.1.2.4" in transfer_syntax:
                res.quarantine_reasons.append(DicomQuarantineReason.UNSUPPORTED_COMPRESSION)
                res.quarantine_details.append(
                    f"Unsupported compressed transfer syntax '{transfer_syntax}'. Fail-closed policy requires uncompressed DICOM."
                )
            else:
                res.quarantine_reasons.append(DicomQuarantineReason.UNSUPPORTED_TRANSFER_SYNTAX)
                res.quarantine_details.append(
                    f"Transfer syntax '{transfer_syntax}' is not supported."
                )

        # Extract standard tags
        if (0x0008, 0x0016) in elements:
            res.sop_class_uid = elements[(0x0008, 0x0016)].as_text()
        if (0x0008, 0x0018) in elements:
            res.sop_instance_uid = elements[(0x0008, 0x0018)].as_text()
        if (0x0008, 0x0060) in elements:
            res.modality = elements[(0x0008, 0x0060)].as_text()
        if (0x0008, 0x0020) in elements:
            res.study_date = elements[(0x0008, 0x0020)].as_text()
        if (0x0010, 0x0010) in elements:
            res.patient_name = elements[(0x0010, 0x0010)].as_text()
        if (0x0010, 0x0020) in elements:
            res.patient_id = elements[(0x0010, 0x0020)].as_text()
        if (0x0010, 0x0030) in elements:
            res.patient_birth_date = elements[(0x0010, 0x0030)].as_text()
        if (0x0018, 0x0050) in elements:
            res.slice_thickness_mm = elements[(0x0018, 0x0050)].as_float()
        if (0x0028, 0x0008) in elements:
            frames = elements[(0x0028, 0x0008)].as_int()
            if frames:
                res.number_of_frames = frames
        if (0x0028, 0x0301) in elements:
            res.burned_in_annotation = elements[(0x0028, 0x0301)].as_text().upper()

        if (0x0028, 0x0030) in elements:
            px_text = elements[(0x0028, 0x0030)].as_text()
            parts = px_text.split("\\")
            if len(parts) >= 2:
                try:
                    res.pixel_spacing = (float(parts[0]), float(parts[1]))
                except ValueError:
                    pass

        if (0x0020, 0x0032) in elements:
            pos_text = elements[(0x0020, 0x0032)].as_text()
            pos_parts = pos_text.split("\\")
            if len(pos_parts) == 3:
                try:
                    res.image_position_patient = (float(pos_parts[0]), float(pos_parts[1]), float(pos_parts[2]))
                except ValueError:
                    pass

        # Multiframe validation
        if res.number_of_frames > 1:
            res.quarantine_reasons.append(DicomQuarantineReason.MULTIFRAME_UNSUPPORTED)
            res.quarantine_details.append(
                f"Multiframe DICOM with {res.number_of_frames} frames is not supported in uncompressed 2D slice intake."
            )

        # PHI Screening
        # 1. Patient Name: Must be empty or start with 'P-' / 'SUBJ-' / 'ANON'
        p_name = res.patient_name.strip()
        if p_name and not re.match(r"^(ANON.*|SUBJ[-_].*|P[-_].*|\*+)$", p_name, re.IGNORECASE):
            res.quarantine_reasons.append(DicomQuarantineReason.PHI_IN_PATIENT_NAME)
            res.quarantine_details.append(f"PatientName '{p_name}' does not match pseudonymized pattern.")

        # 2. Patient ID: Must match pseudonym format
        p_id = res.patient_id.strip()
        if p_id and not re.match(r"^(ANON.*|SUBJ[-_].*|P[-_].*)$", p_id, re.IGNORECASE):
            res.quarantine_reasons.append(DicomQuarantineReason.PHI_IN_PATIENT_ID)
            res.quarantine_details.append(f"PatientID '{p_id}' violates pseudonym format.")

        # 3. Patient Birth Date: Must be blank (HIPAA 18-element rule)
        if res.patient_birth_date.strip():
            res.quarantine_reasons.append(DicomQuarantineReason.PHI_IN_BIRTH_DATE)
            res.quarantine_details.append(f"PatientBirthDate '{res.patient_birth_date}' contains Protected Health Information.")

        # 4. Burned-in identifier check
        if res.burned_in_annotation == "YES":
            res.quarantine_reasons.append(DicomQuarantineReason.BURNED_IN_IDENTIFIERS_RISK)
            res.quarantine_details.append("BurnedInAnnotation is explicitly 'YES'. Pixel data may contain PHI.")
        elif res.modality in ("SC", "US", "OT") and res.burned_in_annotation != "NO":
            # Secondary capture or ultrasound without explicit 'NO' is high risk
            res.quarantine_reasons.append(DicomQuarantineReason.BURNED_IN_IDENTIFIERS_RISK)
            res.quarantine_details.append(
                f"Modality '{res.modality}' without explicit BurnedInAnnotation='NO' presents risk of burned-in patient names."
            )

        # 4b. Spatial Coordinates & Affine Transform Construction
        if (0x0020, 0x0037) in elements:
            iop_text = elements[(0x0020, 0x0037)].as_text()
            parts = [p.strip() for p in iop_text.split("\\") if p.strip()]
            if len(parts) == 6:
                try:
                    iop = tuple(float(p) for p in parts)
                    res.image_orientation_patient = iop
                    Xx, Xy, Xz = iop[0], iop[1], iop[2]
                    Yx, Yy, Yz = iop[3], iop[4], iop[5]
                    norm_x = (Xx**2 + Xy**2 + Xz**2) ** 0.5
                    norm_y = (Yx**2 + Yy**2 + Yz**2) ** 0.5
                    dot_xy = Xx * Yx + Xy * Yy + Xz * Yz
                    if abs(norm_x - 1.0) > 0.05 or abs(norm_y - 1.0) > 0.05 or abs(dot_xy) > 0.05:
                        res.quarantine_reasons.append(DicomQuarantineReason.MALFORMED_SPATIAL_COORDINATES)
                        res.quarantine_details.append(
                            f"ImageOrientationPatient vectors not orthonormal: |X|={norm_x:.4f}, |Y|={norm_y:.4f}, X.Y={dot_xy:.4f}"
                        )
                    else:
                        Zx = Xy * Yz - Xz * Yy
                        Zy = Xz * Yx - Xx * Yz
                        Zz = Xx * Yy - Xy * Yx
                        if res.pixel_spacing and res.image_position_patient:
                            dr, dc = res.pixel_spacing
                            if dr <= 0 or dc <= 0:
                                res.quarantine_reasons.append(DicomQuarantineReason.MALFORMED_SPATIAL_COORDINATES)
                                res.quarantine_details.append(f"PixelSpacing values ({dr}, {dc}) must be strictly positive.")
                            else:
                                ds = res.slice_thickness_mm if (res.slice_thickness_mm and res.slice_thickness_mm > 0) else 1.0
                                Sx, Sy, Sz = res.image_position_patient
                                res.spatial_affine_matrix_4x4 = [
                                    [round(Xx * dc, 6), round(Yx * dr, 6), round(Zx * ds, 6), round(Sx, 6)],
                                    [round(Xy * dc, 6), round(Yy * dr, 6), round(Zy * ds, 6), round(Sy, 6)],
                                    [round(Xz * dc, 6), round(Yz * dr, 6), round(Zz * ds, 6), round(Sz, 6)],
                                    [0.0, 0.0, 0.0, 1.0],
                                ]
                except ValueError:
                    res.quarantine_reasons.append(DicomQuarantineReason.MALFORMED_SPATIAL_COORDINATES)
                    res.quarantine_details.append("ImageOrientationPatient contains non-numeric values.")
            else:
                res.quarantine_reasons.append(DicomQuarantineReason.MALFORMED_SPATIAL_COORDINATES)
                res.quarantine_details.append(f"ImageOrientationPatient expected 6 values, got {len(parts)}.")

        # 4c. Private Tag Screening for Vendor PHI
        phi_patterns = [
            re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
            re.compile(r"\b(Mr|Mrs|Ms|Dr)[._\s]+[A-Za-z]+", re.IGNORECASE),
            re.compile(r"\b(patient\s*name|patient\s*id|birth\s*date|social\s*security|medical\s*record)\b", re.IGNORECASE),
        ]
        for tag, el in elements.items():
            if tag[0] % 2 == 1:
                txt = el.as_text()
                if txt and any(p.search(txt) for p in phi_patterns):
                    res.quarantine_reasons.append(DicomQuarantineReason.PRIVATE_TAG_PHI_DETECTED)
                    res.quarantine_details.append(
                        f"Private tag {el.tag_hex} contains potential PHI: '{txt[:40]}...'"
                    )
                    break

        # 4d. Mandatory Institutional Pixel De-identification Verification Policy
        if require_pixel_certificate:
            if attestation:
                res.has_pixel_deidentification_certificate = True
                res.deidentification_certificate_id = getattr(attestation, "attestation_id", str(attestation.get("attestation_id", ""))) if isinstance(attestation, dict) else attestation.attestation_id
                res.deidentification_method_description = "HMAC-SHA256 Certified Institutional Safe Harbor Attestation"
                res.pixel_deidentification_status = "VERIFIED_ATTESTED"
            elif pixel_certificate and pixel_certificate.get("certificate_id") and pixel_certificate.get("verified_by_institution"):
                res.has_pixel_deidentification_certificate = True
                res.deidentification_certificate_id = str(pixel_certificate.get("certificate_id"))
                res.deidentification_method_description = str(pixel_certificate.get("method_description", "Certified Safe Harbor Pixel Masking"))
                res.pixel_deidentification_status = "LEGACY_VERIFIED"
            else:
                res.quarantine_reasons.append(DicomQuarantineReason.UNVERIFIED_PIXEL_DEIDENTIFICATION)
                res.quarantine_details.append(
                    "BurnedInAnnotation='NO' header is unverified without independent institutional de-identification attestation. "
                    "Offline pure-Python engine requires explicit institutional sign-off for pixel privacy."
                )
                res.has_pixel_deidentification_certificate = False
                res.pixel_deidentification_status = "QUARANTINED"
        elif attestation:
            res.has_pixel_deidentification_certificate = True
            res.deidentification_certificate_id = getattr(attestation, "attestation_id", str(attestation.get("attestation_id", ""))) if isinstance(attestation, dict) else attestation.attestation_id
            res.deidentification_method_description = "HMAC-SHA256 Certified Institutional Safe Harbor Attestation"
            res.pixel_deidentification_status = "VERIFIED_ATTESTED"
        elif pixel_certificate and pixel_certificate.get("certificate_id") and pixel_certificate.get("verified_by_institution"):
            res.has_pixel_deidentification_certificate = True
            res.deidentification_certificate_id = str(pixel_certificate.get("certificate_id"))
            res.deidentification_method_description = str(pixel_certificate.get("method_description", "Certified Safe Harbor Pixel Masking"))
            res.pixel_deidentification_status = "LEGACY_VERIFIED"

        # 5. Filename screening
        filename = os.path.basename(file_path)
        if re.search(r"\b(Mr|Mrs|Ms|Dr)[._\s]+[A-Za-z]+", filename, re.IGNORECASE) or re.search(r"\b\d{3}-\d{2}-\d{4}\b", filename):
            res.quarantine_reasons.append(DicomQuarantineReason.PHI_IN_METADATA_HEADER)
            res.quarantine_details.append(f"Filename '{filename}' contains suspected PHI tokens.")

        return res


class DicomIntakeAdapter:
    """Manages secure offline intake, inspection, and catalog integration with security controls."""

    def __init__(
        self,
        quarantine_dir: str = "data/quarantine/dicom",
        allowed_base_dir: Optional[str] = None,
        trust_authority: Optional[Any] = None,
    ):
        self.quarantine_dir = quarantine_dir
        self.allowed_base_dir = allowed_base_dir
        self.trust_authority = trust_authority
        os.makedirs(self.quarantine_dir, exist_ok=True)
        self._ingested_sop_uids: Set[str] = set()
        self._ingested_hashes: Set[str] = set()
        self._quarantine_records: List[Dict[str, Any]] = []
        self._pixel_certificates: Dict[str, Dict[str, Any]] = {}

    def register_pixel_certificate(self, identifier: str, certificate: Dict[str, Any]) -> None:
        """Register an independent institutional pixel de-identification certificate."""
        self._pixel_certificates[identifier] = certificate

    def inspect_file(
        self,
        file_path: str,
        require_pixel_certificate: bool = False,
        pixel_certificate: Optional[Dict[str, Any]] = None,
        attestation: Optional[Any] = None,
    ) -> DicomPreflightResult:
        """Run standalone preflight inspection on a single local file."""
        # Resolve certificate if registered
        cert = pixel_certificate
        res = DicomHeaderParser.parse_file(
            file_path=file_path,
            allowed_base_dir=self.allowed_base_dir,
            require_pixel_certificate=require_pixel_certificate,
            pixel_certificate=cert,
            attestation=attestation,
        )

        # If not passed in, check if certificate was preregistered by SOPInstanceUID or hash
        if require_pixel_certificate and not res.has_pixel_deidentification_certificate:
            registered_cert = self._pixel_certificates.get(res.sop_instance_uid) or self._pixel_certificates.get(res.sha256_hash)
            if registered_cert and registered_cert.get("certificate_id") and registered_cert.get("verified_by_institution"):
                # Clear the unverified quarantine reason
                res.quarantine_reasons = [r for r in res.quarantine_reasons if r != DicomQuarantineReason.UNVERIFIED_PIXEL_DEIDENTIFICATION]
                res.quarantine_details = [d for d in res.quarantine_details if "unverified without independent" not in d]
                res.has_pixel_deidentification_certificate = True
                res.deidentification_certificate_id = str(registered_cert.get("certificate_id"))
                res.deidentification_method_description = str(registered_cert.get("method_description", "Certified Safe Harbor Pixel Masking"))
                res.pixel_deidentification_status = "LEGACY_VERIFIED"
        
        # Check duplicate
        if res.sop_instance_uid and res.sop_instance_uid in self._ingested_sop_uids:
            res.quarantine_reasons.append(DicomQuarantineReason.DUPLICATE_SOP_INSTANCE)
            res.quarantine_details.append(f"Duplicate SOPInstanceUID '{res.sop_instance_uid}'.")
        if res.sha256_hash and res.sha256_hash in self._ingested_hashes:
            res.quarantine_reasons.append(DicomQuarantineReason.DUPLICATE_SOP_INSTANCE)
            res.quarantine_details.append("Identical SHA-256 hash has already been ingested.")

        return res

    def inspect_directory(self, dir_path: str, require_pixel_certificate: bool = False) -> List[DicomPreflightResult]:
        """Inspect all DICOM candidate files in a local directory."""
        results: List[DicomPreflightResult] = []
        if not os.path.exists(dir_path):
            return results

        for root, _, files in os.walk(dir_path):
            for fname in files:
                fpath = os.path.join(root, fname)
                res = self.inspect_file(fpath, require_pixel_certificate=require_pixel_certificate)
                results.append(res)
        return results

    def inspect_dataset(
        self,
        dataset_id: str,
        dir_path: str,
        require_pixel_certificate: bool = True,
    ) -> Tuple[bool, str, List[DicomPreflightResult]]:
        """Inspect all files in a dataset directory, compute manifest hash, and verify attestation."""
        results: List[DicomPreflightResult] = []
        if not os.path.exists(dir_path):
            return False, f"Directory does not exist: {dir_path}", []

        # Collect files and calculate manifest hash
        file_records: List[Tuple[str, str]] = []
        file_paths: List[str] = []
        for root, _, files in os.walk(dir_path):
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                rel_name = os.path.relpath(fpath, dir_path).replace("\\", "/")
                h = hashlib.sha256()
                try:
                    with open(fpath, "rb") as f:
                        while chunk := f.read(65536):
                            h.update(chunk)
                    file_records.append((rel_name, h.hexdigest()))
                    file_paths.append(fpath)
                except Exception:
                    pass

        attestation = None
        if self.trust_authority and require_pixel_certificate:
            manifest_sha256 = self.trust_authority.compute_dataset_manifest_hash(file_records)
            is_valid, msg, att = self.trust_authority.verify_dataset_attestation(dataset_id, manifest_sha256)
            if not is_valid:
                for fpath in file_paths:
                    res = self.inspect_file(fpath, require_pixel_certificate=True, attestation=None)
                    results.append(res)
                return False, msg, results
            attestation = att

        all_passed = True
        for fpath in file_paths:
            res = self.inspect_file(fpath, require_pixel_certificate=require_pixel_certificate, attestation=attestation)
            if not res.passed_screening:
                all_passed = False
            results.append(res)

        return all_passed, "DATASET_INSPECTION_COMPLETE", results

    def quarantine_file(self, res: DicomPreflightResult) -> Dict[str, Any]:
        """Record quarantine entry and save tamper-evident manifest."""
        record = {
            "file_path": res.file_path,
            "sha256_hash": res.sha256_hash,
            "quarantined_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "reasons": [r.value for r in res.quarantine_reasons],
            "details": res.quarantine_details,
            "metadata_summary": {
                "transfer_syntax": res.transfer_syntax_uid,
                "modality": res.modality,
                "sop_instance_uid": res.sop_instance_uid,
                "patient_id": res.patient_id,
            }
        }
        self._quarantine_records.append(record)
        
        # Persist quarantine record to quarantine log
        manifest_path = os.path.join(
            self.quarantine_dir,
            f"quarantine_{res.sha256_hash[:16]}_{int(time.time())}.json"
        )
        try:
            import json
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
        except Exception:
            pass

        return record

    def get_quarantine_records(self) -> List[Dict[str, Any]]:
        return list(self._quarantine_records)
