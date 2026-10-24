"""Anatomical Landmark Registration Engine for MSK-Therapy-OS.

Provides multi-source coordinate normalization, rigid and similarity Procrustes/Umeyama
alignment, singular value decomposition (SVD) in pure Python (zero external dependencies),
residual error quantification, and strict clinical abstention / rejection semantics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple

from .landmark_registry import (
    AnatomicalLandmark,
    BodyRegion,
    CANONICAL_LANDMARKS,
    LandmarkRegistry,
)

# Anatomical body envelope for standard adult human in BodyParts3D canonical frame (meters)
BODY_ENVELOPE = {
    "x_min": -0.38, "x_max": 0.38,
    "y_min": -0.05, "y_max": 1.76,
    "z_min": -0.28, "z_max": 0.28,
}

# Maximum permissible registration residual errors (in millimeters)
MAX_PERMISSIBLE_RMS_MM = {
    BodyRegion.HEAD_NECK: 15.0,
    BodyRegion.TORSO: 20.0,
    BodyRegion.UPPER_EXTREMITY: 25.0,
    BodyRegion.LOWER_EXTREMITY: 25.0,
}


@dataclass
class RegistrationTransform:
    """Rigid or similarity 3D affine transform: Y = s * R * X + t."""
    rotation_matrix: List[List[float]]  # 3x3 matrix
    translation_vector: Tuple[float, float, float]  # [tx, ty, tz] in meters
    scale: float = 1.0
    rms_error_mm: float = 0.0
    max_error_mm: float = 0.0
    landmark_residuals_mm: Dict[str, float] = field(default_factory=dict)
    status: str = "UNVERIFIED"
    source_name: str = ""
    rejection_reason: Optional[str] = None

    def transform_point(self, p: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Apply transformation to a 3D coordinate vector."""
        r = self.rotation_matrix
        s = self.scale
        tx, ty, tz = self.translation_vector
        x, y, z = p
        rx = s * (r[0][0] * x + r[0][1] * y + r[0][2] * z) + tx
        ry = s * (r[1][0] * x + r[1][1] * y + r[1][2] * z) + ty
        rz = s * (r[2][0] * x + r[2][1] * y + r[2][2] * z) + tz
        return (rx, ry, rz)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rotation_matrix": self.rotation_matrix,
            "translation_vector": list(self.translation_vector),
            "scale": self.scale,
            "rms_error_mm": round(self.rms_error_mm, 2),
            "max_error_mm": round(self.max_error_mm, 2),
            "landmark_residuals_mm": {k: round(v, 2) for k, v in self.landmark_residuals_mm.items()},
            "status": self.status,
            "source_name": self.source_name,
            "rejection_reason": self.rejection_reason,
        }


# =============================================================================
# Pure Python 3x3 Linear Algebra & SVD Routines
# =============================================================================

