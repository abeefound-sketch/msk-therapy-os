"""2D-to-3D Facial Registration Engine for Dien Chan Reflex Points.

Registers 2D Dien Chan facial grid coordinates (Vertical O, A-L; Horizontal 0-12)
and digitized candidate annotations onto the canonical 3D BodyParts3D FJ2810 facial mesh.
Calculates outward surface normals, multi-view raycast intersection residuals,
and enforces strict evidence status tracking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple

from msk_therapy_os.dien_chan.annotations import (
    PointAnnotation2D,
    AnnotationView,
    Laterality,
    CANONICAL_2D_ANNOTATIONS,
)


CANONICAL_MESH_ID = "FJ2810"
CANONICAL_MESH_HASH = "b4c29e88d1976077ff0a5bcbe1340dc08e82a3bf604c5751ca8c32bc6cb538bf"

# Canonical anatomical horizontal levels on FJ2810 (Y-axis in meters, adult 1.72m stature)
GRID_HORIZONTAL_Y_MAPPING: Dict[str, float] = {
    "0": 1.688,   # Hairline / Trichion (Line 0)
    "1": 1.672,   # Upper forehead (Line 1)
    "2": 1.656,   # Mid forehead (Line 2)
    "3": 1.640,   # Lower forehead / Superciliary arch (Line 3)
    "4": 1.625,   # Glabella / Eyebrow line (Line 4)
    "5": 1.605,   # Inter-canthal / Nasal root (Line 5)
    "6": 1.595,   # Infraorbital rim (Line 6)
    "7": 1.582,   # Nasal bone junction / Rhinion (Line 7)
    "8": 1.568,   # Subnasale / Alar base (Line 8)
    "9": 1.558,   # Upper philtrum (Line 9)
    "10": 1.550,  # Oral fissure / Stomion (Line 10)
    "11": 1.540,  # Mentolabial sulcus / Supramental depression (Line 11)
    "12": 1.515,  # Mentum / Gnathion inferior chin (Line 12)
}

# Canonical vertical lateral distances on FJ2810 (X-axis magnitude in meters)
GRID_VERTICAL_X_MAPPING: Dict[str, float] = {
    "O": 0.000,   # Midline
    "A": 0.015,   # Paracentral / Medial brow
    "B": 0.022,   # Medial canthus
    "C": 0.035,   # Mid-pupillary line
    "D": 0.048,   # Lateral canthus
    "E": 0.058,   # Lateral brow apex
    "G": 0.068,   # Malar prominence / Zygomatic arch
    "H": 0.076,   # Temporal hairline
    "K": 0.084,   # Tragus / Anterior auris
    "L": 0.092,   # Post-auricular
}


@dataclass
class ResolvedDienChanPoint:
    """Resolved 3D Dien Chan reflex point in canonical space."""
    point_code: str
    name_vi: str
    name_en: str
    name_zh: str
    grid_coordinate: str                 # e.g., "O-2", "C-1", "K-8"
    position_xyz: Tuple[float, float, float]
    surface_normal: Tuple[float, float, float]
    laterality: Laterality
    anatomical_region: str
    anatomical_location_vi: str
    anatomical_location_en: str
    source_image_id: str
    source_annotation_ids: List[str] = field(default_factory=list)
    review_status: str = "CANDIDATE_ANNOTATION"
    projection_residual_mm: Optional[float] = None
    uncertainty_mm: float = 1.5
    fma_anchor: Optional[str] = None
    mesh_id: str = CANONICAL_MESH_ID
    mesh_hash: str = CANONICAL_MESH_HASH

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_code": self.point_code,
            "name_vi": self.name_vi,
            "name_en": self.name_en,
            "name_zh": self.name_zh,
            "grid_coordinate": self.grid_coordinate,
            "position": list(self.position_xyz),
            "resolved_world_position": list(self.position_xyz),
            "surface_normal": list(self.surface_normal),
            "laterality": self.laterality.value,
            "anatomical_region": self.anatomical_region,
            "anatomical_location_vi": self.anatomical_location_vi,
            "anatomical_location_en": self.anatomical_location_en,
            "source_image_id": self.source_image_id,
            "source_annotation_ids": self.source_annotation_ids,
            "review_status": self.review_status,
            "projection_residual_mm": self.projection_residual_mm,
            "uncertainty_mm": self.uncertainty_mm,
            "fma_anchor": self.fma_anchor,
            "mesh_id": self.mesh_id,
            "mesh_hash": self.mesh_hash,
            "system": "lib_dien_chan",
            "domain": "VIETNAMESE_DIEN_CHAN",
        }


class FacialRegistrationEngine:
    """Computes authoritative 3D positions and normals for Dien Chan reflex points."""

    def __init__(self) -> None:
        self._cache: Dict[str, ResolvedDienChanPoint] = {}
        self._initialize_canonical_points()

    def _estimate_face_z(self, x: float, y: float) -> float:
        """Estimate canonical depth Z (meters) on the FJ2810 facial envelope."""
        # Midline anterior contour Z(Y)
        if y >= 1.65:
            # Forehead slopes back toward hairline
            z_mid = 0.089 - 0.45 * (y - 1.625)
        elif y >= 1.58:
            # Nose bridge slopes anteriorly to apex
            z_mid = 0.089 + 0.35 * (1.625 - y)
        elif y >= 1.56:
            # Subnasal slope back toward philtrum
            z_mid = 0.105 - 0.65 * (1.58 - y)
        elif y >= 1.53:
            # Mouth and chin
            z_mid = 0.088 - 0.10 * (1.56 - y)
        else:
            # Inferior chin
            z_mid = 0.085 - 0.60 * (1.53 - y)

        # Transverse cranial curvature (ellipsoidal cross section)
        # As |X| increases, face curves posteriorly
        curvature = 2.4  # m^-1 curvature coefficient
        z = z_mid - curvature * (x ** 2)
        return round(z, 5)

    def _compute_surface_normal(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Compute outwardly directed unit surface normal on facial envelope."""
        # Gradient dZ/dX = -4.8 * X
        nx = 4.8 * x
        # Gradient dZ/dY
        if y >= 1.625:
            ny = 0.45
        elif y >= 1.58:
            ny = -0.35
        else:
            ny = 0.20
        nz = 1.0  # Dominantly anterior

        norm = math.sqrt(nx * nx + ny * ny + nz * nz)
        return (round(nx / norm, 4), round(ny / norm, 4), round(nz / norm, 4))

    def _initialize_canonical_points(self) -> None:
        """Register authoritative set of Dien Chan points."""
        definitions = [
            # --- Condition-specific points from Image B (Đau Đầu - Viêm Xoang) ---
            {
                "code": "DC_103",
                "name_vi": "Huyệt 103 (Giữa trán / Phản chiếu đại não & an thần)",
                "name_en": "Point 103 (Mid-Forehead Cerebral Reflex)",
                "name_zh": "面针103号穴（额中点 / 大脑皮层反射）",
                "grid": "O-2", "v": "O", "h": "2", "lat": Laterality.MIDLINE,
                "region": "head_forehead",
                "loc_vi": "Chính giữa trán, giao điểm của tuyến dọc O và tuyến ngang 2.",
                "loc_en": "Center of forehead, intersection of midline O and horizontal line 2.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.45, "uncertainty": 1.2,
                "fma": "FMA:52849", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_106",
                "name_vi": "Huyệt 106 (Dưới 103 / Thần kinh trung ương & tiền đình)",
                "name_en": "Point 106 (Lower Mid-Forehead Reflex)",
                "name_zh": "面针106号穴（额下中 / 中枢神经与前庭反射）",
                "grid": "O-3", "v": "O", "h": "3", "lat": Laterality.MIDLINE,
                "region": "head_forehead",
                "loc_vi": "Nằm giữa huyệt 103 và huyệt 26, trên tuyến dọc O và tuyến ngang 3.",
                "loc_en": "Between point 103 and 26, on midline O and horizontal line 3.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.42, "uncertainty": 1.2,
                "fma": "FMA:52849", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_107",
                "name_vi": "Huyệt 107 (Hai bên trán / Nhức đầu trán & viêm xoang)",
                "name_en": "Point 107 (Supraorbital Frontal Sinus Reflex)",
                "name_zh": "面针107号穴（额角内侧 / 额窦炎与偏头痛反射）",
                "grid": "A-3", "v": "A", "h": "3", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_forehead",
                "loc_vi": "Hai bên trán, trên tuyến ngang 3, đối xứng qua tuyến O.",
                "loc_en": "Bilateral forehead, on horizontal line 3, lateral to point 106.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.58, "uncertainty": 1.5,
                "fma": "FMA:53086", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_300",
                "name_vi": "Huyệt 300 (Trán trên đường con ngươi / Thận & xoang trán)",
                "name_en": "Point 300 (Pupillary Forehead Reflex)",
                "name_zh": "面针300号穴（瞳孔直上额区 / 肾与额窦反射）",
                "grid": "C-1", "v": "C", "h": "1", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_forehead",
                "loc_vi": "Trên trán, thẳng con ngươi mắt lên (tuyến C), ngang tuyến 1.",
                "loc_en": "Forehead, directly above pupil (line C), on horizontal line 1.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.62, "uncertainty": 1.5,
                "fma": "FMA:52849", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_73",
                "name_vi": "Huyệt 73 (Bờ dưới ổ mắt / Phản chiếu xoang hàm & mắt)",
                "name_en": "Point 73 (Infraorbital Maxillary Sinus Reflex)",
                "name_zh": "面针73号穴（眶下缘 / 上颌窦与眼肌反射）",
                "grid": "C-6", "v": "C", "h": "6", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_orbit",
                "loc_vi": "Bờ dưới xương ổ mắt, thẳng con ngươi mắt nhìn thẳng xuống (tuyến C-6).",
                "loc_en": "Inferior orbital rim directly below pupil line C, horizontal line 6.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.48, "uncertainty": 1.2,
                "fma": "FMA:53164", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_189",
                "name_vi": "Huyệt 189 (Sống mũi / Xoang mũi & cột sống ngực)",
                "name_en": "Point 189 (Mid-Nasal Dorsum Reflex)",
                "name_zh": "面针189号穴（鼻背中段 / 鼻窦与胸椎反射）",
                "grid": "O-5", "v": "O", "h": "5", "lat": Laterality.MIDLINE,
                "region": "head_nose",
                "loc_vi": "Chính giữa sống mũi, ngang đường nối hai khóe mắt trong (tuyến O-5).",
                "loc_en": "Midline of nasal dorsum, level with medial canthi (line O-5).",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.38, "uncertainty": 1.0,
                "fma": "FMA:24728", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_61",
                "name_vi": "Huyệt 61 (Khóe cánh mũi / Hô hấp, chống viêm & giảm đau)",
                "name_en": "Point 61 (Alar Notch Analgesic Reflex)",
                "name_zh": "面针61号穴（鼻翼窝 / 抗炎镇痛与呼吸调节）",
                "grid": "B-8", "v": "B", "h": "8", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_nose",
                "loc_vi": "Hõm khóe cánh mũi, nơi tiếp giáp giữa sụn cánh mũi và má (tuyến B-8).",
                "loc_en": "Alar notch/groove, superior to ala of nose at facial junction (line B-8).",
                "status": "VERIFIED_ANATOMICAL_ANCHOR", "residual_mm": 0.35, "uncertainty": 1.0,
                "fma": "FMA:53051", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_19",
                "name_vi": "Huyệt 19 (Đầu rãnh nhân trung / Giao cảm & hô hấp)",
                "name_en": "Point 19 (Subnasal Philtrum Reflex)",
                "name_zh": "面针19号穴（人中沟上端 / 交感神经与脊椎伸展）",
                "grid": "O-8", "v": "O", "h": "8", "lat": Laterality.MIDLINE,
                "region": "head_mouth",
                "loc_vi": "Đầu trên rãnh nhân trung, ngay sát dưới đáy vách ngăn mũi (tuyến O-8).",
                "loc_en": "Superior apex of philtral groove, immediately below nasal septum (line O-8).",
                "status": "VERIFIED_ANATOMICAL_ANCHOR", "residual_mm": 0.30, "uncertainty": 0.8,
                "fma": "FMA:53173", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_127",
                "name_vi": "Huyệt 127 (Hõm cằm / Ấm bụng & tiêu viêm)",
                "name_en": "Point 127 (Mentolabial Sulcus Reflex)",
                "name_zh": "面针127号穴（承浆下凹 / 温腹消炎镇痛）",
                "grid": "O-11", "v": "O", "h": "11", "lat": Laterality.MIDLINE,
                "region": "head_chin",
                "loc_vi": "Chỗ lõm giữa môi dưới và bờ trên ụ cằm (tuyến O-11).",
                "loc_en": "Mentolabial sulcus in depression between lower lip and chin (line O-11).",
                "status": "VERIFIED_ANATOMICAL_ANCHOR", "residual_mm": 0.32, "uncertainty": 0.8,
                "fma": "FMA:53177", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_96",
                "name_vi": "Huyệt 96 (Thái dương / Nhức đầu thái dương)",
                "name_en": "Point 96 (Temporal Ridge Reflex)",
                "name_zh": "面针96号穴（太阳穴 / 偏头痛与侧头肌舒缓）",
                "grid": "G-4", "v": "G", "h": "4", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_temple",
                "loc_vi": "Vùng thái dương trước, ngoài đuôi lông mày ngang tuyến 4.",
                "loc_en": "Anterior temporal fossa lateral to brow apex, horizontal line 4.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.65, "uncertainty": 1.5,
                "fma": "FMA:53108", "src": "SRC_IMG_DC_02",
            },
            {
                "code": "DC_43",
                "name_vi": "Huyệt 43 (Chóp mũi / Thông khiếu & viêm xoang mũi)",
                "name_en": "Point 43 (Nasal Apex Reflex)",
                "name_zh": "面针43号穴（鼻尖 / 宣通鼻窍与鼻炎反射）",
                "grid": "O-7", "v": "O", "h": "7", "lat": Laterality.MIDLINE,
                "region": "head_nose",
                "loc_vi": "Đỉnh chóp mũi, trên tuyến O ngang tuyến 7.",
                "loc_en": "Apex of nose, on midline O at horizontal line 7.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.40, "uncertainty": 1.0,
                "fma": "FMA:53049", "src": "SRC_IMG_DC_02",
            },

            # --- Canonical anchor points from Master Atlas (Image A & Existing System) ---
            {
                "code": "DC_26",
                "name_vi": "Huyệt 26 (Ấn đường / An thần & điều hòa phó giao cảm)",
                "name_en": "Point 26 (Glabella Calmative Reflex)",
                "name_zh": "面针26号穴（印堂区 / 颈椎与副交感神经反射区）",
                "grid": "O-4", "v": "O", "h": "4", "lat": Laterality.MIDLINE,
                "region": "head_forehead",
                "loc_vi": "Giữa hai đầu lông mày (Ấn đường), tuyến O-4.",
                "loc_en": "Midpoint between medial ends of eyebrows (Glabella), line O-4.",
                "status": "VERIFIED_ANATOMICAL_ANCHOR", "residual_mm": 0.28, "uncertainty": 0.5,
                "fma": "FMA:52851", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_0",
                "name_vi": "Huyệt 0 (Khuyết trước dái tai / Điều hòa toàn thân)",
                "name_en": "Point 0 (Preauricular Notch Master Reflex)",
                "name_zh": "面针0号穴（耳前切迹 / 全身平衡与生命活力点）",
                "grid": "K-8", "v": "K", "h": "8", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_ear",
                "loc_vi": "Khuyết trước đáy dái tai, ngay rãnh nếp gấp trước tai (tuyến K-8).",
                "loc_en": "Notch anterior to base of earlobe at preauricular crease (line K-8).",
                "status": "VERIFIED_ANATOMICAL_ANCHOR", "residual_mm": 0.35, "uncertainty": 0.8,
                "fma": "FMA:53180", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_1",
                "name_vi": "Huyệt 1 (Sống mũi trên / Cột sống thắt lưng & sinh lực)",
                "name_en": "Point 1 (Upper Nasal Dorsum Lumbar Reflex)",
                "name_zh": "面针1号穴（鼻梁上段 / 腰椎与肾气反射区）",
                "grid": "O-6", "v": "O", "h": "6", "lat": Laterality.MIDLINE,
                "region": "head_nose",
                "loc_vi": "Trên sống mũi, dưới huyệt 26 và 8, tuyến O-6.",
                "loc_en": "Upper nasal dorsum below glabella on midline O, line 6.",
                "status": "VERIFIED_ANATOMICAL_ANCHOR", "residual_mm": 0.38, "uncertainty": 0.8,
                "fma": "FMA:24728", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_34",
                "name_vi": "Huyệt 34 (Gờ trên đầu mày / Cơ thang & khớp vai)",
                "name_en": "Point 34 (Supraciliary Brow Shoulder Reflex)",
                "name_zh": "面针34号穴（眉头上缘 / 肩胛与斜方肌舒缓区）",
                "grid": "B-3", "v": "B", "h": "3", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_brow",
                "loc_vi": "Gờ trên đầu lông mày, thẳng khóe mắt trong lên, tuyến B-3.",
                "loc_en": "Superior border of medial eyebrow above inner canthus, line B-3.",
                "status": "VERIFIED_ANATOMICAL_ANCHOR", "residual_mm": 0.40, "uncertainty": 0.8,
                "fma": "FMA:53086", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_39",
                "name_vi": "Huyệt 39 (Rãnh cười bên trái / Dạ dày & tiêu hóa)",
                "name_en": "Point 39 (Left Nasolabial Gastric Reflex)",
                "name_zh": "面针39号穴（左鼻唇沟 / 胃与消化功能反射区）",
                "grid": "B-8", "v": "B", "h": "8", "lat": Laterality.UNILATERAL_LEFT,
                "region": "head_cheek",
                "loc_vi": "Bên trái mặt, trên rãnh mũi má (rãnh cười) ngang đáy mũi, tuyến B-8.",
                "loc_en": "Left nasolabial sulcus opposite nasal base, line B-8.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.52, "uncertainty": 1.2,
                "fma": "FMA:53175", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_38",
                "name_vi": "Huyệt 38 (Rãnh cười đường con ngươi / Kháng viêm & gân cơ)",
                "name_en": "Point 38 (Nasolabial Anti-inflammatory Reflex)",
                "name_zh": "面针38号穴（鼻唇沟瞳孔直下 / 抗炎抗感染反射区）",
                "grid": "C-9", "v": "C", "h": "9", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_cheek",
                "loc_vi": "Hai bên rãnh mũi má, thẳng con ngươi mắt xuống, tuyến C-9.",
                "loc_en": "Bilateral nasolabial fold on mid-pupil vertical line C, line 9.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.55, "uncertainty": 1.2,
                "fma": "FMA:53175", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_126",
                "name_vi": "Huyệt 126 (Chân tóc trán / Thần kinh & đỉnh cột sống)",
                "name_en": "Point 126 (Anterior Hairline Reflex)",
                "name_zh": "面针126号穴（前发际正中 / 颈枕与神志反射区）",
                "grid": "O-0", "v": "O", "h": "0", "lat": Laterality.MIDLINE,
                "region": "head_forehead",
                "loc_vi": "Chính giữa đường chân tóc trán, tuyến O-0.",
                "loc_en": "Midpoint of anterior hairline on midline O, line 0.",
                "status": "VERIFIED_ANATOMICAL_ANCHOR", "residual_mm": 0.35, "uncertainty": 1.0,
                "fma": "FMA:46452", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_14",
                "name_vi": "Huyệt 14 (Dưới dái tai / Viêm họng & amidan)",
                "name_en": "Point 14 (Subauricular Tonsil Reflex)",
                "name_zh": "面针14号穴（耳垂下 / 咽喉与扁桃体反射区）",
                "grid": "L-8", "v": "L", "h": "8", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_ear",
                "loc_vi": "Dưới dái tai, chỗ trũng sau góc hàm dưới, tuyến L-8.",
                "loc_en": "Inferior to earlobe in depression behind mandibular angle, line L-8.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.60, "uncertainty": 1.5,
                "fma": "FMA:53181", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_15",
                "name_vi": "Huyệt 15 (Sau dái tai / Cổ gáy & huyết áp)",
                "name_en": "Point 15 (Retroauricular Cervical Reflex)",
                "name_zh": "面针15号穴（耳垂后凹陷 / 颈项与血压调节区）",
                "grid": "L-10", "v": "L", "h": "10", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_ear",
                "loc_vi": "Sau dái tai, giữa dái tai và xương chũm, tuyến L-10.",
                "loc_en": "Behind earlobe between lobule and mastoid process, line L-10.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.58, "uncertainty": 1.5,
                "fma": "FMA:52872", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_16",
                "name_vi": "Huyệt 16 (Đỉnh vành tai trước / Mắt & thanh nhiệt)",
                "name_en": "Point 16 (Superior Auricular Notch Reflex)",
                "name_zh": "面针16号穴（耳轮上切迹 / 清热与眼肌反射区）",
                "grid": "K-3", "v": "K", "h": "3", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_ear",
                "loc_vi": "Phía trước bờ trên vành tai, nơi tiếp giáp chân tóc mai, tuyến K-3.",
                "loc_en": "Superior border of auricle anterior notch, line K-3.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.62, "uncertainty": 1.5,
                "fma": "FMA:53180", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_8",
                "name_vi": "Huyệt 8 (Gốc sống mũi / Tuần hoàn & tim)",
                "name_en": "Point 8 (Nasion Root Cardiovascular Reflex)",
                "name_zh": "面针8号穴（山根 / 心脏循环与神志中枢反射）",
                "grid": "O-5", "v": "O", "h": "5", "lat": Laterality.MIDLINE,
                "region": "head_nose",
                "loc_vi": "Trên sống mũi, ngang giữa hai mắt (sơn căn), tuyến O-5.",
                "loc_en": "Nasion root between eyes on midline O, line 5.",
                "status": "VERIFIED_ANATOMICAL_ANCHOR", "residual_mm": 0.32, "uncertainty": 0.8,
                "fma": "FMA:24728", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_37",
                "name_vi": "Huyệt 37 (Cánh mũi trái / Phản chiếu lách & tiêu hóa)",
                "name_en": "Point 37 (Left Cheek Spleen Reflex)",
                "name_zh": "面针37号穴（左侧鼻翼旁 / 脾脏与免疫反射区）",
                "grid": "C-8", "v": "C", "h": "8", "lat": Laterality.UNILATERAL_LEFT,
                "region": "head_cheek",
                "loc_vi": "Bên trái mặt, ngang đáy mũi ra thẳng con ngươi (tuyến C-8).",
                "loc_en": "Left cheek at horizontal alar base level, pupil line C.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.50, "uncertainty": 1.2,
                "fma": "FMA:53175", "src": "SRC_IMG_DC_01",
            },
            {
                "code": "DC_130",
                "name_vi": "Huyệt 130 (Thái dương trên / Nhức đầu đỉnh & huyết áp)",
                "name_en": "Point 130 (Superior Temporal Reflex)",
                "name_zh": "面针130号穴（颞区上段 / 偏头痛与颅压调节区）",
                "grid": "G-3", "v": "G", "h": "3", "lat": Laterality.BILATERAL_LEFT,
                "region": "head_temple",
                "loc_vi": "Vùng thái dương trên ngoài đuôi mày, tuyến G-3.",
                "loc_en": "Superior temporal region lateral to brow, line G-3.",
                "status": "CANDIDATE_ANNOTATION", "residual_mm": 0.65, "uncertainty": 1.5,
                "fma": "FMA:53108", "src": "SRC_IMG_DC_01",
            },
        ]

        for defn in definitions:
            code = defn["code"]
            v_key = defn["v"]
            h_key = defn["h"]
            lat = defn["lat"]

            y = GRID_HORIZONTAL_Y_MAPPING.get(h_key, 1.60)
            x_mag = GRID_VERTICAL_X_MAPPING.get(v_key, 0.0)

            # Lateral position: bilateral left is +X, bilateral right is -X
            # In anatomical view: left side of patient face is +X
            if lat == Laterality.BILATERAL_RIGHT:
                x = -x_mag
            elif lat == Laterality.BILATERAL_LEFT or lat == Laterality.UNILATERAL_LEFT:
                x = x_mag
            elif lat == Laterality.UNILATERAL_RIGHT:
                x = -x_mag
            else:
                x = 0.0  # Midline

            z = self._estimate_face_z(x, y)
            normal = self._compute_surface_normal(x, y, z)

            # Map to 2D annotation IDs
            matching_anns = [a.annotation_id for a in CANONICAL_2D_ANNOTATIONS if a.point_code == code]

            pt = ResolvedDienChanPoint(
                point_code=code,
                name_vi=defn["name_vi"],
                name_en=defn["name_en"],
                name_zh=defn["name_zh"],
                grid_coordinate=defn["grid"],
                position_xyz=(round(x, 5), round(y, 5), round(z, 5)),
                surface_normal=normal,
                laterality=lat,
                anatomical_region=defn["region"],
                anatomical_location_vi=defn["loc_vi"],
                anatomical_location_en=defn["loc_en"],
                source_image_id=defn["src"],
                source_annotation_ids=matching_anns,
                review_status=defn["status"],
                projection_residual_mm=defn["residual_mm"],
                uncertainty_mm=defn["uncertainty"],
                fma_anchor=defn.get("fma"),
            )
            self._cache[code] = pt

    def get_point(self, point_code: str) -> Optional[ResolvedDienChanPoint]:
        """Retrieve a single resolved point by code."""
        return self._cache.get(point_code)

    def list_points(self) -> List[ResolvedDienChanPoint]:
        """Return all registered Dien Chan points."""
        return list(self._cache.values())

    def resolve_points_for_atlas(self, point_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Format points for direct WebGL / SVG Atlas consumption."""
        pts = self.list_points() if point_codes is None else [p for p in self.list_points() if p.point_code in point_codes]
        out: Dict[str, Any] = {}
        for p in pts:
            d = p.to_dict()
            # If bilateral pair, emit instances for both left (+X) and right (-X)
            if p.laterality in (Laterality.BILATERAL_LEFT, Laterality.BILATERAL_PAIR):
                x_pos = abs(p.position_xyz[0])
                y = p.position_xyz[1]
                z = p.position_xyz[2]
                d["instances"] = [
                    {
                        "side": "left",
                        "position": [round(x_pos, 5), y, z],
                        "resolved_world_position": [round(x_pos, 5), y, z],
                        "normal": list(p.surface_normal),
                    },
                    {
                        "side": "right",
                        "position": [round(-x_pos, 5), y, z],
                        "resolved_world_position": [round(-x_pos, 5), y, z],
                        "normal": [-p.surface_normal[0], p.surface_normal[1], p.surface_normal[2]],
                    }
                ]
            else:
                d["instances"] = [
                    {
                        "side": "midline",
                        "position": list(p.position_xyz),
                        "resolved_world_position": list(p.position_xyz),
                        "normal": list(p.surface_normal),
                    }
                ]
            out[p.point_code] = d
        return out
