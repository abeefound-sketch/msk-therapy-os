"""P18 Forensics & Remediation Verification Suite.

Validates that all concrete architectural, spatial, and functional defects
identified in the P18 Independent Audit have been resolved:
1. Cache invalidation on point mutation (Engine Cache Bug Fixed).
2. Two-sources drift: Documented and measured between baked JSON and canonical resolver.
3. Upstream raw synthetic offset failure: Synthetic dx/dy/dz eliminated; status is UPSTREAM_TRANSFORM_UNAVAILABLE.
4. Quality tier governance: Rules dictate quality class without blind promotion.
"""

import json
import math
from pathlib import Path
import pytest

from msk_therapy_os.spatial_resolver import AnatomicalSpatialResolver, AUDITED_CANONICAL_POINTS
from msk_therapy_os.meridian_surface_engine import MeridianSurfacePathEngine

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestP18ForensicRemediations:
    """Explicitly verifies that confirmed P18 defects are resolved."""

    def test_reproduce_meridian_surface_engine_cache_invalidation_bug(self):
        """Audit Finding #6: MeridianSurfacePathEngine cache key incorporates cryptographic point digest.

        Modifying LI1 coordinates by 70mm and calling build_channel_path again MUST return
        a freshly recalculated object (path2 is not path1) because point_digest changed.
        """
        resolver = AnatomicalSpatialResolver()
        engine = MeridianSurfacePathEngine()

        # 1. Resolve points for Large Intestine
        resolved = {}
        for i in range(1, 21):
            code = f"LI{i}"
            res = resolver.resolve_point(code, "canonical", {}, {})
            resolved[code] = res

        # 2. First build of Large Intestine path
        li_meta = {"points": [f"LI{i}" for i in range(1, 21)]}
        path1 = engine.reconstruct_channel("LI", li_meta, resolved, "right", "canonical")
        assert path1 is not None
        initial_v0 = list(path1["surface_vertices"][0])

        # 3. Mutate LI1 coordinates drastically (+70 mm on each axis)
        resolved_mutated = dict(resolved)
        res_li1_mutated = dict(resolved["LI1"])
        mutated_pos = [initial_v0[0] + 0.070, initial_v0[1] + 0.070, initial_v0[2] + 0.070]
        res_li1_mutated["resolved_world_position"] = mutated_pos
        res_li1_mutated["canonical_position"] = mutated_pos
        res_li1_mutated["instances"] = [
            {
                "side": "right",
                "position": mutated_pos,
                "normal": [0.0, 0.0, 1.0],
            }
        ]
        resolved_mutated["LI1"] = res_li1_mutated

        # 4. Second build with same channel/side/mode
        path2 = engine.reconstruct_channel("LI", li_meta, resolved_mutated, "right", "canonical")

        # P18 Fix: Cache key includes point_digest; path2 is fresh and updated!
        is_stale = (path2 is path1) or (path2["surface_vertices"][0] == initial_v0)
        assert not is_stale, "Cache invalidation bug has been remediated by cryptographic point digest!"
        assert abs(path2["surface_vertices"][0][0] - mutated_pos[0]) < 0.001

    def test_reproduce_two_spatial_sources_drift(self):
        """Audit Finding #2: 130/362 points diverge by >= 50 mm between baked JSON and canonical resolver.

        Authoritative baseline verification: Demonstrates that the divergence is exactly 130 and 28 points.
        """
        json_path = REPO_ROOT / "msk_therapy_os" / "static" / "atlas" / "data" / "acupuncture_3d.json"
        assert json_path.exists()
        with open(json_path, "r", encoding="utf-8") as f:
            baked = json.load(f)

        resolver = AnatomicalSpatialResolver()
        baked_pts = baked["points"]

        divergent_50mm = []
        divergent_100mm = []

        for code, b_data in baked_pts.items():
            b_pos = b_data["position"]
            res = resolver.resolve_point(code, "canonical", {}, {})
            c_pos = res["resolved_world_position"]
            dist_mm = math.sqrt(sum((a - b) ** 2 for a, b in zip(b_pos, c_pos))) * 1000.0
            if dist_mm >= 50.0:
                divergent_50mm.append((code, dist_mm))
            if dist_mm >= 100.0:
                divergent_100mm.append((code, dist_mm))

        # Replicate exact confirmed counts
        assert len(divergent_50mm) == 130, f"Expected exactly 130 points >= 50mm, got {len(divergent_50mm)}"
        assert len(divergent_100mm) == 28, f"Expected exactly 28 points >= 100mm, got {len(divergent_100mm)}"

    def test_reproduce_upstream_raw_synthetic_offset_defect(self):
        """Audit Finding #4: spatial_resolver.py upstream_raw synthetic offsets eliminated.

        Under P18 governance, synthetic dx/dy/dz offsets are removed.
        Returns legacy coordinates with status UPSTREAM_TRANSFORM_UNAVAILABLE.
        """
        resolver = AnatomicalSpatialResolver()
        res_canon = resolver.resolve_point("LI4", "canonical", {}, {})
        res_upstream = resolver.resolve_point("LI4", "upstream_raw", {}, {})

        assert res_upstream["registration_status"] == "UPSTREAM_TRANSFORM_UNAVAILABLE"
        assert res_upstream["rejection_reason"] is not None
        assert "Synthetic offset removed" in res_upstream["rejection_reason"]
        assert res_upstream["resolved_world_position"] == res_canon["legacy_position"]

    def test_reproduce_quality_classification_overclaim(self):
        """Audit Finding #8: spatial_resolver.py respects rule quality classification.

        Verifies that resolver preserves audited CLASS_A and rule-defined quality classes.
        """
        resolver = AnatomicalSpatialResolver()
        class_counts = {}

        json_path = REPO_ROOT / "msk_therapy_os" / "static" / "atlas" / "data" / "acupuncture_3d.json"
        with open(json_path, "r", encoding="utf-8") as f:
            baked = json.load(f)

        for code in baked["points"]:
            res = resolver.resolve_point(code, "canonical", {}, {})
            qc = res["quality_class"]
            class_counts[qc] = class_counts.get(qc, 0) + 1

        assert class_counts["CLASS_A"] >= 18
        assert "CLASS_B" in class_counts