def mat3_mult(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Multiply two 3x3 matrices."""
    return [
        [sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]


def mat3_transpose(m: List[List[float]]) -> List[List[float]]:
    """Transpose a 3x3 matrix."""
    return [[m[j][i] for j in range(3)] for i in range(3)]


def mat3_det(m: List[List[float]]) -> float:
    """Determinant of a 3x3 matrix."""
    return (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )


def mat3_identity() -> List[List[float]]:
    """3x3 Identity matrix."""
    return [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]


def jacobi_eigen_sym3(a: List[List[float]], max_iter: int = 50, eps: float = 1e-12) -> Tuple[List[float], List[List[float]]]:
    """Compute eigenvalues and eigenvectors of a 3x3 symmetric matrix via Jacobi rotations."""
    # Copy A
    v = mat3_identity()
    diag = [a[i][i] for i in range(3)]
    a_mat = [row[:] for row in a]

    for _ in range(max_iter):
        # Find maximum off-diagonal element
        p, q = 0, 1
        max_val = abs(a_mat[0][1])
        if abs(a_mat[0][2]) > max_val:
            p, q = 0, 2
            max_val = abs(a_mat[0][2])
        if abs(a_mat[1][2]) > max_val:
            p, q = 1, 2
            max_val = abs(a_mat[1][2])

        if max_val < eps:
            break

        app = a_mat[p][p]
        aqq = a_mat[q][q]
        apq = a_mat[p][q]

        theta = 0.5 * (aqq - app) / apq
        t = 1.0 / (abs(theta) + math.sqrt(theta * theta + 1.0))
        if theta < 0.0:
            t = -t
        c = 1.0 / math.sqrt(t * t + 1.0)
        s = t * c

        # Apply Givens rotation to A
        tau = s / (1.0 + c)
        a_mat[p][p] = app - t * apq
        a_mat[q][q] = aqq + t * apq
        a_mat[p][q] = 0.0
        a_mat[q][p] = 0.0

        for r in range(3):
            if r != p and r != q:
                arp = a_mat[r][p]
                arq = a_mat[r][q]
                a_mat[r][p] = arp - s * (arq + tau * arp)
                a_mat[p][r] = a_mat[r][p]
                a_mat[r][q] = arq + s * (arp - tau * arq)
                a_mat[q][r] = a_mat[r][q]

        # Accumulate transformation in V
        for r in range(3):
            vrp = v[r][p]
            vrq = v[r][q]
            v[r][p] = vrp - s * (vrq + tau * vrp)
            v[r][q] = vrq + s * (vrp - tau * vrq)

    eigenvalues = [a_mat[i][i] for i in range(3)]

    # Sort eigenvalues descending
    idx = sorted(range(3), key=lambda i: eigenvalues[i], reverse=True)
    sorted_vals = [eigenvalues[i] for i in idx]
    sorted_vecs = [[v[r][i] for r in range(3)] for i in idx]
    # In sorted_vecs, column i is sorted_vecs[i]
    v_out = [[sorted_vecs[j][i] for j in range(3)] for i in range(3)]

    return sorted_vals, v_out


def svd_3x3(h: List[List[float]]) -> Tuple[List[List[float]], List[float], List[List[float]]]:
    """Compute Singular Value Decomposition of a 3x3 matrix: H = U * S * V^T."""
    ht = mat3_transpose(h)
    hth = mat3_mult(ht, h)
    eigenvalues, v = jacobi_eigen_sym3(hth)

    singular_values = [math.sqrt(max(0.0, ev)) for ev in eigenvalues]

    # Ensure V columns are right-handed, handling coplanar rank-2 matrices
    v_col0 = [v[i][0] for i in range(3)]
    v_col1 = [v[i][1] for i in range(3)]
    if singular_values[2] < 1e-6:
        v_col2 = [
            v_col0[1] * v_col1[2] - v_col0[2] * v_col1[1],
            v_col0[2] * v_col1[0] - v_col0[0] * v_col1[2],
            v_col0[0] * v_col1[1] - v_col0[1] * v_col1[0],
        ]
        for i in range(3):
            v[i][2] = v_col2[i]

    # Compute U columns: u_j = (H * v_j) / sigma_j
    u = [[0.0] * 3 for _ in range(3)]
    for j in range(2):
        sigma = singular_values[j]
        if sigma > 1e-10:
            for i in range(3):
                u[i][j] = sum(h[i][k] * v[k][j] for k in range(3)) / sigma

    if singular_values[2] > 1e-10:
        for i in range(3):
            u[i][2] = sum(h[i][k] * v[k][2] for k in range(3)) / singular_values[2]
    else:
        # 3rd column is cross product of u_col0 and u_col1 to ensure orthonormality
        u_col0 = [u[i][0] for i in range(3)]
        u_col1 = [u[i][1] for i in range(3)]
        u_col2 = [
            u_col0[1] * u_col1[2] - u_col0[2] * u_col1[1],
            u_col0[2] * u_col1[0] - u_col0[0] * u_col1[2],
            u_col0[0] * u_col1[1] - u_col0[1] * u_col1[0],
        ]
        for i in range(3):
            u[i][2] = u_col2[i]

    vt = mat3_transpose(v)
    return u, singular_values, vt


# =============================================================================
# Umeyama Landmark Alignment Engine
# =============================================================================

class AnatomicalRegistrationEngine:
    """Engine for registering multi-source anatomical landmarks to canonical BodyParts3D coordinates."""

    def __init__(self, landmark_registry: Optional[LandmarkRegistry] = None):
        self.registry = landmark_registry or LandmarkRegistry()

    @staticmethod
    def validate_body_envelope(position: Tuple[float, float, float]) -> bool:
        """Check if 3D coordinates in meters reside within physiological adult human envelope."""
        x, y, z = position
        return (
            BODY_ENVELOPE["x_min"] <= x <= BODY_ENVELOPE["x_max"] and
            BODY_ENVELOPE["y_min"] <= y <= BODY_ENVELOPE["y_max"] and
            BODY_ENVELOPE["z_min"] <= z <= BODY_ENVELOPE["z_max"]
        )

    @staticmethod
    def check_collinearity(points: List[Tuple[float, float, float]], eps: float = 1e-4) -> bool:
        """Check if a set of 3D points are collinear (degenerate for 3D rotation)."""
        if len(points) < 3:
            return True

        p0 = points[0]
        # Find first non-coincident point
        v1 = None
        for p in points[1:]:
            dx, dy, dz = p[0] - p0[0], p[1] - p0[1], p[2] - p0[2]
            norm = math.sqrt(dx * dx + dy * dy + dz * dz)
            if norm > eps:
                v1 = (dx / norm, dy / norm, dz / norm)
                break

        if v1 is None:
            return True

        for p in points[2:]:
            dx, dy, dz = p[0] - p0[0], p[1] - p0[1], p[2] - p0[2]
            norm = math.sqrt(dx * dx + dy * dy + dz * dz)
            if norm <= eps:
                continue
            v2 = (dx / norm, dy / norm, dz / norm)
            # Cross product norm
            cx = v1[1] * v2[2] - v1[2] * v2[1]
            cy = v1[2] * v2[0] - v1[0] * v2[2]
            cz = v1[0] * v2[1] - v1[1] * v2[0]
            cross_norm = math.sqrt(cx * cx + cy * cy + cz * cz)
            if cross_norm > eps:
                return False  # Non-collinear found

        return True

    def calculate_umeyama_alignment(
        self,
        source_landmarks: Dict[str, Tuple[float, float, float]],
        target_landmarks: Optional[Dict[str, Tuple[float, float, float]]] = None,
        allow_scaling: bool = False,
        source_name: str = "upstream",
        region: BodyRegion = BodyRegion.HEAD_NECK
    ) -> RegistrationTransform:
        """Compute optimal rigid/similarity alignment using the Umeyama SVD algorithm."""
        # Resolve target canonical landmarks
        common_keys = []
        src_pts = []
        dst_pts = []

        for key, s_pos in source_landmarks.items():
            t_pos = None
            if target_landmarks and key in target_landmarks:
                t_pos = target_landmarks[key]
            else:
                lm = self.registry.get_landmark(key)
                if lm:
                    t_pos = lm.canonical_position

            if t_pos is not None:
                common_keys.append(key)
                src_pts.append(s_pos)
                dst_pts.append(t_pos)

        n = len(common_keys)
        # Rejection Gate 1: Insufficient landmarks
        if n < 3:
            return RegistrationTransform(
                rotation_matrix=mat3_identity(),
                translation_vector=(0.0, 0.0, 0.0),
                scale=1.0,
                status="UNREGISTERED",
                source_name=source_name,
                rejection_reason=f"Insufficient common landmarks ({n} < 3). Requires at least 3 non-collinear anchors.",
            )

        # Rejection Gate 2: Collinear configuration
        if self.check_collinearity(src_pts) or self.check_collinearity(dst_pts):
            return RegistrationTransform(
                rotation_matrix=mat3_identity(),
                translation_vector=(0.0, 0.0, 0.0),
                scale=1.0,
                status="DEGENERATE_COLLINEAR_LANDMARKS",
                source_name=source_name,
                rejection_reason="Landmarks are collinear; 3D rotation axis is mathematically unconstrained.",
            )

        # 1. Compute Centroids
        mu_src = [sum(p[i] for p in src_pts) / n for i in range(3)]
        mu_dst = [sum(p[i] for p in dst_pts) / n for i in range(3)]

        # 2. Center Points
        src_c = [[p[i] - mu_src[i] for i in range(3)] for p in src_pts]
        dst_c = [[p[i] - mu_dst[i] for i in range(3)] for p in dst_pts]

        # 3. Compute Source Variance
        var_src = sum(sum(p[i] ** 2 for i in range(3)) for p in src_c) / n

        # 4. Cross-covariance matrix H (3x3): H = (1/n) * src_c^T * dst_c
        h = [[0.0] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                h[i][j] = sum(src_c[k][i] * dst_c[k][j] for k in range(n)) / n

        # 5. SVD: H = U * S * V^T
        u, s_vals, vt = svd_3x3(h)
        v = mat3_transpose(vt)

        # 6. Reflection test: det(V * U^T)
        ut = mat3_transpose(u)
        v_ut = mat3_mult(v, ut)
        d = mat3_det(v_ut)

        # Proper rotation constraint
        s_matrix = mat3_identity()
        if d < 0.0:
            s_matrix[2][2] = -1.0

        r = mat3_mult(mat3_mult(v, s_matrix), ut)

        # 7. Scale
        if allow_scaling and var_src > 1e-12:
            scale = sum(s_vals[i] * s_matrix[i][i] for i in range(3)) / var_src
        else:
            scale = 1.0

        # 8. Translation: t = mu_dst - scale * R * mu_src
        r_mu_src = [
            sum(r[i][k] * mu_src[k] for k in range(3))
            for i in range(3)
        ]
        t = (
            mu_dst[0] - scale * r_mu_src[0],
            mu_dst[1] - scale * r_mu_src[1],
            mu_dst[2] - scale * r_mu_src[2],
        )

        transform = RegistrationTransform(
            rotation_matrix=r,
            translation_vector=t,
            scale=scale,
            source_name=source_name,
        )

        # 9. Compute Residuals & Errors in Millimeters
        residuals = {}
        sum_sq_err = 0.0
        max_err = 0.0

        for i, key in enumerate(common_keys):
            transformed = transform.transform_point(src_pts[i])
            actual = dst_pts[i]
            dist_mm = self.registry.calculate_distance_mm(transformed, actual)
            residuals[key] = dist_mm
            sum_sq_err += dist_mm ** 2
            if dist_mm > max_err:
                max_err = dist_mm

        rms_err = math.sqrt(sum_sq_err / n)
        transform.rms_error_mm = rms_err
        transform.max_error_mm = max_err
        transform.landmark_residuals_mm = residuals

        # 10. Check Clinical Uncertainty & Error Thresholds
        max_permitted = MAX_PERMISSIBLE_RMS_MM.get(region, 25.0)
        if rms_err <= max_permitted:
            transform.status = "VERIFIED_ANATOMICAL_ANCHOR"
        else:
            transform.status = "HIGH_DISCREPANCY_UNVERIFIED"
            transform.rejection_reason = (
                f"Registration RMS error ({rms_err:.1f}mm) exceeds clinical tolerance threshold ({max_permitted:.1f}mm) for region '{region.value}'."
            )

        return transform

    def register_point_to_canonical(
        self,
        point_code: str,
        source_coords: Tuple[float, float, float],
        transform: RegistrationTransform,
        region: BodyRegion = BodyRegion.HEAD_NECK
    ) -> Dict[str, Any]:
        """Transform an acupoint into canonical frame with bounding box and uncertainty verification."""
        if transform.status in ("UNREGISTERED", "DEGENERATE_COLLINEAR_LANDMARKS"):
            return {
                "point_code": point_code,
                "canonical_coords": None,
                "status": transform.status,
                "rejection_reason": transform.rejection_reason,
            }

        transformed = transform.transform_point(source_coords)

        # Bounding box envelope test
        if not self.validate_body_envelope(transformed):
            return {
                "point_code": point_code,
                "canonical_coords": list(transformed),
                "status": "OUT_OF_ANATOMICAL_BOUNDS",
                "rejection_reason": f"Transformed coordinates {transformed} fall outside human anatomical envelope.",
            }

        status = transform.status
        nearest_lm, lm_dist = self.registry.find_nearest_landmark(transformed, region)

        return {
            "point_code": point_code,
            "canonical_coords": [round(c, 5) for c in transformed],
            "status": status,
            "rms_error_mm": transform.rms_error_mm,
            "nearest_landmark": nearest_lm.landmark_id if nearest_lm else None,
            "distance_to_landmark_mm": round(lm_dist, 2) if nearest_lm else None,
            "rejection_reason": transform.rejection_reason,
        }
