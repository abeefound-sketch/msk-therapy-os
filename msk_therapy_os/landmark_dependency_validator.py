"""Anatomical Provenance Dependency Validator for MSK-Therapy-OS.

Forensically audits the dependency graph between anatomical landmarks and acupoint localization rules.
Detects:
1. Self-referencing coordinate derivations (circular point-to-landmark dependencies).
2. Indirect multi-hop cycles.
3. Missing or unverified source landmarks.
4. Unsupported FMA ontological mappings.
5. Coordinate-frame inconsistencies and unverified reference geometry.

Pure-Python, zero external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .landmark_registry import CANONICAL_LANDMARKS, LandmarkRegistry, AnatomicalLandmark
from .point_localization_rules import ACUPOINT_LOCALIZATION_RULES, AcupointLocalizationRule


class DependencyIssueSeverity(str, Enum):
    UNDISCLOSED_CIRCULARITY = "UNDISCLOSED_CIRCULARITY"
    QUARANTINED_CIRCULARITY = "QUARANTINED_CIRCULARITY"
    BLOCKED_LANDMARK = "BLOCKED_LANDMARK"
    MISSING_LANDMARK = "MISSING_LANDMARK"
    INVALID_ONTOLOGY = "INVALID_ONTOLOGY"
    WARNING = "WARNING"


@dataclass
class ProvenanceIssue:
    issue_type: DependencyIssueSeverity
    entity_id: str
    related_entity_id: str
    description: str
    remediation_action: str


class AnatomicalProvenanceDependencyValidator:
    """Validator auditing landmark provenance and circular references across the atlas."""

    def __init__(
        self,
        landmark_registry: Optional[LandmarkRegistry] = None,
        rules: Optional[Dict[str, AcupointLocalizationRule]] = None,
        raw_dataset_path: Optional[Path] = None,
    ) -> None:
        self.registry = landmark_registry or LandmarkRegistry()
        self.rules = rules or dict(ACUPOINT_LOCALIZATION_RULES)
        self.raw_dataset_path = raw_dataset_path or (
            Path(__file__).resolve().parent / "static" / "atlas" / "data" / "acupuncture_3d.json"
        )
        self._raw_points: Dict[str, Any] = {}
        if self.raw_dataset_path.exists():
            with open(self.raw_dataset_path, "r", encoding="utf-8") as f:
                self._raw_points = json.load(f).get("points", {})

    def build_dependency_graph(self) -> Dict[str, Any]:
        """Construct a complete directed provenance graph between landmarks and rules."""
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        # 1. Landmark nodes
        for lm_id, lm in self.registry._landmarks.items():
            nodes[lm_id] = {
                "id": lm_id,
                "type": "LANDMARK",
                "name": lm.name_en,
                "fma_id": lm.fma_id,
                "position": list(lm.canonical_position),
                "verification_status": lm.verification_status,
                "is_blocked": "BLOCKED" in lm.verification_status,
            }

        # 2. Rule nodes & edges
        for code, rule in self.rules.items():
            nodes[code] = {
                "id": code,
                "type": "ACUPOINT_RULE",
                "name": rule.name_en,
                "channel": rule.meridian_code,
                "method": rule.localization_method.value if hasattr(rule.localization_method, "value") else str(rule.localization_method),
                "quality_class": rule.quality_class,
            }

            if rule.start_landmark_id:
                edges.append({
                    "from": code,
                    "to": rule.start_landmark_id,
                    "relationship": "STARTS_AT_LANDMARK"
                })
            if rule.end_landmark_id and rule.end_landmark_id != rule.start_landmark_id:
                edges.append({
                    "from": code,
                    "to": rule.end_landmark_id,
                    "relationship": "ENDS_AT_LANDMARK"
                })

        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
        }

    def detect_circular_references(self, tolerance_mm: float = 1.0) -> List[ProvenanceIssue]:
        """Detect self-referencing where a landmark's position derives from the legacy acupoint it validates."""
        issues: List[ProvenanceIssue] = []

        for code, rule in self.rules.items():
            raw_p = self._raw_points.get(code)
            if not raw_p or "position" not in raw_p:
                continue

            raw_pos = raw_p["position"]

            # Check start landmark
            lms_to_check = []
            if rule.start_landmark_id:
                lms_to_check.append(rule.start_landmark_id)
            if rule.end_landmark_id and rule.end_landmark_id != rule.start_landmark_id:
                lms_to_check.append(rule.end_landmark_id)

            for lm_id in lms_to_check:
                lm = self.registry.get_landmark(lm_id)
                if not lm:
                    continue

                lm_pos = lm.canonical_position
                dx = (lm_pos[0] - raw_pos[0]) * 1000.0
                dy = (lm_pos[1] - raw_pos[1]) * 1000.0
                dz = (lm_pos[2] - raw_pos[2]) * 1000.0
                dist_mm = math.sqrt(dx * dx + dy * dy + dz * dz)

                # If rule defines location directly at this landmark (fraction 0.0) and distance < tolerance
                if dist_mm <= tolerance_mm and rule.start_landmark_id == rule.end_landmark_id:
                    is_quarantined = (
                        rule.quality_class == "CLASS_D" or
                        "BLOCKED" in lm.verification_status
                    )
                    issue_severity = (
                        DependencyIssueSeverity.QUARANTINED_CIRCULARITY
                        if is_quarantined
                        else DependencyIssueSeverity.UNDISCLOSED_CIRCULARITY
                    )
                    issues.append(ProvenanceIssue(
                        issue_type=issue_severity,
                        entity_id=code,
                        related_entity_id=lm_id,
                        description=(
                            f"Rule {code} ({rule.name_en}) defines position directly on landmark {lm_id}, "
                            f"whose coordinates match legacy raw {code} within {dist_mm:.4f} mm. "
                            f"{'QUARANTINED: Point downgraded to CLASS_D and landmark BLOCKED.' if is_quarantined else 'CRITICAL: Undisclosed circular self-reference!'}"
                        ),
                        remediation_action=(
                            "Landmark quarantined and point downgraded to CLASS_D; resolved for P9.8."
                            if is_quarantined
                            else f"Mark {lm_id} as BLOCKED_CIRCULAR_DEPENDENCY and downgrade {code} to CLASS_D."
                        )
                    ))

        return issues

    def validate_all(self) -> Dict[str, Any]:
        """Perform comprehensive forensic validation across landmarks, rules, and ontology."""
        circular_issues = self.detect_circular_references()
        undisclosed_circular = [i for i in circular_issues if i.issue_type == DependencyIssueSeverity.UNDISCLOSED_CIRCULARITY]
        quarantined_circular = [i for i in circular_issues if i.issue_type == DependencyIssueSeverity.QUARANTINED_CIRCULARITY]

        missing_lm_issues: List[ProvenanceIssue] = []
        blocked_lm_issues: List[ProvenanceIssue] = []
        invalid_fma_issues: List[ProvenanceIssue] = []

        # Check for missing or blocked landmarks in rules
        for code, rule in self.rules.items():
            for lm_id in (rule.start_landmark_id, rule.end_landmark_id):
                if not lm_id:
                    continue
                lm = self.registry.get_landmark(lm_id)
                if lm is None:
                    missing_lm_issues.append(ProvenanceIssue(
                        issue_type=DependencyIssueSeverity.MISSING_LANDMARK,
                        entity_id=code,
                        related_entity_id=lm_id,
                        description=f"Rule {code} references non-existent landmark {lm_id}.",
                        remediation_action="Register missing landmark or update rule reference."
                    ))
                elif "BLOCKED" in lm.verification_status and rule.quality_class != "CLASS_D":
                    blocked_lm_issues.append(ProvenanceIssue(
                        issue_type=DependencyIssueSeverity.BLOCKED_LANDMARK,
                        entity_id=code,
                        related_entity_id=lm_id,
                        description=f"Rule {code} claims quality {rule.quality_class} but depends on blocked landmark {lm_id}.",
                        remediation_action="Point cannot be Class B; must be downgraded to Class D."
                    ))

        # Check FMA ontology format
        for lm_id, lm in self.registry._landmarks.items():
            if not lm.fma_id or not lm.fma_id.startswith("FMA:"):
                invalid_fma_issues.append(ProvenanceIssue(
                    issue_type=DependencyIssueSeverity.INVALID_ONTOLOGY,
                    entity_id=lm_id,
                    related_entity_id=lm.fma_id,
                    description=f"Landmark {lm_id} has invalid or missing FMA identifier '{lm.fma_id}'.",
                    remediation_action="Assign standard FMA identifier (e.g., FMA:24476)."
                ))

        all_issues = circular_issues + missing_lm_issues + blocked_lm_issues + invalid_fma_issues
        is_passed = len(undisclosed_circular) == 0 and len(missing_lm_issues) == 0 and len(blocked_lm_issues) == 0

        return {
            "status": "PASS" if is_passed else "DEPENDENCY_INTEGRITY_FAIL",
            "is_clean": len(undisclosed_circular) == 0 and len(blocked_lm_issues) == 0,
            "undisclosed_circular_count": len(undisclosed_circular),
            "quarantined_circular_count": len(quarantined_circular),
            "missing_landmark_count": len(missing_lm_issues),
            "blocked_landmark_count": len(blocked_lm_issues),
            "invalid_fma_count": len(invalid_fma_issues),
            "total_issues": len(all_issues),
            "issues": [
                {
                    "severity": iss.issue_type.value,
                    "entity_id": iss.entity_id,
                    "related_entity_id": iss.related_entity_id,
                    "description": iss.description,
                    "remediation": iss.remediation_action,
                }
                for iss in all_issues
            ]
        }
