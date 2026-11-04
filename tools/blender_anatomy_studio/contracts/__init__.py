"""Schema contracts and validator helpers for Blender Anatomical Studio & Motion Pipelines.
Uses jsonschema if available; otherwise falls back to standard library validation.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

CONTRACTS_DIR = Path(__file__).resolve().parent

SCHEMAS = {
    "anatomy_asset_manifest": CONTRACTS_DIR / "anatomy_asset_manifest.schema.json",
    "annotation": CONTRACTS_DIR / "annotation.schema.json",
    "joint_constraint": CONTRACTS_DIR / "joint_constraint.schema.json",
    "motion_sequence": CONTRACTS_DIR / "motion_sequence.schema.json",
    "pose_observation": CONTRACTS_DIR / "pose_observation.schema.json",
    "validation_report": CONTRACTS_DIR / "validation_report.schema.json",
}

def load_schema(name: str) -> Dict[str, Any]:
    if name not in SCHEMAS:
        raise KeyError(f"Unknown contract schema: {name}. Available: {list(SCHEMAS.keys())}")
    schema_path = SCHEMAS[name]
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _stdlib_validate(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """Lightweight recursive schema validator using only standard library."""
    req = schema.get("required", [])
    for field in req:
        if field not in data:
            return False, f"Missing required property: '{field}'"

    props = schema.get("properties", {})
    for k, v in data.items():
        if k in props:
            p_def = props[k]
            expected_type = p_def.get("type")
            if isinstance(expected_type, list):
                if v is None and "null" in expected_type:
                    continue
                type_map = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}
                valid = any(isinstance(v, type_map[t]) for t in expected_type if t != "null")
                if not valid:
                    return False, f"Property '{k}' expected one of types {expected_type}, got {type(v).__name__}"
            elif expected_type == "string":
                if not isinstance(v, str):
                    return False, f"Property '{k}' expected string, got {type(v).__name__}"
                if "pattern" in p_def and not re.match(p_def["pattern"], v):
                    return False, f"Property '{k}' value '{v}' does not match pattern {p_def['pattern']}"
                if "enum" in p_def and v not in p_def["enum"]:
                    return False, f"Property '{k}' value '{v}' not in enum {p_def['enum']}"
            elif expected_type == "number":
                if not isinstance(v, (int, float)):
                    return False, f"Property '{k}' expected number, got {type(v).__name__}"
            elif expected_type == "integer":
                if not isinstance(v, int):
                    return False, f"Property '{k}' expected integer, got {type(v).__name__}"
            elif expected_type == "array":
                if not isinstance(v, list):
                    return False, f"Property '{k}' expected array, got {type(v).__name__}"
                if "minItems" in p_def and len(v) < p_def["minItems"]:
                    return False, f"Property '{k}' array has fewer items than minItems ({len(v)} < {p_def['minItems']})"
            elif expected_type == "object":
                if not isinstance(v, dict):
                    return False, f"Property '{k}' expected object, got {type(v).__name__}"

    return True, ""

def validate_contract(data: Dict[str, Any], schema_name: str) -> Tuple[bool, str]:
    schema = load_schema(schema_name)
    if HAS_JSONSCHEMA:
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True, ""
        except jsonschema.ValidationError as e:
            return False, f"Validation error at path '{list(e.path)}': {e.message}"
        except Exception as e:
            return False, str(e)
    else:
        return _stdlib_validate(data, schema)
