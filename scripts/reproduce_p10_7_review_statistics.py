"""MSK-Therapy-OS P10.7 Independent Reviewer Statistical Reproduction Tool

Allows independent biostatistical and scientific reviewers to reproduce all sample size,
multi-level design effect, compound variance decomposition, and power calculations
from pure synthetic/analytical fixtures without accessing sensitive clinical data.

Usage:
    python scripts/reproduce_p10_7_review_statistics.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from msk_therapy_os.statistical_oracle import (
    IndependentStatisticalOracle,
    OracleStudyScenario,
)
from msk_therapy_os.protocol_freeze import ProtocolFreezeManager


def main() -> int:
    print("=" * 80)
    print("MSK-THERAPY-OS P10.7 INDEPENDENT SCIENTIFIC REVIEW REPRODUCTION RUNNER")
    print("=" * 80)
    print(f"Target Protocol Version: {ProtocolFreezeManager.CURRENT_PROTOCOL_VERSION}")
    print(f"Target Release Tag:      {ProtocolFreezeManager.RELEASE_TAG}")
    
    manifest = ProtocolFreezeManager.create_freeze_candidate_manifest()
    valid, err = ProtocolFreezeManager.verify_manifest_integrity(manifest)
    print(f"Protocol Manifest Hash:  {manifest.canonical_hash}")
    print(f"Manifest Integrity:      {'VERIFIED' if valid else 'FAILED: ' + str(err)}")
    print("-" * 80)

    print("\n[SECTION 1: FORENSIC SAMPLE SIZE SCENARIO COMPARISON]")
    scenarios = [
        OracleStudyScenario.FEASIBILITY_PILOT,
        OracleStudyScenario.PRIMARY_ACCURACY_STUDY,
        OracleStudyScenario.EXPANDED_ACCURACY_STUDY,
        OracleStudyScenario.MULTI_SITE_VALIDATION,
    ]

    print(f"{'Scenario':<25} | {'N':<4} | {'Holdout':<7} | {'Min Power':<10} | {'Subgroups OK?':<13} | {'Verdict'}")
    print("-" * 80)

    results = {}
    for sc in scenarios:
        res = IndependentStatisticalOracle.evaluate_scenario(sc)
        results[sc.value] = res
        print(
            f"{sc.value:<25} | "
            f"{res['total_patients']:<4} | "
            f"{res['total_holdout_patients']:<7} | "
            f"{res['minimum_subgroup_power']*100:>8.1f}% | "
            f"{str(res['all_subgroups_adequately_powered']):<13} | "
            f"{res['verdict']}"
        )

    print("\n[SECTION 2: DETAILED COHORT EVALUATION FOR RECOMMENDED PRIMARY PILOT (N=85)]")
    p85 = results[OracleStudyScenario.PRIMARY_ACCURACY_STUDY.value]
    print(f"{'Cohort ID':<24} | {'Region':<18} | {'N_tot':<5} | {'N_hold':<6} | {'M_eff':<6} | {'Total SD':<8} | {'95% CI':<8} | {'Power (z)'}")
    print("-" * 80)
    for c in p85["cohorts"]:
        print(
            f"{c['cohort_id']:<24} | "
            f"{c['target_region']:<18} | "
            f"{c['total_subjects']:<5} | "
            f"{c['holdout_subjects']:<6} | "
            f"{c['holdout_effective_n_observations']:<6.1f} | "
            f"{c['total_sd_mm']:<8.2f} | "
            f"+/-{c['mean_error_ci_95_half_width_mm']:<5.2f} | "
            f"{c['non_inferiority_power']*100:>6.1f}%"
        )

    print("\n[SECTION 3: STUDENT'S t CRITICAL VALUE DILATION AUDIT]")
    print("Cluster df | t_crit (two-tailed 0.05) | z_crit (normal 0.05) | Dilation Factor")
    print("-" * 80)
    for df in [2, 3, 5, 7, 10, 14, 20, 30]:
        t_val = IndependentStatisticalOracle.student_t_critical_value(df, alpha_two_tailed=0.05)
        z_val = 1.95996
        dilation = t_val / z_val
        print(f"{df:<10} | {t_val:<25.3f} | {z_val:<20.3f} | +{(dilation - 1.0)*100:.1f}%")

    print("\n" + "=" * 80)
    print("REPRODUCTION COMPLETE: Zero external network or clinical data access required.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
