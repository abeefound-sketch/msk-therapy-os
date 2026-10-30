"""MSK-Therapy-OS P10.5 Statistical Study Design & Precision Analysis Engine

Provides mathematically rigorous, reproducible sample-size, precision, and sensitivity
modeling for multi-center anatomical validation protocols across Cohorts A, B, and C.

Features:
- Distinguishes 5 sample metrics: Patients (N), Studies, Landmarks (m), Total Obs (M), Effective N (N_eff).
- Cluster Design Effect: DE = 1 + (m - 1) * rho_within + m * (n_site - 1) * rho_site.
- Sensitivity analysis across variable ICCs (rho in [0.20, 0.55]) and standard deviations (sigma in [1.0, 2.5] mm).
- Evaluates 3 distinct planning scenarios:
  1. MINIMUM_FEASIBILITY_PILOT (N=45)
  2. PRIMARY_ANATOMICAL_ACCURACY_STUDY (N=85)
  3. INDEPENDENT_MULTI_SITE_VALIDATION (N=150)
- Calculates holdout partition precision (95% CI half-width on mean and RMSE).
- Evaluates statistical power under one-sided non-inferiority margins (delta_0 = 3.0 mm).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class PlanningScenarioType(str, Enum):
    MINIMUM_FEASIBILITY_PILOT = "MINIMUM_FEASIBILITY_PILOT"
    PRIMARY_ANATOMICAL_ACCURACY_STUDY = "PRIMARY_ANATOMICAL_ACCURACY_STUDY"
    INDEPENDENT_MULTI_SITE_VALIDATION = "INDEPENDENT_MULTI_SITE_VALIDATION"


@dataclass
class CohortDesignSpec:
    cohort_id: str
    target_region: str
    num_subjects: int
    landmarks_per_subject: int
    within_subject_icc: float  # rho_within
    expected_mean_error_mm: float = 1.60
    assumed_sd_mm: float = 1.20
    non_inferiority_margin_mm: float = 3.00
    calibration_ratio: float = 0.50
    tuning_ratio: float = 0.25
    holdout_ratio: float = 0.25


@dataclass
class ScenarioEvaluationResult:
    scenario_type: PlanningScenarioType
    total_subjects: int
    total_observations: int
    total_holdout_subjects: int
    total_holdout_observations: int
    aggregate_holdout_effective_n: float
    aggregate_holdout_power: float
    cohort_details: List[Dict[str, Any]]
    biostatistical_recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["scenario_type"] = self.scenario_type.value
        return d


def compute_one_sided_z_power(
    effect_delta_mm: float,  # (margin - expected_mean)
    sigma_mm: float,
    effective_n: float,
    alpha: float = 0.05,
) -> float:
    """Computes statistical power for one-sided z-test of non-inferiority."""
    if effective_n <= 1.0 or sigma_mm <= 0.0 or effect_delta_mm <= 0.0:
        return 0.0
    se = sigma_mm / math.sqrt(effective_n)
    z_alpha = 1.6448536269514722  # z for 0.05 one-sided
    ncp = effect_delta_mm / se
    z_beta = ncp - z_alpha
    power = 0.5 * (1.0 + math.erf(z_beta / math.sqrt(2.0)))
    return max(0.0, min(1.0, power))


class StatisticalStudyDesignEngine:
    """Comprehensive design and sensitivity analysis engine for clinical research protocols."""

    @staticmethod
    def evaluate_cohort(
        spec: CohortDesignSpec,
        site_heterogeneity_icc: float = 0.05,
        subjects_per_site: int = 15,
    ) -> Dict[str, Any]:
        """Calculates cohort-specific effective sample size, precision, and power."""
        m_pts = spec.landmarks_per_subject
        n_subj = spec.num_subjects
        total_obs = n_subj * m_pts

        # Multi-level hierarchical design effect:
        # DE = 1 + (m - 1) * rho_within + m * (n_site - 1) * rho_site
        de_within = 1.0 + (m_pts - 1) * spec.within_subject_icc
        de_site = m_pts * max(0, subjects_per_site - 1) * site_heterogeneity_icc
        total_de = de_within + de_site

        n_eff_total = total_obs / total_de

        # Partitions
        n_calib = int(round(n_subj * spec.calibration_ratio))
        n_tuning = int(round(n_subj * spec.tuning_ratio))
        n_holdout = n_subj - n_calib - n_tuning

        obs_holdout = n_holdout * m_pts
        n_eff_holdout = obs_holdout / total_de

        # Power on holdout
        delta = spec.non_inferiority_margin_mm - spec.expected_mean_error_mm
        power = compute_one_sided_z_power(delta, spec.assumed_sd_mm, n_eff_holdout)

        # 95% CI half-width on mean error: 1.96 * SD / sqrt(N_eff)
        ci_half_width_mean = 1.96 * spec.assumed_sd_mm / math.sqrt(max(1.0, n_eff_holdout))

        # 95% CI half-width on RMSE (approximate): 1.96 * SD / sqrt(2 * N_eff)
        ci_half_width_rmse = 1.96 * spec.assumed_sd_mm / math.sqrt(2.0 * max(1.0, n_eff_holdout))

        return {
            "cohort_id": spec.cohort_id,
            "target_region": spec.target_region,
            "subjects": n_subj,
            "landmarks_per_subject": m_pts,
            "total_observations": total_obs,
            "within_subject_icc": spec.within_subject_icc,
            "design_effect": round(total_de, 3),
            "effective_n_total": round(n_eff_total, 1),
            "partitions": {
                "calibration_subjects": n_calib,
                "tuning_subjects": n_tuning,
                "holdout_subjects": n_holdout,
                "holdout_observations": obs_holdout,
                "holdout_effective_n": round(n_eff_holdout, 1),
            },
            "holdout_precision": {
                "mean_error_ci_95_half_width_mm": round(ci_half_width_mean, 3),
                "rmse_ci_95_half_width_mm": round(ci_half_width_rmse, 3),
            },
            "holdout_statistical_power": round(power, 4),
            "is_holdout_sufficient_for_subgroup_power": power >= 0.80,
        }

    @staticmethod
    def run_scenario(scenario_type: PlanningScenarioType) -> ScenarioEvaluationResult:
        """Executes one of the three standardized planning scenarios."""
        if scenario_type == PlanningScenarioType.MINIMUM_FEASIBILITY_PILOT:
            # N = 45 total (15 A, 15 B, 15 C)
            specs = [
                CohortDesignSpec("COHORT_A_ABDOMEN", "Abdominal Landmarks", 15, 12, 0.40, assumed_sd_mm=1.40),
                CohortDesignSpec("COHORT_B_EXTREMITIES", "Bilateral Extremities", 15, 10, 0.45, assumed_sd_mm=1.50),
                CohortDesignSpec("COHORT_C_CRANIOFACIAL", "Craniofacial Landmarks", 15, 12, 0.35, assumed_sd_mm=1.10),
            ]
            rec = "Adequate for software workflow rehearsal and feasibility testing; UNDERPOWERED for separate cohort-level regulatory equivalence."

        elif scenario_type == PlanningScenarioType.PRIMARY_ANATOMICAL_ACCURACY_STUDY:
            # N = 85 total (30 A, 25 B, 30 C)
            specs = [
                CohortDesignSpec("COHORT_A_ABDOMEN", "Abdominal Landmarks", 30, 12, 0.38, assumed_sd_mm=1.30),
                CohortDesignSpec("COHORT_B_EXTREMITIES", "Bilateral Extremities", 25, 10, 0.40, assumed_sd_mm=1.40),
                CohortDesignSpec("COHORT_C_CRANIOFACIAL", "Craniofacial Landmarks", 30, 13, 0.35, assumed_sd_mm=1.15),
            ]
            rec = "Highly powered (>99%) at aggregate whole-body level; Cohort B holdout borderline for strict subgroup non-inferiority."

        elif scenario_type == PlanningScenarioType.INDEPENDENT_MULTI_SITE_VALIDATION:
            # N = 150 total (50 A, 50 B, 50 C across >=3 hospital sites)
            specs = [
                CohortDesignSpec("COHORT_A_ABDOMEN", "Abdominal Landmarks", 50, 12, 0.38, assumed_sd_mm=1.35),
                CohortDesignSpec("COHORT_B_EXTREMITIES", "Bilateral Extremities", 50, 12, 0.40, assumed_sd_mm=1.40),
                CohortDesignSpec("COHORT_C_CRANIOFACIAL", "Craniofacial Landmarks", 50, 14, 0.35, assumed_sd_mm=1.15),
            ]
            rec = "Gold standard multi-center design; provides >95% holdout power for every individual cohort independently under multi-scanner variance."

        cohort_results = [StatisticalStudyDesignEngine.evaluate_cohort(s) for s in specs]
        total_subjs = sum(c["subjects"] for c in cohort_results)
        total_obs = sum(c["total_observations"] for c in cohort_results)
        total_hold_subjs = sum(c["partitions"]["holdout_subjects"] for c in cohort_results)
        total_hold_obs = sum(c["partitions"]["holdout_observations"] for c in cohort_results)
        agg_eff_hold = sum(c["partitions"]["holdout_effective_n"] for c in cohort_results)

        # Aggregate power across all cohorts pooled
        delta_agg = 3.0 - 1.6
        sd_agg = 1.30
        agg_power = compute_one_sided_z_power(delta_agg, sd_agg, agg_eff_hold)

        return ScenarioEvaluationResult(
            scenario_type=scenario_type,
            total_subjects=total_subjs,
            total_observations=total_obs,
            total_holdout_subjects=total_hold_subjs,
            total_holdout_observations=total_hold_obs,
            aggregate_holdout_effective_n=round(agg_eff_hold, 1),
            aggregate_holdout_power=round(agg_power, 4),
            cohort_details=cohort_results,
            biostatistical_recommendation=rec,
        )

    @staticmethod
    def run_sensitivity_grid(
        num_subjects: int = 30,
        landmarks: int = 12,
        icc_values: List[float] = [0.20, 0.35, 0.50],
        sd_values: List[float] = [1.0, 1.3, 1.6, 2.0],
    ) -> List[Dict[str, Any]]:
        """Generates a multi-parameter sensitivity grid for biostatistical review."""
        grid: List[Dict[str, Any]] = []
        for icc in icc_values:
            for sd in sd_values:
                spec = CohortDesignSpec(
                    cohort_id="SENSITIVITY", target_region="Test",
                    num_subjects=num_subjects, landmarks_per_subject=landmarks,
                    within_subject_icc=icc, assumed_sd_mm=sd
                )
                res = StatisticalStudyDesignEngine.evaluate_cohort(spec)
                grid.append({
                    "within_subject_icc": icc,
                    "assumed_sd_mm": sd,
                    "design_effect": res["design_effect"],
                    "holdout_effective_n": res["partitions"]["holdout_effective_n"],
                    "holdout_statistical_power": res["holdout_statistical_power"],
                    "mean_ci_half_width_mm": res["holdout_precision"]["mean_error_ci_95_half_width_mm"],
                })
        return grid
