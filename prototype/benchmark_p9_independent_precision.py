import time
import math
import psutil
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import List, Dict, Tuple
from msk_therapy_os.landmark_registry import LandmarkRegistry, BodyRegion
from msk_therapy_os.anatomical_registration import AnatomicalRegistrationEngine, svd_3x3
from msk_therapy_os.cun_scaling import CunScalingEngine
from msk_therapy_os.pose_rigging import PoseKinematicsEngine, GuardedSurfaceProjector

proc = psutil.Process(os.getpid())
reg = LandmarkRegistry()
reg_engine = AnatomicalRegistrationEngine(reg)
cun_engine = CunScalingEngine()
pose_engine = PoseKinematicsEngine(reg)
projector = GuardedSurfaceProjector()

src_torso = {
    'LM_C7_SPINE': (0.04, 1.328, -0.072),
    'LM_JUGULAR_NOTCH': (0.04, 1.258, 0.072),
    'LM_XIPHOSTERNAL_JOINT': (0.04, 1.048, 0.118),
    'LM_UMBILICUS': (0.04, 0.876, 0.132),
}

def benchmark_op(name, warmup_fn, run_fn, warmups=100, samples=1000):
    for _ in range(warmups):
        warmup_fn()
    
    t_proc_start = time.process_time()
    mem_start = proc.memory_info().rss / (1024 * 1024)
    
    times = []
    for _ in range(samples):
        t0 = time.perf_counter()
        run_fn()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1e6)  # microseconds
        
    t_proc_end = time.process_time()
    mem_end = proc.memory_info().rss / (1024 * 1024)
    
    times.sort()
    n = len(times)
    mean_val = sum(times) / n
    median_val = times[n // 2]
    p95_val = times[int(n * 0.95)]
    p99_val = times[int(n * 0.99)]
    min_val = times[0]
    max_val = times[-1]
    throughput = 1e6 / mean_val if mean_val > 0 else 0
    total_wall_s = sum(times) / 1e6
    proc_cpu_ratio = ((t_proc_end - t_proc_start) / total_wall_s * 100) if total_wall_s > 0 else 0
    
    return {
        'name': name,
        'mean_us': mean_val,
        'median_us': median_val,
        'p95_us': p95_val,
        'p99_us': p99_val,
        'min_us': min_val,
        'max_us': max_val,
        'throughput_ops': throughput,
        'cpu_util_pct': proc_cpu_ratio,
        'mem_delta_mb': mem_end - mem_start,
    }

results = []

# 1. Umeyama SVD Alignment
results.append(benchmark_op(
    'Umeyama 3x3 SVD Alignment',
    lambda: reg_engine.calculate_umeyama_alignment(src_torso, region=BodyRegion.TORSO),
    lambda: reg_engine.calculate_umeyama_alignment(src_torso, region=BodyRegion.TORSO),
))

# 2. WHO B-cun Regional Metrics
results.append(benchmark_op(
    'WHO B-cun 11-Segment Metrics',
    lambda: cun_engine.calculate_segment_metrics(nominal_height_mm=1720.0),
    lambda: cun_engine.calculate_segment_metrics(nominal_height_mm=1720.0),
))

# 3. 30-Landmark Forward Kinematics
posture_angles = {'cervical_flexion_deg': 15.0, 'elbow_flexion_left_deg': 30.0, 'knee_flexion_left_deg': 20.0}
results.append(benchmark_op(
    '30-Landmark Forward Kinematics',
    lambda: pose_engine.compute_pose_transformed_landmarks(posture_angles),
    lambda: pose_engine.compute_pose_transformed_landmarks(posture_angles),
))

# 4. Guarded Surface Projection
anchor = (0.0, 1.2, 0.05)
surface_hit = (0.0, 1.2, 0.10)
normal = (0.0, 0.0, 1.0)
expected_dir = (0.0, 0.0, 1.0)

results.append(benchmark_op(
    'Guarded Surface Projection',
    lambda: projector.project_safely(anchor, surface_hit, normal, expected_dir, BodyRegion.TORSO),
    lambda: projector.project_safely(anchor, surface_hit, normal, expected_dir, BodyRegion.TORSO),
))

# 5. Complete End-to-End Pipeline
def run_e2e():
    tr = reg_engine.calculate_umeyama_alignment(src_torso, region=BodyRegion.TORSO)
    cm = cun_engine.calculate_segment_metrics(nominal_height_mm=1720.0)
    lm = pose_engine.compute_pose_transformed_landmarks(posture_angles)
    pj = projector.project_safely(anchor, surface_hit, normal, expected_dir, BodyRegion.TORSO)

results.append(benchmark_op(
    'Complete End-to-End Pipeline',
    run_e2e,
    run_e2e,
))

print('| Subsystem | Mean (us) | Median (us) | P95 (us) | P99 (us) | Min (us) | Max (us) | Throughput (ops/s) | CPU Util (%) |')
print('| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |')
for r in results:
    print(f"| {r['name']} | {r['mean_us']:.2f} | {r['median_us']:.2f} | {r['p95_us']:.2f} | {r['p99_us']:.2f} | {r['min_us']:.2f} | {r['max_us']:.2f} | {r['throughput_ops']:,.0f} | {r['cpu_util_pct']:.1f}% |")

with open('2data/evidence/release_readiness/p9_precision_benchmark.json', 'w') as f:
    json.dump(results, f, indent=2)
