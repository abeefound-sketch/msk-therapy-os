"""Reproducible upstream bootstrap and asset hash verification harness."""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class UpstreamSpec:
    name: str
    repo_url: str
    pinned_commit: str
    license_files: List[str]
    critical_assets: Dict[str, str]  # relative_path -> sha256


PINNED_UPSTREAMS: List[UpstreamSpec] = [
    UpstreamSpec(
        name="tcm-3d",
        repo_url="https://github.com/JICio/tcm-3d",
        pinned_commit="e8b9ad1c17e67a25e94406100e3fb5c296c24f7a",
        license_files=["LICENSE", "NOTICE"],
        critical_assets={
            "public/models/atlas.json": "c359f4bcd2cba90b7411d66d5e9fc04dc81294d46cd5c1e8b212c824f2e5bbee",
            "public/models/body-10.bin": "4a959d998acd35cf88518a0f2f8ab99b42d9f69c7ce0d6a814df315eeac807ac",
            "app/meridian-surface.json": "b172e3eb3ab1c018c77c8ac557b03b67a2a569294cce3b17a9c509d9a33284f6",
        },
    ),
    UpstreamSpec(
        name="acupuncture-3d-authoring",
        repo_url="https://github.com/eb-barry/acupuncture-3d-authoring",
        pinned_commit="cb7a41692276adcbf696538d30f2e3d8ecb4bbc6",
        license_files=["README.md", "THIRD_PARTY_NOTICES.md"],
        critical_assets={
            "models/male_character.glb": "1d52c883c830ff9bc53d146fe8fd199569735a6921569a401b0e05ded4825018",
            "src/data/acupuncture-data.json": "a6afdb28f3d42221250d075f623fc0b193ceb8049639bb743579283b67281d0b",
        },
    ),
    UpstreamSpec(
        name="anatomy-3d",
        repo_url="https://github.com/WaterCMY/anatomy-3d",
        pinned_commit="e8d40dca7b1f63f54567395df21d8b1b38a7e840",
        license_files=["LICENSE", "LICENSE-MODEL"],
        critical_assets={
            "models/anatomy.glb": "318347f91e4989da0c271e9662df536943df1149b413fef01cf21586073ea73e",
            "index.html": None,  # Checked for presence
        },
    ),
    UpstreamSpec(
        name="tcm-acupoints",
        repo_url="https://github.com/spacejohnlf/tcm-acupoints",
        pinned_commit="04e35abb66585eb29c7250ea8ab5243c8c744f64",
        license_files=["LICENSE", "ATTRIBUTION.md"],
        critical_assets={
            "public/models/body.glb": "0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3",
            "src/lib/acupoint-data.ts": "140169b2f360bf661bbf0adf60869a171e22289bef3e158ddca65e9fccb93ed1",
        },
    ),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class BootstrapManager:
    """Manages cloning, verifying commits, and verifying asset integrity."""

    def __init__(self, upstream_root: Path | str | None = None, artifacts_dir: Path | str | None = None):
        if upstream_root is None:
            self.upstream_root = Path(__file__).resolve().parents[1] / "upstream"
        else:
            self.upstream_root = Path(upstream_root)

        if artifacts_dir is None:
            self.artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
        else:
            self.artifacts_dir = Path(artifacts_dir)

        self.upstream_root.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def bootstrap_all(self, fetch_if_missing: bool = True) -> Dict[str, Any]:
        report = {
            "verified_at": json.loads(json.dumps(None)),
            "upstreams": {},
            "all_passed": True,
        }

        manifest_entries = []

        for spec in PINNED_UPSTREAMS:
            repo_dir = self.upstream_root / spec.name
            upstream_res: Dict[str, Any] = {
                "name": spec.name,
                "url": spec.repo_url,
                "target_commit": spec.pinned_commit,
                "installed": repo_dir.exists(),
                "commit_match": False,
                "actual_commit": None,
                "licenses_present": [],
                "missing_licenses": [],
                "asset_checks": {},
                "status": "PASS",
            }

            # 1. Clone if missing
            if not repo_dir.exists():
                if fetch_if_missing:
                    print(f"Cloning {spec.name} from {spec.repo_url}...")
                    subprocess.run(
                        ["git", "clone", spec.repo_url, str(repo_dir)],
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["git", "-C", str(repo_dir), "checkout", spec.pinned_commit],
                        check=True,
                        capture_output=True,
                    )
                    upstream_res["installed"] = True
                else:
                    upstream_res["status"] = "BLOCKED_MISSING_REPO"
                    report["all_passed"] = False
                    report["upstreams"][spec.name] = upstream_res
                    continue

            # 2. Verify commit SHA
            try:
                cp = subprocess.run(
                    ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                actual_sha = cp.stdout.strip()
                upstream_res["actual_commit"] = actual_sha
                upstream_res["commit_match"] = (actual_sha.lower() == spec.pinned_commit.lower())
                if not upstream_res["commit_match"]:
                    upstream_res["status"] = "FAIL_COMMIT_MISMATCH"
                    report["all_passed"] = False
            except Exception as e:
                upstream_res["status"] = f"FAIL_GIT_ERROR: {e}"
                report["all_passed"] = False

            # 3. Check licenses
            for lic_file in spec.license_files:
                p_lic = repo_dir / lic_file
                if p_lic.exists():
                    upstream_res["licenses_present"].append(lic_file)
                else:
                    upstream_res["missing_licenses"].append(lic_file)
            if upstream_res["missing_licenses"]:
                upstream_res["status"] = "FAIL_MISSING_LICENSE"
                report["all_passed"] = False

            # 4. Check critical asset SHA256 hashes
            for rel_asset, expected_hash in spec.critical_assets.items():
                p_asset = repo_dir / rel_asset
                if not p_asset.exists():
                    upstream_res["asset_checks"][rel_asset] = {
                        "exists": False,
                        "status": "FAIL_MISSING",
                    }
                    upstream_res["status"] = "FAIL_MISSING_ASSET"
                    report["all_passed"] = False
                else:
                    actual_h = sha256_file(p_asset)
                    matches = (expected_hash is None) or (actual_h.lower() == expected_hash.lower())
                    upstream_res["asset_checks"][rel_asset] = {
                        "exists": True,
                        "actual_sha256": actual_h,
                        "expected_sha256": expected_hash,
                        "match": matches,
                        "status": "PASS" if matches else "FAIL_HASH_MISMATCH",
                    }
                    if not matches:
                        upstream_res["status"] = "FAIL_HASH_MISMATCH"
                        report["all_passed"] = False

                    manifest_entries.append({
                        "upstream": spec.name,
                        "asset": rel_asset,
                        "sha256": actual_h,
                        "size_bytes": p_asset.stat().st_size,
                    })

            report["upstreams"][spec.name] = upstream_res

        # Write manifest
        out_manifest = self.artifacts_dir / "upstream_hashes.json"
        with open(out_manifest, "w", encoding="utf-8") as f:
            json.dump(manifest_entries, f, indent=2)

        return report
