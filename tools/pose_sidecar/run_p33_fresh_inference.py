"""Milestone P33: Fresh Real Video Pose Inference & Telemetry Benchmark.
Executes live inference through Google MediaPipe Task Model on real video,
records per-frame latency, validates constraints, and exports debug screenshots.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

REPO_ROOT = Path(__file__).resolve().parents[2]
VIDEO_PATH = REPO_ROOT / "tools" / "pose_sidecar" / "samples" / "real_human_motion_cam01.mp4"
MODEL_PATH = REPO_ROOT / "tools" / "pose_sidecar" / "models" / "pose_landmarker_full.task"
EVIDENCE_DIR = REPO_ROOT / "1docs" / "audits" / "P33" / "evidence"
SCREENSHOT_DIR = REPO_ROOT / "1docs" / "audits" / "P33" / "screenshots"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_angle_3d(p1: Tuple[float, float, float], p_mid: Tuple[float, float, float], p3: Tuple[float, float, float]) -> float:
    v1 = (p1[0] - p_mid[0], p1[1] - p_mid[1], p1[2] - p_mid[2])
    v2 = (p3[0] - p_mid[0], p3[1] - p_mid[1], p3[2] - p_mid[2])

    mag1 = math.hypot(v1[0], v1[1], v1[2])
    mag2 = math.hypot(v2[0], v2[1], v2[2])

    if mag1 < 1e-6 or mag2 < 1e-6:
        return 0.0

    dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
    cos_val = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_val))


def get_peak_memory_mb() -> float:
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except Exception:
        # Fallback using Windows API
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return counters.PeakWorkingSetSize / (1024 * 1024)
    return -1.0


def run_fresh_inference():
    print("=" * 70)
    print("MSK-THERAPY-OS | P33 FRESH REAL VIDEO MEDIAPIPE INFERENCE RUN")
    print("=" * 70)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    assert VIDEO_PATH.exists(), f"Video missing: {VIDEO_PATH}"
    assert MODEL_PATH.exists(), f"Model missing: {MODEL_PATH}"

    video_sha256 = compute_sha256(VIDEO_PATH)
    model_sha256 = compute_sha256(MODEL_PATH)
    print(f"Video file: {VIDEO_PATH.name} ({VIDEO_PATH.stat().st_size:,} bytes)")
    print(f"  SHA-256: {video_sha256}")
    print(f"Model file: {MODEL_PATH.name} ({MODEL_PATH.stat().st_size:,} bytes)")
    print(f"  SHA-256: {model_sha256}")

    # Init MediaPipe detector
    init_start = time.perf_counter()
    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        output_segmentation_masks=False,
        running_mode=vision.RunningMode.IMAGE
    )
    detector = vision.PoseLandmarker.create_from_options(options)
    init_duration_sec = time.perf_counter() - init_start
    print(f"MediaPipe Task Initialization Duration: {init_duration_sec:.4f} s")

    cap = cv2.VideoCapture(str(VIDEO_PATH))
    fps = cap.get(cv2.CAP_PROP_FPS) or 60.0
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video Stream: {width}x{height} @ {fps:.2f} FPS | Total Video Frames: {total_video_frames}")

    frames_telemetry = []
    annotated_sample_frames = [0, 50, 99]
    frame_latencies_ms = []

    frame_idx = 0
    while cap.isOpened():
        ret, frame_bgr = cap.read()
        if not ret:
            break

        timestamp = frame_idx / fps
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Measure single-frame inference time precisely
        frame_t0 = time.perf_counter()
        detection_result = detector.detect(mp_image)
        frame_inference_ms = (time.perf_counter() - frame_t0) * 1000.0
        frame_latencies_ms.append(frame_inference_ms)

        landmarks_list = detection_result.pose_landmarks
        world_landmarks_list = detection_result.pose_world_landmarks

        if not landmarks_list or len(landmarks_list) == 0:
            frame_idx += 1
            continue

        lms = landmarks_list[0]
        world_lms = world_landmarks_list[0] if world_landmarks_list else lms

        # Landmarks: Right Shoulder=12, Elbow=14, Wrist=16, Hip=24
        s = lms[12]
        e = lms[14]
        w = lms[16]
        h = lms[24]

        s_w = world_lms[12]
        e_w = world_lms[14]
        w_w = world_lms[16]
        h_w = world_lms[24]

        p_sh = (s_w.x, s_w.y, s_w.z)
        p_el = (e_w.x, e_w.y, e_w.z)
        p_wr = (w_w.x, w_w.y, w_w.z)
        p_hip = (h_w.x, h_w.y, h_w.z)

        min_vis = min(s.visibility, e.visibility, w.visibility)
        occluded = min_vis < 0.5

        interior_elbow = compute_angle_3d(p_sh, p_el, p_wr)
        raw_elbow_flexion = 180.0 - interior_elbow
        raw_shoulder_elevation = compute_angle_3d(p_hip, p_sh, p_el)

        clamped_elbow = max(0.0, min(145.0, raw_elbow_flexion))
        clamped_shoulder = max(0.0, min(180.0, raw_shoulder_elevation))

        # Annotate debug image at sample frames
        if frame_idx in annotated_sample_frames:
            dbg_img = frame_bgr.copy()
            for idx in [12, 14, 16, 24]:
                lm = lms[idx]
                cx, cy = int(lm.x * width), int(lm.y * height)
                cv2.circle(dbg_img, (cx, cy), 6, (0, 255, 0), -1)
                cv2.putText(dbg_img, str(idx), (cx + 8, cy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            # Draw lines
            p_sh_px = (int(s.x * width), int(s.y * height))
            p_el_px = (int(e.x * width), int(e.y * height))
            p_wr_px = (int(w.x * width), int(w.y * height))
            cv2.line(dbg_img, p_sh_px, p_el_px, (0, 0, 255), 2)
            cv2.line(dbg_img, p_el_px, p_wr_px, (0, 255, 255), 2)

            info_text = f"F:{frame_idx} | T:{timestamp:.2f}s | Elb:{clamped_elbow:.1f}deg | Sh:{clamped_shoulder:.1f}deg | Inf:{frame_inference_ms:.1f}ms"
            cv2.putText(dbg_img, info_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(dbg_img, "P33 AUDIT: REAL VIDEO INFERENCE", (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

            out_png = SCREENSHOT_DIR / f"p33_mediapipe_frame_{frame_idx:03d}.png"
            cv2.imwrite(str(out_png), dbg_img)
            print(f"  Saved debug inference frame: {out_png.name}")

        frames_telemetry.append({
            "frame_index": frame_idx,
            "timestamp_sec": round(timestamp, 4),
            "inference_duration_ms": round(frame_inference_ms, 2),
            "min_landmark_visibility": round(float(min_vis), 3),
            "is_occluded": occluded,
            "raw_angles": {
                "elbow_flexion_deg": round(raw_elbow_flexion, 2),
                "shoulder_elevation_deg": round(raw_shoulder_elevation, 2)
            },
            "constrained_angles": {
                "elbow_flexion_deg": round(clamped_elbow, 2),
                "shoulder_elevation_deg": round(clamped_shoulder, 2)
            },
            "observable_flags": {
                "elbow_flexion_observable": not occluded,
                "forearm_pronation_observable": False,
                "depth_calibrated": False
            }
        })

        frame_idx += 1

    cap.release()

    peak_ram_mb = get_peak_memory_mb()
    avg_latency_ms = sum(frame_latencies_ms) / len(frame_latencies_ms) if frame_latencies_ms else 0.0
    effective_fps = 1000.0 / avg_latency_ms if avg_latency_ms > 0 else 0.0

    print("\n--- INFERENCE PERFORMANCE METRICS ---")
    print(f"Total Frames Processed: {len(frames_telemetry)}")
    print(f"Average Inference Latency: {avg_latency_ms:.2f} ms / frame")
    print(f"Min / Max Latency: {min(frame_latencies_ms):.2f} ms / {max(frame_latencies_ms):.2f} ms")
    print(f"Effective Inference Throughput: {effective_fps:.2f} frames/sec")
    print(f"Peak Process Working Set RAM: {peak_ram_mb:.2f} MB")

    # Three-frame keyframe comparison
    f_first = frames_telemetry[0]
    f_mid = frames_telemetry[len(frames_telemetry) // 2]
    f_last = frames_telemetry[-1]

    print("\n--- THREE-FRAME COMPARISON (FIRST / MID / LAST) ---")
    print(f"Frame {f_first['frame_index']} (T={f_first['timestamp_sec']}s): Sh={f_first['constrained_angles']['shoulder_elevation_deg']}°, Elb={f_first['constrained_angles']['elbow_flexion_deg']}°, Lat={f_first['inference_duration_ms']}ms")
    print(f"Frame {f_mid['frame_index']} (T={f_mid['timestamp_sec']}s): Sh={f_mid['constrained_angles']['shoulder_elevation_deg']}°, Elb={f_mid['constrained_angles']['elbow_flexion_deg']}°, Lat={f_mid['inference_duration_ms']}ms")
    print(f"Frame {f_last['frame_index']} (T={f_last['timestamp_sec']}s): Sh={f_last['constrained_angles']['shoulder_elevation_deg']}°, Elb={f_last['constrained_angles']['elbow_flexion_deg']}°, Lat={f_last['inference_duration_ms']}ms")

    report = {
        "milestone": "P33",
        "video_asset": {
            "filename": VIDEO_PATH.name,
            "sha256": video_sha256,
            "width": width,
            "height": height,
            "fps": fps,
            "total_frames": total_video_frames
        },
        "model_asset": {
            "filename": MODEL_PATH.name,
            "sha256": model_sha256,
            "framework": "Google MediaPipe Tasks Vision",
            "model_type": "pose_landmarker_full"
        },
        "performance": {
            "initialization_duration_sec": round(init_duration_sec, 4),
            "total_frames_processed": len(frames_telemetry),
            "avg_inference_latency_ms": round(avg_latency_ms, 2),
            "min_inference_latency_ms": round(min(frame_latencies_ms), 2),
            "max_inference_latency_ms": round(max(frame_latencies_ms), 2),
            "inference_throughput_fps": round(effective_fps, 2),
            "peak_process_ram_mb": round(peak_ram_mb, 2)
        },
        "three_frame_samples": {
            "first_frame": f_first,
            "middle_frame": f_mid,
            "last_frame": f_last
        },
        "frames": frames_telemetry
    }

    out_json = EVIDENCE_DIR / "p33_fresh_inference_run.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved Fresh Telemetry Evidence: {out_json} ({out_json.stat().st_size:,} bytes)")
    print("=" * 70)


if __name__ == "__main__":
    run_fresh_inference()
