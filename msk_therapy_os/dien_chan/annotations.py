"""2D Annotation and Digitization Model for Dien Chan Facial Reference Images.

Provides strict data structures for digitized 2D point annotations,
pixel-to-normalized coordinate conversion, confidence scoring,
and candidate status tracking from low-resolution source charts.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AnnotationView(str, Enum):
    """View orientation in source chart."""
    FRONTAL = "frontal"
    PROFILE_LEFT = "profile_left"
    PROFILE_RIGHT = "profile_right"


class AnnotationConfidence(str, Enum):
    """Confidence level of 2D digitization from source chart."""
    HIGH = "HIGH"          # Point number and landmark dot clearly discernible
    MEDIUM = "MEDIUM"      # Point number visible but landmark location estimated from grid
    LOW = "LOW"            # Blurry number or ambiguous marker dot
    UNREADABLE = "UNREADABLE"  # Illegible label requiring higher-resolution source


class Laterality(str, Enum):
    """Anatomical laterality of the point."""
    MIDLINE = "midline"
    BILATERAL_LEFT = "bilateral_left"
    BILATERAL_RIGHT = "bilateral_right"
    BILATERAL_PAIR = "bilateral_pair"
    UNILATERAL_LEFT = "unilateral_left"
    UNILATERAL_RIGHT = "unilateral_right"


@dataclass
class PointAnnotation2D:
    """Individual 2D annotation from a source reference image."""
    annotation_id: str
    source_image_id: str
    point_code: str                     # e.g., "DC_103", "DC_73"
    view: AnnotationView
    pixel_x: float                      # Pixel X in source image (0 to W-1)
    pixel_y: float                      # Pixel Y in source image (0 to H-1)
    image_width: int
    image_height: int
    norm_u: float = 0.0                 # Normalized coordinate u = pixel_x / image_width
    norm_v: float = 0.0                 # Normalized coordinate v = pixel_y / image_height
    grid_vertical: str = ""             # Vertical grid line (e.g., "O", "A", "B", "C", "D", "E", "G", "H", "K", "L")
    grid_horizontal: str = ""           # Horizontal grid line ("0" through "12")
    laterality: Laterality = Laterality.MIDLINE
    confidence: AnnotationConfidence = AnnotationConfidence.HIGH
    is_candidate: bool = True           # True until confirmed by authoritative cross-reference
    annotator: str = "curator_lead"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.image_width > 0 and self.norm_u == 0.0:
            self.norm_u = round(self.pixel_x / self.image_width, 4)
        if self.image_height > 0 and self.norm_v == 0.0:
            self.norm_v = round(self.pixel_y / self.image_height, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "annotation_id": self.annotation_id,
            "source_image_id": self.source_image_id,
            "point_code": self.point_code,
            "view": self.view.value,
            "pixel_x": self.pixel_x,
            "pixel_y": self.pixel_y,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "norm_u": self.norm_u,
            "norm_v": self.norm_v,
            "grid_vertical": self.grid_vertical,
            "grid_horizontal": self.grid_horizontal,
            "laterality": self.laterality.value,
            "confidence": self.confidence.value,
            "is_candidate": self.is_candidate,
            "annotator": self.annotator,
            "notes": self.notes,
        }


# Canonical digitized 2D annotations from Image B (Đau Đầu - Viêm Xoang, 800x578)
# and Image A (Đồ hình nhìn thẳng - nhìn nghiêng, 800x480)
CANONICAL_2D_ANNOTATIONS: List[PointAnnotation2D] = [
    # --- Frontal View Annotations (Image B: W=800, H=578) ---
    PointAnnotation2D(
        annotation_id="ANN_DC_B_103_F",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_103",
        view=AnnotationView.FRONTAL,
        pixel_x=202.0, pixel_y=125.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="2",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Midline forehead at vertical O, horizontal line 2 (mid-forehead)."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_106_F",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_106",
        view=AnnotationView.FRONTAL,
        pixel_x=202.0, pixel_y=163.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="3",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Midline forehead at vertical O, horizontal line 3 (inferior to 103, superior to glabella)."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_107_FL",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_107",
        view=AnnotationView.FRONTAL,
        pixel_x=176.0, pixel_y=163.0, image_width=800, image_height=578,
        grid_vertical="A", grid_horizontal="3",
        laterality=Laterality.BILATERAL_LEFT,
        confidence=AnnotationConfidence.HIGH,
        notes="Left forehead, lateral to 106 along horizontal line 3."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_107_FR",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_107",
        view=AnnotationView.FRONTAL,
        pixel_x=228.0, pixel_y=163.0, image_width=800, image_height=578,
        grid_vertical="A", grid_horizontal="3",
        laterality=Laterality.BILATERAL_RIGHT,
        confidence=AnnotationConfidence.HIGH,
        notes="Right forehead, lateral to 106 along horizontal line 3."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_300_FL",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_300",
        view=AnnotationView.FRONTAL,
        pixel_x=145.0, pixel_y=140.0, image_width=800, image_height=578,
        grid_vertical="C", grid_horizontal="1",
        laterality=Laterality.BILATERAL_LEFT,
        confidence=AnnotationConfidence.HIGH,
        notes="Left upper forehead at vertical C (mid-pupillary line), horizontal line 1."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_300_FR",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_300",
        view=AnnotationView.FRONTAL,
        pixel_x=258.0, pixel_y=140.0, image_width=800, image_height=578,
        grid_vertical="C", grid_horizontal="1",
        laterality=Laterality.BILATERAL_RIGHT,
        confidence=AnnotationConfidence.HIGH,
        notes="Right upper forehead at vertical C (mid-pupillary line), horizontal line 1."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_73_FL",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_73",
        view=AnnotationView.FRONTAL,
        pixel_x=146.0, pixel_y=288.0, image_width=800, image_height=578,
        grid_vertical="C", grid_horizontal="6",
        laterality=Laterality.BILATERAL_LEFT,
        confidence=AnnotationConfidence.HIGH,
        notes="Left infraorbital rim, vertical C (mid-pupillary), horizontal line 6."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_73_FR",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_73",
        view=AnnotationView.FRONTAL,
        pixel_x=258.0, pixel_y=288.0, image_width=800, image_height=578,
        grid_vertical="C", grid_horizontal="6",
        laterality=Laterality.BILATERAL_RIGHT,
        confidence=AnnotationConfidence.HIGH,
        notes="Right infraorbital rim, vertical C (mid-pupillary), horizontal line 6."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_189_F",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_189",
        view=AnnotationView.FRONTAL,
        pixel_x=202.0, pixel_y=248.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="5",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Nasal dorsum at vertical O, horizontal line 5 (inter-canthal level)."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_61_FL",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_61",
        view=AnnotationView.FRONTAL,
        pixel_x=182.0, pixel_y=352.0, image_width=800, image_height=578,
        grid_vertical="B", grid_horizontal="8",
        laterality=Laterality.BILATERAL_LEFT,
        confidence=AnnotationConfidence.HIGH,
        notes="Left alar notch/crease, vertical B, horizontal line 8 (alar base level)."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_61_FR",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_61",
        view=AnnotationView.FRONTAL,
        pixel_x=222.0, pixel_y=352.0, image_width=800, image_height=578,
        grid_vertical="B", grid_horizontal="8",
        laterality=Laterality.BILATERAL_RIGHT,
        confidence=AnnotationConfidence.HIGH,
        notes="Right alar notch/crease, vertical B, horizontal line 8 (alar base level)."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_19_F",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_19",
        view=AnnotationView.FRONTAL,
        pixel_x=202.0, pixel_y=365.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="8",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Upper philtrum apex directly under nasal septum, vertical O, horizontal line 8."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_127_F",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_127",
        view=AnnotationView.FRONTAL,
        pixel_x=202.0, pixel_y=452.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="11",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Mentolabial sulcus (depression above chin), vertical O, horizontal line 11."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_96_FL",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_96",
        view=AnnotationView.FRONTAL,
        pixel_x=105.0, pixel_y=226.0, image_width=800, image_height=578,
        grid_vertical="G", grid_horizontal="4",
        laterality=Laterality.BILATERAL_LEFT,
        confidence=AnnotationConfidence.MEDIUM,
        notes="Left temple / lateral orbit, vertical G, horizontal line 4."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_96_FR",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_96",
        view=AnnotationView.FRONTAL,
        pixel_x=298.0, pixel_y=226.0, image_width=800, image_height=578,
        grid_vertical="G", grid_horizontal="4",
        laterality=Laterality.BILATERAL_RIGHT,
        confidence=AnnotationConfidence.MEDIUM,
        notes="Right temple / lateral orbit, vertical G, horizontal line 4."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_43_F",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_43",
        view=AnnotationView.FRONTAL,
        pixel_x=202.0, pixel_y=320.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="7",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Nasal apex / tip, vertical O, horizontal line 7."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_26_F",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_26",
        view=AnnotationView.FRONTAL,
        pixel_x=202.0, pixel_y=210.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="4",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Glabella / between eyebrows, vertical O, horizontal line 4."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_0_FL",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_0",
        view=AnnotationView.FRONTAL,
        pixel_x=68.0, pixel_y=365.0, image_width=800, image_height=578,
        grid_vertical="K", grid_horizontal="8",
        laterality=Laterality.BILATERAL_LEFT,
        confidence=AnnotationConfidence.HIGH,
        notes="Left preauricular notch at incisura anterior auris, vertical K, horizontal line 8."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_0_FR",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_0",
        view=AnnotationView.FRONTAL,
        pixel_x=336.0, pixel_y=365.0, image_width=800, image_height=578,
        grid_vertical="K", grid_horizontal="8",
        laterality=Laterality.BILATERAL_RIGHT,
        confidence=AnnotationConfidence.HIGH,
        notes="Right preauricular notch at incisura anterior auris, vertical K, horizontal line 8."
    ),

    # --- Profile View Annotations (Image B: Right half, W=800, H=578) ---
    PointAnnotation2D(
        annotation_id="ANN_DC_B_103_P",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_103",
        view=AnnotationView.PROFILE_LEFT,
        pixel_x=706.0, pixel_y=125.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="2",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Profile view: mid-forehead anterior contour."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_106_P",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_106",
        view=AnnotationView.PROFILE_LEFT,
        pixel_x=714.0, pixel_y=163.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="3",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Profile view: lower forehead contour above glabella."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_189_P",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_189",
        view=AnnotationView.PROFILE_LEFT,
        pixel_x=734.0, pixel_y=248.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="5",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Profile view: nasal bridge dorsal prominence."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_19_P",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_19",
        view=AnnotationView.PROFILE_LEFT,
        pixel_x=722.0, pixel_y=365.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="8",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Profile view: subnasal junction / upper philtrum."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_127_P",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_127",
        view=AnnotationView.PROFILE_LEFT,
        pixel_x=688.0, pixel_y=452.0, image_width=800, image_height=578,
        grid_vertical="O", grid_horizontal="11",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
        notes="Profile view: mentolabial hollow / supramental crease."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_96_P",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_96",
        view=AnnotationView.PROFILE_LEFT,
        pixel_x=605.0, pixel_y=226.0, image_width=800, image_height=578,
        grid_vertical="G", grid_horizontal="4",
        laterality=Laterality.BILATERAL_LEFT,
        confidence=AnnotationConfidence.MEDIUM,
        notes="Profile view: anterior temporal area."
    ),
    PointAnnotation2D(
        annotation_id="ANN_DC_B_0_P",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_0",
        view=AnnotationView.PROFILE_LEFT,
        pixel_x=488.0, pixel_y=365.0, image_width=800, image_height=578,
        grid_vertical="K", grid_horizontal="8",
        laterality=Laterality.BILATERAL_LEFT,
        confidence=AnnotationConfidence.HIGH,
        notes="Profile view: tragus anterior notch."
    ),
]


def get_annotations_for_point(point_code: str) -> List[PointAnnotation2D]:
    """Retrieve all 2D annotations across views for a given point code."""
    return [ann for ann in CANONICAL_2D_ANNOTATIONS if ann.point_code == point_code]


def get_annotations_for_source(source_id: str) -> List[PointAnnotation2D]:
    """Retrieve all annotations belonging to a source image."""
    return [ann for ann in CANONICAL_2D_ANNOTATIONS if ann.source_image_id == source_id]
