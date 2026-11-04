"""Fetch a small authentic CMU Mocap trial for P23 motion bank."""
import hashlib
import json
import urllib.request
from pathlib import Path

DEST_DIR = Path(__file__).resolve().parents[2] / "research" / "motion_samples"
DEST_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES = [
    ("02.asf", "http://mocap.cs.cmu.edu/subjects/02/02.asf"),
    ("02_01.amc", "http://mocap.cs.cmu.edu/subjects/02/02_01.amc"),
]

def fetch_samples():
    results = {}
    for name, url in SAMPLES:
        out_path = DEST_DIR / name
        try:
            print(f"Fetching {name} from {url}...")
            urllib.request.urlretrieve(url, str(out_path))
            data = out_path.read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            results[name] = {
                "status": "DOWNLOADED",
                "size_bytes": len(data),
                "sha256": sha,
                "url": url
            }
            print(f"  {name}: {len(data)} bytes, sha256: {sha[:16]}...")
        except Exception as e:
            results[name] = {
                "status": "FAILED",
                "error": str(e),
                "url": url
            }
            print(f"  {name}: FAILED -> {e}")

    manifest_path = DEST_DIR / "cmu_samples_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved manifest to {manifest_path}")

if __name__ == "__main__":
    fetch_samples()
