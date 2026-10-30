"""MSK-Therapy-OS P10.4B Statistical Power & Sample Allocation Engine

Provides deterministic, reproducible calculations for sample size sizing, cluster design effects,
effective independent sample sizes, and holdout power evaluation across Cohorts A, B, and C.

Key Scientific Concepts:
1. Number of Patients (N): Unique human subjects.
2. Number of Studies: Radiological scan series (typically 1 per patient, occasionally multi-series).
3. Number of Landmarks: Distinct anatomical locations evaluated per patient.
4. Total Observations (M): N * Landmarks * Repeated measures.
5. Intraclass Correlation (ICC, rho): Non-zero correlation among points measured on the same individual.
6. Design Effect (DE): Inflation factor for variance due to intra-subject clustering:
   DE = 1 + (m - 1) * rho
7. Effective Independent Sample Size (N_eff): M / DE.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class CohortSampleSpec:
    cohort_id: str
    target_region: str
    num_subjects: int
    landmarks_per_subject: int
    intra_subject_icc: float  # rho
    calibration_ratio: float = 0.50
    tuning_ratio: float = 0.25
    holdout_ratio: float = 0.25

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculates exact sample accounting and effective sample sizes."""
        n_total = self.num_subjects
        m_landmarks = self.landmarks_per_subject
        total_obs = n_total * m_landmarks
        
        # Design effect
        de = 1.0 + (m_landmarks - 1) * self.intra_subject_icc
        n_eff_total = total_obs / de

        # Partition breakdown
        n_calib = int(round(n_total * self.calibration_ratio))
        n_tuning = int(round(n_total * self.tuning_ratio))
        n_holdout = n_total - n_calib - n_tuning

        obs_holdout = n_holdout * m_landmarks
        n_eff_holdout = obs_holdout / de

        return {
            "cohort_id": self.cohort_id,
            "target_region": self.target_region,
            "total_subjects": n_total,
            "landmarks_per_subject": m_landmarks,
            "total_observations": total_obs,
            "intra_subject_icc": self.intra_subject_icc,
            "design_effect": round(de, 3),
            "effective_independent_sample_total": round(n_eff_total, 1),
            "partitions": {
                "calibration": {"subjects": n_calib, "observations": n_calib * m_landmarks},
                "tuning": {"subjects": n_tuning, "observations": n_tuning * m_landmarks},
                "holdout": {
                    "subjects": n_holdout,
                    "observations": obs_holdout,
                    "effective_n": round(n_eff_holdout, 1),
                    "holdout_ratio_actual": round(n_holdout / n_total, 3),
                },
            },
        }


def evaluate_statistical_power(
    effect_size_delta: float,  # (threshold - expected_mean) in mm, e.g. (3.0 - 1.6) = 1.4 mm
    standard_deviation: float,  # e.g. 1.2 mm
    n_independent: float,
    alpha: float = 0.05,
) -> float:
    """Computes statistical power for one-sided non-inferiority z-test."""
    if n_independent <= 1:
        return 0.0
    se = standard_deviation / math.sqrt(n_independent)
    # Critical value z_alpha for one-sided 0.05 is ~1.645
    z_crit = 1.6448536269514722
    # Non-centrality parameter
    ncp = effect_size_delta / se
    z_beta = ncp - z_crit
    # Power = standard normal CDF(z_beta)
    power = 0.5 * (1.0 + math.erf(z_beta / math.sqrt(2.0)))
    return max(0.0, min(1.0, power))


class StatisticalProtocolEvaluator:
    """Evaluates protocol designs and compares alternative allocation strategies."""

    BASELINE_COHORTS = [
        CohortSampleSpec("COHORT_A_HEAD_NECK_CT", "Head & Neck", 30, 12, 0.35, 0.50, 0.25, 0.25),
        CohortSampleSpec("COHORT_B_KNEE_EXTREMITY_MRI", "Knee Extremity", 25, 10, 0.40, 0.50, 0.25, 0.25),
        CohortSampleSpec("COHORT_C_UPPER_LIMB_CT_MRI", "Upper Limb", 30, 13, 0.35, 0.50, 0.25, 0.25),
    ]

    ALTERNATIVE_EXPANDED_COHORTS = [
        CohortSampleSpec("COHORT_A_HEAD_NECK_CT", "Head & Neck", 40, 12, 0.35, 0.50, 0.20, 0.30),
        CohortSampleSpec("COHORT_B_KNEE_EXTREMITY_MRI", "Knee Extremity", 35, 10, 0.40, 0.50, 0.20, 0.30),
        CohortSampleSpec("COHORT_C_UPPER_LIMB_CT_MRI", "Upper Limb", 40, 13, 0.35, 0.50, 0.20, 0.30),
    ]

    @staticmethod
    def evaluate_protocol(cohort_specs: List[CohortSampleSpec]) -> Dict[str, Any]:
        """Calculates cohort-level and aggregate sample adequacy."""
        results = []
        total_n = 0
        total_obs = 0
        total_holdout_n = 0
        total_holdout_obs = 0
        total_eff_holdout = 0.0

        for spec in cohort_specs:
            m = spec.calculate_metrics()
            holdout_eff = m["partitions"]["holdout"]["effective_n"]
            # Power to detect non-inferiority (Mean <= 3.0mm when true mean is 1.6mm, SD=1.2mm)
            power_holdout = evaluate_statistical_power(
                effect_size_delta=1.4,
                standard_deviation=1.2,
                n_independent=holdout_eff,
                alpha=0.05
            )
            m["holdout_statistical_power"] = round(power_holdout, 4)
            # Precision of 95% CI on RMSE (half-width ~ 1.96 * SD / sqrt(2 * N_eff))
            ci_half_width = 1.96 * 1.2 / math.sqrt(2.0 * max(1.0, holdout_eff))
            m["holdout_rmse_ci_half_width_mm"] = round(ci_half_width, 3)

            results.append(m)
            total_n += m["total_subjects"]
            total_obs += m["total_observations"]
            total_holdout_n += m["partitions"]["holdout"]["subjects"]
            total_holdout_obs += m["partitions"]["holdout"]["observations"]
            total_eff_holdout += holdout_eff

        aggregate_power = evaluate_statistical_power(
            effect_size_delta=1.4, standard_deviation=1.2, n_independent=total_eff_holdout, alpha=0.05
        )

        return {
            "cohort_analyses": results,
            "aggregate": {
                "total_patients": total_n,
                "total_observations": total_obs,
                "total_holdout_patients": total_holdout_n,
                "total_holdout_observations": total_holdout_obs,
                "total_effective_holdout_n": round(total_eff_holdout, 1),
                "aggregate_holdout_power": round(aggregate_power, 4),
            },
        }
