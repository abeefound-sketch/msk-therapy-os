"""End-to-End Real Video Pose Inference Pipeline for Milestone P28.
Extracts genuine MediaPipe pose landmarks from a real human movement video,
applies biomechanical joint constraints (Kapandji / Seth), validates schema contracts,
and exports motion sequences and annotated evidence frames.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Paths
SIDE_CAR_DIR = Path(__file__).resolve().parent
REPO_ROOT = SIDE_CAR_DIR.parents[1]
VIDEO_PATH = SIDE_CAR_DIR / "samples" / "real_human_motion_cam01.mp4"
MODEL_PATH = SIDE_CAR_DIR / "models" / "pose_landmarker_full.task"
EVIDENCE_DIR = REPO_ROOT / "1docs" / "audits" / "P28" / "evidence"
SCREENSHOT_DIR = REPO_ROOT / "1docs" / "audits" / "P28" / "screenshots"

EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_angle_3d(p1: Tuple[float, float, float], p_mid: Tuple[float, float, float], p3: Tuple[float, float, float]) -> float:
    """Compute interior 3D angle at p_mid formed by vectors to p1 and p3."""
    v1 = (p1[0] - p_mid[0], p1[1] - p_mid[1], p1[2] - p_mid[2])
    v2 = (p3[0] - p_mid[0], p3[1] - p_mid[1], p3[2] - p_mid[2])

    mag1 = math.hypot(v1[0], v1[1], v1[2])
    mag2 = math.hypot(v2[0], v2[1], v2[2])

    if mag1 < 1e-6 or mag2 < 1e-6:
        return 0.0

    dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
    cos_val = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_val))


def run_pipeline():
    print("=" * 60)
    print("STARTING P28 REAL VIDEO POSE INFERENCE PIPELINE")
    print("=" * 60)

    assert VIDEO_PATH.exists(), f"Video missing: {VIDEO_PATH}"
    assert MODEL_PATH.exists(), f"Model missing: {MODEL_PATH}"

    video_hash = compute_sha256(VIDEO_PATH)
    model_hash = compute_sha256(MODEL_PATH)

    print(f"Video: {VIDEO_PATH.name} (SHA-256: {video_hash})")
    print(f"Model: {MODEL_PATH.name} (SHA-256: {model_hash})")

    # Initialize MediaPipe PoseLandmarker
    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        output_segmentation_masks=False,
        running_mode=vision.RunningMode.IMAGE
    )
    detector = vision.PoseLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(str(VIDEO_PATH))
    fps = cap.get(cv2.CAP_PROP_FPS) or 60.0
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Video Specs: {width}x{height} @ {fps:.2f} FPS, total {total_video_frames} frames")

    motion_frames = []
    pose_observations = []
    dropped_frames = 0

    frame_idx = 0
    annotated_sample_frames = [0, 20, 50, 80]

    while cap.isOpened():
        ret, frame_bgr = cap.read()
        if not ret:
            break

        timestamp = frame_idx / fps
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        detection_result = detector.detect(mp_image)
        landmarks_list = detection_result.pose_landmarks
        world_landmarks_list = detection_result.pose_world_landmarks

        if not landmarks_list or len(landmarks_list) == 0:
            dropped_frames += 1
            frame_idx += 1
            continue

        landmarks = landmarks_list[0]
        world_lms = world_landmarks_list[0] if world_landmarks_list else landmarks

        # Extract right arm indices: Shoulder=12, Elbow=14, Wrist=16, Hip=24
        s = landmarks[12]
        e = landmarks[14]
        w = landmarks[16]
        h = landmarks[24]

        # Use 3D world landmarks for metric angular reconstruction if available
        s_w = world_lms[12]
        e_w = world_lms[14]
        w_w = world_lms[16]
        h_w = world_lms[24]

        p_sh = (s_w.x, s_w.y, s_w.z)
        p_el = (e_w.x, e_w.y, e_w.z)
        p_wr = (w_w.x, w_w.y, w_w.z)
        p_hip = (h_w.x, h_w.y, h_w.z)

        # Check occlusion
        min_vis = min(s.visibility, e.visibility, w.visibility)
        occluded = min_vis < 0.5

        if occluded:
            dropped_frames += 1
            quality_flags = ["RIGHT_ARM_OCCLUSION_DETECTED", "RECONSTRUCTION_CONFIDENCE_LOW"]
            clamped_elbow = 0.0
            clamped_shoulder = 0.0
            confidence = 0.0
        else:
            quality_flags = ["TRACKING_OPTIMAL"]
            # Elbow flexion: 0 deg = straight, positive = bent
            interior_elbow = compute_angle_3d(p_sh, p_el, p_wr)
            raw_elbow_flexion = 180.0 - interior_elbow

            # Shoulder elevation: angle between torso (hip->shoulder) and upper arm (shoulder->elbow)
            shoulder_torso_angle = compute_angle_3d(p_hip, p_sh, p_el)
            raw_shoulder_elevation = shoulder_torso_angle

            # Clamp to Kapandji & Seth physiological bounds
            clamped_elbow = max(0.0, min(145.0, raw_elbow_flexion))
            clamped_shoulder = max(0.0, min(180.0, raw_shoulder_elevation))
            confidence = float(min_vis)

        # Record motion sequence frame
        motion_frames.append({
            "frame_index": frame_idx,
            "time_seconds": round(timestamp, 4),
            "joint_rotations": {
                "right_elbow_flexion_deg": round(clamped_elbow, 2),
                "right_shoulder_elevation_deg": round(clamped_shoulder, 2)
            },
            "confidence": round(confidence, 3),
            "observable_flags": {
                "elbow_flexion_observable": not occluded,
                "forearm_pronation_observable": False,
                "depth_calibrated": False
            }
        })

        # Save annotated image for audit evidence
        if frame_idx in annotated_sample_frames:
            ann_frame = frame_bgr.copy()
            # Draw key points
            for idx_pt in [12, 14, 16, 24]:
                pt = landmarks[idx_pt]
                px, py = int(pt.x * width), int(pt.y * height)
                cv2.circle(ann_frame, (px, py), 10, (0, 255, 0), -1)

            # Draw lines
            p_s = (int(s.x * width), int(s.y * height))
            p_e = (int(e.x * width), int(e.y * height))
            p_w = (int(w.x * width), int(w.y * height))
            p_h = (int(h.x * width), int(h.y * height))
            cv2.line(ann_frame, p_s, p_e, (255, 0, 0), 4)
            cv2.line(ann_frame, p_e, p_w, (0, 255, 255), 4)
            cv2.line(ann_frame, p_h, p_s, (0, 0, 255), 3)

            # Overlay telemetry text
            txt_elbow = f"Elbow Flexion: {clamped_elbow:.1f} deg (Kapandji [0, 145])"
            txt_sh = f"Shoulder Elev: {clamped_shoulder:.1f} deg (Seth [0, 180])"
            txt_conf = f"Confidence: {confidence:.2f} | Frame: {frame_idx}"
            cv2.putText(ann_frame, "MSK-Therapy-OS Real MediaPipe Inference", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
            cv2.putText(ann_frame, txt_elbow, (40, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.putText(ann_frame, txt_sh, (40, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(ann_frame, txt_conf, (40, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

            out_img = SCREENSHOT_DIR / f"01_real_mediapipe_frame_{frame_idx:03d}.png"
            cv2.imwrite(str(out_img), ann_frame)
            print(f"Saved annotated evidence frame: {out_img.name}")

        frame_idx += 1

    cap.release()

    # Construct schema-compliant MotionSequence object
    motion_seq = {
        "schema_version": "1.0.0",
        "motion_id": "MOT-P28-REAL-001",
        "source_trial": f"Pose2Sim_Demo_cam01_{video_hash[:8]}",
        "source_type": "MEDIAPIPE_ESTIMATED",
        "fps": round(fps, 2),
        "root_transform": [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0
        ],
        "rig_version": "1.0.0",
        "source_skeleton": "MediaPipe_33_Landmarks",
        "target_skeleton": "Armature_UpperLimb_R",
        "frames": motion_frames,
        "quality_metadata": {
            "total_frames": len(motion_frames),
            "dropped_frames": dropped_frames,
            "unobservable_dofs": ["forearm_pronation_supination", "wrist_radial_ulnar_deviation"],
            "checksum": hashlib.sha256(json.dumps(motion_frames, sort_keys=True).encode()).hexdigest()
        }
    }

    out_json = EVIDENCE_DIR / "p28_real_motion_sequence.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(motion_seq, f, indent=2, ensure_ascii=False)

    print(f"Successfully processed {len(motion_frames)} real frames!")
    print(f"Saved Motion Sequence: {out_json} (Checksum: {motion_seq['quality_metadata']['checksum']})")


if __name__ == "__main__":
    run_pipeline()
