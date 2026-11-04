"""Inspect exact bounding boxes and joint connection surfaces of right upper limb bones in BodyParts3D dataset."""
import json
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ATLAS_PATH = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models" / "atlas.json"
MODELS_DIR = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models"

TARGET_IDS = {
    "FJ3362": "Right clavicle",
    "FJ3384": "Right scapula",
    "FJ3368": "Right humerus",
    "FJ3349": "Right radius",
    "FJ3391": "Right ulna",
    "FJ3352": "Right second metacarpal bone"
}

atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
parts = {p["id"]: p for p in atlas["parts"] if p["id"] in TARGET_IDS}

print("=== BODYPARTS3D RIGHT UPPER LIMB MESH BOUNDS ===")
for pid, name in TARGET_IDS.items():
    p = parts.get(pid)
    if not p:
        print(f"Missing {pid} ({name})")
        continue
    bounds = p["bounds"]
    min_pt, max_pt = bounds[0], bounds[1]
    center = [(min_pt[i] + max_pt[i]) / 2.0 for i in range(3)]
    size = [max_pt[i] - min_pt[i] for i in range(3)]
    print(f"\n{pid} ({name}):")
    print(f"  Min:    [{min_pt[0]:.4f}, {min_pt[1]:.4f}, {min_pt[2]:.4f}]")
    print(f"  Max:    [{max_pt[0]:.4f}, {max_pt[1]:.4f}, {max_pt[2]:.4f}]")
    print(f"  Center: [{center[0]:.4f}, {center[1]:.4f}, {center[2]:.4f}]")
    print(f"  Size:   [{size[0]:.4f}, {size[1]:.4f}, {size[2]:.4f}] (Span X, Height Y, Depth Z)")

# Compute joint articulation contact points
# 1. Sternoclavicular (Clavicle medial end): max X of Clavicle (since right side is -X, medial is towards 0)
clav_p = parts["FJ3362"]
scap_p = parts["FJ3384"]
hum_p = parts["FJ3368"]
rad_p = parts["FJ3349"]
uln_p = parts["FJ3391"]
meta_p = parts["FJ3352"]

print("\n=== ANATOMICAL JOINT CONTACT ANALYSIS ===")
# Sternoclavicular: medial end of clavicle
sc_joint = [clav_p["bounds"][1][0], (clav_p["bounds"][0][1] + clav_p["bounds"][1][1])/2, (clav_p["bounds"][0][2] + clav_p["bounds"][1][2])/2]
print(f"1. Sternoclavicular (SC) joint pivot: ~[{sc_joint[0]:.4f}, {sc_joint[1]:.4f}, {sc_joint[2]:.4f}]")

# Acromioclavicular: lateral end of clavicle meets acromion of scapula
ac_joint = [clav_p["bounds"][0][0], (clav_p["bounds"][0][1] + clav_p["bounds"][1][1])/2, (clav_p["bounds"][0][2] + clav_p["bounds"][1][2])/2]
print(f"2. Acromioclavicular (AC) joint:       ~[{ac_joint[0]:.4f}, {ac_joint[1]:.4f}, {ac_joint[2]:.4f}]")

# Glenohumeral (Shoulder): Humerus proximal head
gh_joint = [
    (hum_p["bounds"][0][0] + hum_p["bounds"][1][0])/2,
    hum_p["bounds"][1][1] - 0.02, # near top of humerus
    (hum_p["bounds"][0][2] + hum_p["bounds"][1][2])/2
]
print(f"3. Glenohumeral (Shoulder) pivot:     ~[{gh_joint[0]:.4f}, {gh_joint[1]:.4f}, {gh_joint[2]:.4f}]")

# Elbow: Humerus distal condyle meets proximal radius/ulna
elbow_joint = [
    (hum_p["bounds"][0][0] + hum_p["bounds"][1][0])/2,
    hum_p["bounds"][0][1] + 0.015, # near distal end of humerus
    (hum_p["bounds"][0][2] + hum_p["bounds"][1][2])/2
]
print(f"4. Elbow joint pivot:                  ~[{elbow_joint[0]:.4f}, {elbow_joint[1]:.4f}, {elbow_joint[2]:.4f}]")

# Wrist: Distal radius meets carpus / metacarpal base
wrist_joint = [
    (rad_p["bounds"][0][0] + rad_p["bounds"][1][0])/2,
    rad_p["bounds"][0][1] + 0.01, # distal radius
    (rad_p["bounds"][0][2] + rad_p["bounds"][1][2])/2
]
print(f"5. Wrist joint pivot:                  ~[{wrist_joint[0]:.4f}, {wrist_joint[1]:.4f}, {wrist_joint[2]:.4f}]")
