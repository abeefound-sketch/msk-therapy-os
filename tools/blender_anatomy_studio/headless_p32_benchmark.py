"""Blender Headless Benchmark for Milestone P32.
Loads p29_anatomical_rig_binding.blend, evaluates 100 keyframes through depsgraph,
measures FPS and memory, and saves final release scene.
"""
import json
import os
import sys
import time
from pathlib import Path

import bpy

def run_blender_benchmark():
    start_time = time.perf_counter()

    repo_root = Path(bpy.data.filepath).resolve().parents[4] if bpy.data.filepath else Path("D:/5Projects/msk-therapy-os")
    p29_blend = repo_root / "1docs" / "audits" / "P29" / "evidence" / "p29_anatomical_rig_binding.blend"
    out_blend = repo_root / "1docs" / "audits" / "P32" / "evidence" / "p32_final_release.blend"
    metrics_json = repo_root / "1docs" / "audits" / "P32" / "evidence" / "p32_blender_benchmark.json"

    print(f"Loading reference blend: {p29_blend}")
    load_start = time.perf_counter()
    bpy.ops.wm.open_mainfile(filepath=str(p29_blend))
    load_time = time.perf_counter() - load_start

    scene = bpy.context.scene
    armature = bpy.data.objects.get("Armature_UpperLimb_R")
    humerus = bpy.data.objects.get("Humerus_R")
    scapula = bpy.data.objects.get("Scapula_R")
    li14_marker = next((o for o in bpy.data.objects if "LI14" in o.name), None)
    li15_marker = next((o for o in bpy.data.objects if "LI15" in o.name), None)

    # Benchmark 100 frames playback / depsgraph evaluation
    eval_start = time.perf_counter()
    frame_count = 100
    for f in range(1, frame_count + 1):
        scene.frame_set(f)
        # Force dependency graph evaluation
        _ = bpy.context.evaluated_depsgraph_get()

    eval_duration = time.perf_counter() - eval_start
    playback_fps = frame_count / eval_duration if eval_duration > 0 else 0.0

    # Save final release scene
    out_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
    save_file_size = out_blend.stat().st_size

    metrics = {
        "blender_version": bpy.app.version_string,
        "scene_load_time_sec": round(load_time, 4),
        "depsgraph_eval_duration_sec": round(eval_duration, 4),
        "total_frames_evaluated": frame_count,
        "effective_playback_fps": round(playback_fps, 2),
        "avg_frame_latency_ms": round((eval_duration / frame_count) * 1000.0, 2),
        "release_blend_path": str(out_blend),
        "release_blend_size_bytes": save_file_size,
        "objects_in_scene": len(bpy.data.objects),
        "meshes_in_scene": len(bpy.data.meshes),
        "armature_present": armature is not None,
        "humerus_present": humerus is not None,
        "scapula_present": scapula is not None,
        "li14_present": li14_marker is not None,
        "li15_present": li15_marker is not None,
    }

    metrics_json.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"BENCHMARK_SUCCESS: {json.dumps(metrics)}")


if __name__ == "__main__":
    run_blender_benchmark()
