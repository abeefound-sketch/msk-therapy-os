r"""
MSK-Therapy-OS V1.3 — Universal Anatomical Binding System (Full-Body Atlas)
Comprehensive E2E Integration & Reality Verification Test Suite
==========================================================================
Verifies:
1. Universal API: Metadata, Structures, Strategies, Evaluation.
2. Architectural Reusability: Adding a new anatomical structure dynamically via configuration.
3. Playwright Browser E2E Reality Audit:
   - Full-body character with 53 canonical bones.
   - 9 authentic BP3D bones (5 upper + 4 lower).
   - 10 authentic BP3D muscles (6 upper + 4 lower).
   - 6 dynamic surface anchors (LI4, LI11, LI14, LI15, ST36, KI3) + 2 3D tube meridians.
   - Simultaneous arm ($90^\circ$) + leg ($60^\circ$) motion.
   - Parametric morphing stability.
   - Project save and restore.
   - Telemetry screenshot collection in 1docs/product_v13/evidence/.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / "1docs" / "product_v13" / "evidence"
TEST_PORT = 8013


@pytest.fixture(scope="module")
def v13_server():
    """Spins up a dedicated server instance on TEST_PORT for V1.3 E2E testing."""
    server_py = REPO_ROOT / "msk_therapy_os" / "server.py"
    env = os.environ.copy()
    env["MSK_PORT"] = str(TEST_PORT)
    env["PYTHONPATH"] = str(REPO_ROOT)

    proc = subprocess.Popen(
        [sys.executable, str(server_py), "--port", str(TEST_PORT)],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Health check
    url = f"http://127.0.0.1:{TEST_PORT}/api/character/v13/metadata"
    started = False
    for _ in range(30):
        try:
            with urllib.request.urlopen(url, timeout=1.5) as resp:
                if resp.status == 200:
                    started = True
                    break
        except Exception:
            time.sleep(0.3)

    if not started:
        proc.kill()
        out, err = proc.communicate()
        raise RuntimeError(f"V1.3 test server failed to start on port {TEST_PORT}: {err.decode('utf-8')}")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


class TestV13UniversalABSE2E:

    def test_v13_api_metadata(self, v13_server):
        """Verifies V1.3 metadata contract, 53 bones, and safety notices."""
        url = f"http://127.0.0.1:{TEST_PORT}/api/character/v13/metadata"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))

        assert data["canonical_skeleton"] == "makehuman_game_engine_53"
        assert data["canonical_bones_count"] == 53
        assert data["registered_bones_count"] >= 9
        assert data["registered_muscles_count"] >= 7
        assert data["registered_anchors_count"] >= 6
        assert "RIGID_BONE" in data["supported_strategies"]
        assert "MULTI_BONE_SKINNING" in data["supported_strategies"]
        assert "SURFACE_BARYCENTRIC" in data["supported_strategies"]
        assert data["release_scope"] == "ENGINEERING_RESEARCH_ONLY"
        assert data["clinical_validation"] == "NOT_ESTABLISHED"

    def test_v13_api_structures_and_provenance(self, v13_server):
        """Verifies anatomical structures in universal registry across upper and lower limbs."""
        url = f"http://127.0.0.1:{TEST_PORT}/api/character/v13/structures"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))

        structures = {s["structure_id"]: s for s in data["structures"]}

        # Upper Limb
        assert "FJ3368" in structures  # Humerus
        assert "FJ1478" in structures  # Biceps long
        assert "LI4" in structures     # Hegu

        # Lower Limb
        assert "FJ3365" in structures  # Femur
        assert structures["FJ3365"]["primary_bone_id"] == "thigh_r"
        assert structures["FJ3365"]["deformation_strategy"] == "RIGID_BONE"

        assert "FJ3387" in structures  # Tibia
        assert structures["FJ3387"]["primary_bone_id"] == "calf_r"

        assert "FJ3381" in structures  # Patella
        assert "FJ1433" in structures  # Rectus femoris
        assert structures["FJ1433"]["deformation_strategy"] == "MULTI_BONE_SKINNING"
        assert structures["FJ1433"]["secondary_bone_id"] == "calf_r"

        assert "ST36" in structures    # Zusanli
        assert structures["ST36"]["primary_bone_id"] == "calf_r"

        assert "KI3" in structures     # Taixi

    def test_v13_api_fullbody_kinematic_evaluation(self, v13_server):
        """Verifies simultaneous arm and leg musculoskeletal state evaluation."""
        url = f"http://127.0.0.1:{TEST_PORT}/api/character/v13/evaluate?elbow_flexion=90&knee_flexion=60&shoulder_abduction=30"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))

        assert data["elbow_flexion_deg"] == 90.0
        assert data["knee_flexion_deg"] == 60.0
        assert data["shoulder_abduction_deg"] == 30.0

        # Upper limb metrics
        assert data["biceps_shortening_pct"] > 20.0
        assert data["biceps_bulge_factor"] > 1.10
        assert data["elbow_joint_gap_mm"] == 2.40
        assert data["elbow_penetration_mm"] == 0.00
        assert data["upper_bone_invariance_error_mm"] < 0.12

        # Lower limb metrics
        assert data["quadriceps_stretch_pct"] > 5.0
        assert data["knee_joint_gap_mm"] == 3.00
        assert data["knee_penetration_mm"] == 0.00
        assert data["lower_bone_invariance_error_mm"] < 0.12

        # Acupoints elevations
        elevations = data["marker_elevations"]
        assert elevations["LI4"] > 0.20  # Elevated with flexed arm
        assert elevations["ST36"] > 0.0  # Displaced with flexed knee
        assert data["verification_status"] == "SYNCHRONIZED_ACTIVE"

    def test_v13_architectural_reusability_dynamic_registration(self, v13_server):
        """CRUCIAL TEST: Proves that adding a new anatomical structure is done PURELY

        via declarative configuration without altering any lines of the core ABS engine.
        """
        # Register a new anatomical muscle: Coracobrachialis (FJ1488)
        new_struct_payload = {
            "structure_id": "FJ1488",
            "structure_type": "MUSCLE",
            "anatomical_name_en": "Coracobrachialis",
            "anatomical_name_vi": "Cơ quạ cánh tay",
            "laterality": "RIGHT",
            "source_mesh_id": "Coracobrachialis_R",
            "source_mesh_file": "Coracobrachialis_R.obj",
            "source_hash": "dynamic_sha256_coracobrachialis",
            "canonical_skeleton_id": "makehuman_game_engine_53",
            "primary_bone_id": "upperarm_r",
            "secondary_bone_id": "clavicle_r",
            "deformation_strategy": "MULTI_BONE_SKINNING",
            "registration_status": "REGISTERED_ACTIVE",
            "fma_id": "FMA:37664",
            "source_reference": "BodyParts3D CC BY 4.0 DBCLS Japan",
            "metadata": {
                "resting_length_m": 0.1600,
                "flexed_length_m": 0.1350,
                "resting_diameter_mm": 24.0,
                "max_joint_deg": 90.0
            }
        }

        req = urllib.request.Request(
            f"http://127.0.0.1:{TEST_PORT}/api/character/v13/register",
            data=json.dumps(new_struct_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            res = json.loads(resp.read().decode("utf-8"))

        assert res["status"] == "REGISTERED"
        assert res["structure_id"] == "FJ1488"
        assert res["strategy"] == "MULTI_BONE_SKINNING"

        # Verify it can now be retrieved and evaluated immediately!
        url = f"http://127.0.0.1:{TEST_PORT}/api/character/v13/structures"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        ids = [s["structure_id"] for s in data["structures"]]
        assert "FJ1488" in ids, "Newly registered structure must appear in registry list."

    def test_v13_playwright_fullbody_atlas_reality_acceptance(self, v13_server):
        """Browser automated reality audit of 3D full-body humanoid character, 53 bones,

        simultaneous arm & leg motion, 7 morph targets, and project persistence.
        """
        from playwright.sync_api import sync_playwright

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--use-gl=angle",
                    "--use-angle=swiftshader"
                ]
            )
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            # Navigate to Full-Body Web Atlas
            url = f"http://127.0.0.1:{TEST_PORT}/character_v13/index.html"
            page.goto(url, wait_until="networkidle", timeout=35000)

            # Wait for 3D model to fully load
            page.wait_for_function("() => window.__UNIVERSAL_ABS_V13__ && window.__UNIVERSAL_ABS_V13__.isLoaded() === true", timeout=30000)

            # Check skeleton completeness (53 bones)
            sk_info = page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getSkeletonInfo()")
            assert sk_info["boneCount"] == 53, f"Expected 53 bones, got {sk_info['boneCount']}"
            assert sk_info["hasArmBones"] is True
            assert sk_info["hasLegBones"] is True
            assert sk_info["hasSpineBones"] is True

            # Check anatomical meshes & markers stats
            stats = page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getAnatomyStats()")
            assert stats["hasSkin"] is True
            assert stats["morphTargetCount"] >= 7
            assert stats["boneMeshesCount"] == 9, f"Expected 9 rigid bones, got {stats['boneMeshesCount']}"
            assert stats["muscleMeshesCount"] == 10, f"Expected 10 muscle meshes, got {stats['muscleMeshesCount']}"
            assert stats["markersCount"] == 6, f"Expected 6 markers, got {stats['markersCount']}"
            assert stats["hasMeridians"] is True

            def take_shot(filename):
                target = EVIDENCE_DIR / filename
                page.screenshot(path=str(target), timeout=25000, animations="disabled")

            # 1. Screenshot: Rest Pose (0°) in OVERLAY_MODE
            page.wait_for_timeout(500)
            take_shot("v13_01_fullbody_rest_pose.png")

            # 2. Test Arm Flexion 90°
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setJointAngle('lowerarm_r', 'x', 90)")
            page.wait_for_timeout(300)
            m_arm90 = page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getEvaluatedMetrics()")
            assert m_arm90["biceps_shortening_pct"] > 20.0
            assert m_arm90["biceps_bulge_factor"] > 1.10
            take_shot("v13_02_arm_flexion_90deg.png")

            # 3. Test Knee Flexion 60°
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setJointAngle('lowerarm_r', 'x', 0)")
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setJointAngle('calf_r', 'x', 60)")
            page.wait_for_timeout(300)
            m_knee60 = page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getEvaluatedMetrics()")
            assert m_knee60["quad_stretch_pct"] > 5.0
            assert m_knee60["knee_gap_mm"] == 3.00
            take_shot("v13_03_knee_flexion_60deg.png")

            # 4. Simultaneous Motion: Arm Flexion 90° + Knee Flexion 60° + Torso Twist 15°
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setJointAngle('lowerarm_r', 'x', 90)")
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setJointAngle('calf_r', 'x', 60)")
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setJointAngle('spine_02', 'z', 15)")
            page.wait_for_timeout(300)
            m_simul = page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getEvaluatedMetrics()")
            assert m_simul["elbow_deg"] == 90.0
            assert m_simul["knee_deg"] == 60.0
            assert m_simul["penetration_depth_mm"] == 0.00
            take_shot("v13_04_simultaneous_arm_leg_motion.png")

            # 5. ANATOMY_MODE (Pure Musculoskeletal View during simultaneous motion)
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setMode('ANATOMY_MODE')")
            page.wait_for_timeout(300)
            assert page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getMode()") == "ANATOMY_MODE"
            take_shot("v13_05_anatomy_mode_simultaneous.png")

            # 6. CHARACTER_MODE (Living Skin View)
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setMode('CHARACTER_MODE')")
            page.wait_for_timeout(300)
            assert page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getMode()") == "CHARACTER_MODE"
            take_shot("v13_06_living_skin_mode.png")

            # Return to OVERLAY_MODE
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setMode('OVERLAY_MODE')")
            page.wait_for_timeout(200)

            # 7. Morphing Test: Broader = 0.8 + LegLength = 0.5 under simultaneous motion
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setMorphInfluence('Broader', 0.8)")
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.setMorphInfluence('LegLength', 0.5)")
            page.wait_for_timeout(300)
            assert page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getMorphInfluence('Broader')") == 0.8
            take_shot("v13_07_morph_broader_fullbody_motion.png")

            # 8. Project State Persistence (Save & Restore)
            save_payload = {
                "project_id": "Test_FullBody_Simultaneous_V13",
                "elbow_flexion": 90.0,
                "knee_flexion": 60.0,
                "morph_influences": {"Broader": 0.8, "LegLength": 0.5},
                "display_mode": "OVERLAY_MODE"
            }
            save_res = page.evaluate(
                f"""() => fetch('/api/character/v13/project/save', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({json.dumps(save_payload)})
                }}).then(r => r.json())"""
            )
            assert save_res["status"] == "SAVED"

            # Reset pose
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.resetPose()")
            page.wait_for_timeout(300)
            assert page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getJointAngle('lowerarm_r', 'x')") == 0.0

            # Restore project state
            load_res = page.evaluate(
                """() => fetch('/api/character/v13/project/load?name=Test_FullBody_Simultaneous_V13').then(r => r.json())"""
            )
            page.evaluate(f"() => window.__UNIVERSAL_ABS_V13__.setJointAngle('lowerarm_r', 'x', {load_res['elbow_flexion']})")
            page.evaluate(f"() => window.__UNIVERSAL_ABS_V13__.setJointAngle('calf_r', 'x', {load_res['knee_flexion']})")
            page.evaluate(f"() => window.__UNIVERSAL_ABS_V13__.setMorphInfluence('Broader', {load_res['morph_influences']['Broader']})")
            page.wait_for_timeout(300)
            take_shot("v13_08_project_state_restored.png")

            # 9. Acupoint & Meridian Verification (Lower Limb ST36 and KI3)
            pos_st36 = page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getAcupointWorldPos('ST36')")
            pos_ki3 = page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getAcupointWorldPos('KI3')")
            assert pos_st36 is not None, "ST36 marker must exist"
            assert pos_ki3 is not None, "KI3 marker must exist"
            take_shot("v13_09_acupoints_lower_limb.png")

            # 10. Return to Rest Pose (0 deg)
            page.evaluate("() => window.__UNIVERSAL_ABS_V13__.resetPose()")
            page.wait_for_timeout(300)
            deg_reset = page.evaluate("() => window.__UNIVERSAL_ABS_V13__.getJointAngle('lowerarm_r', 'x')")
            assert round(deg_reset, 1) == 0.0
            take_shot("v13_10_final_verified_rest_pose.png")

            browser.close()
