#!/usr/bin/env python3
"""Static validator for first-version TaskDefinition XML files."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


CONTROL_TAGS = {"Procedure", "Sequence", "OrderAny", "Unordered", "Option", "Alternative"}

DEFAULT_METAOP_PARAMS: Dict[str, Set[str]] = {
    "MoveToObject": {"target_object", "target_device", "target_position", "device", "estimated_time", "id"},
    "MoveToReagent": {"reagent", "target_device", "target_position", "device", "estimated_time", "id"},
    "ContainerOpenCap": {"target_object", "target_device", "device", "estimated_time", "id"},
    "ContainerCloseCap": {"target_object", "target_device", "device", "estimated_time", "id"},
    "OpenCap": {"target_object", "target_device", "device", "estimated_time", "id"},
    "CloseCap": {"target_object", "target_device", "device", "estimated_time", "id"},
    "HydrogelSolidAdd": {"target_object", "reagent_name", "amount", "add_weight", "device", "estimated_time", "id"},
    "HydrogelLiquidAdd": {
        "source_object",
        "target_object",
        "target_index",
        "amount",
        "volume_list",
        "container_well_list",
        "reagent_name",
        "device",
        "estimated_time",
        "id",
    },
    "HydrogelLiquidAddBatch": {
        "source_object",
        "target_object",
        "target_index",
        "amount",
        "volume_list",
        "container_well_list",
        "reagent_name",
        "device",
        "estimated_time",
        "id",
    },
    "HydrogelStir": {"target_object", "time", "temperature", "speed", "device", "estimated_time", "id"},
    "HydrogelUltrasonic": {"target_object", "time", "device", "estimated_time", "id"},
    "HydrogelDryInOven": {"target_object", "temperature", "time", "device", "estimated_time", "id"},
    "Wait": {"time", "target_object", "estimated_time", "id"},
    "HumanWaitUntil": {"deadline", "estimated_time", "id"},
    "HumanOperation": {"description", "involved_objects", "involved_devices", "estimated_time", "id"},
}

DEFAULT_REQUIRED_PARAMS: Dict[str, Set[str]] = {
    "MoveToObject": {"target_object", "target_device"},
    "ContainerOpenCap": {"target_object"},
    "ContainerCloseCap": {"target_object"},
    "OpenCap": {"target_object"},
    "CloseCap": {"target_object"},
    "HydrogelSolidAdd": {"target_object", "reagent_name", "device"},
    "HydrogelLiquidAdd": {"source_object", "target_object", "device"},
    "HydrogelLiquidAddBatch": {"source_object", "target_object", "device"},
    "HydrogelStir": {"target_object", "time", "device"},
    "HydrogelUltrasonic": {"target_object", "time"},
    "HydrogelDryInOven": {"target_object", "temperature", "time"},
    "Wait": {"time"},
    "HumanWaitUntil": {"deadline"},
    "HumanOperation": {"description", "estimated_time"},
}

OBJECT_ATTRS = {"target_object", "source_object", "target_container_name", "target_container"}
DEVICE_ATTRS = {"target_device", "device"}
LIST_PAIR_OPS = {"HydrogelLiquidAdd", "HydrogelLiquidAddBatch"}


@dataclass
class ValidationResult:
    errors: List[str]
    warnings: List[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _load_data(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml  # type: ignore
        except Exception as exc:
            raise RuntimeError("YAML environment files require PyYAML to be installed.") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Environment config must contain a top-level object.")
    return data


def _primitive_catalog_from_env(path: Optional[Path]) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """Return allowed and required parameter sets.

    Without an environment config, use the legacy built-in catalog so existing
    benchmark TaskDefinition files can still be checked.
    """
    if path is None:
        return dict(DEFAULT_METAOP_PARAMS), dict(DEFAULT_REQUIRED_PARAMS)

    data = _load_data(path)
    primitives = data.get("operation_primitives")
    if not isinstance(primitives, dict):
        raise ValueError("Environment config must define operation_primitives when passed to the validator.")

    allowed: Dict[str, Set[str]] = {}
    required: Dict[str, Set[str]] = {}
    for primitive_name, spec in primitives.items():
        if not isinstance(primitive_name, str) or not primitive_name:
            raise ValueError("operation_primitives keys must be non-empty strings.")
        if spec is None:
            spec = {}
        if not isinstance(spec, dict):
            raise ValueError(f"operation_primitives.{primitive_name} must be an object.")

        req = set(spec.get("required_parameters") or spec.get("required") or [])
        opt = set(spec.get("optional_parameters") or spec.get("optional") or [])
        params = spec.get("parameters")
        if isinstance(params, dict):
            for param_name, param_spec in params.items():
                if not isinstance(param_name, str):
                    continue
                if not isinstance(param_spec, dict):
                    raise ValueError(f"operation_primitives.{primitive_name}.parameters.{param_name} must be an object.")
                if "required" not in param_spec:
                    raise ValueError(
                        f"operation_primitives.{primitive_name}.parameters.{param_name} is missing required flag."
                    )
                if not param_spec.get("description"):
                    raise ValueError(
                        f"operation_primitives.{primitive_name}.parameters.{param_name} is missing description."
                    )
                if not param_spec.get("type"):
                    raise ValueError(
                        f"operation_primitives.{primitive_name}.parameters.{param_name} is missing type."
                    )
                if param_spec.get("required"):
                    req.add(param_name)
                else:
                    opt.add(param_name)

        req = {item for item in req if isinstance(item, str) and item}
        opt = {item for item in opt if isinstance(item, str) and item}
        allowed[primitive_name] = req | opt | {"id"}
        required[primitive_name] = req

    if "HumanOperation" not in allowed:
        allowed["HumanOperation"] = DEFAULT_METAOP_PARAMS["HumanOperation"]
        required["HumanOperation"] = DEFAULT_REQUIRED_PARAMS["HumanOperation"]
    return allowed, required


def _child(parent: ET.Element, tag: str) -> Optional[ET.Element]:
    return parent.find(tag)


def _children(parent: Optional[ET.Element], tag: str) -> List[ET.Element]:
    if parent is None:
        return []
    return list(parent.findall(tag))


def _split_csv(value: str) -> List[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_device_assignment(value: str) -> List[Tuple[str, str]]:
    pairs = []
    for part in _split_csv(value):
        if ":" not in part:
            pairs.append((part, ""))
            continue
        alias, device_type = part.split(":", 1)
        pairs.append((alias.strip(), device_type.strip()))
    return pairs


def _parse_literal_list(value: str) -> Optional[List[object]]:
    try:
        parsed = ast.literal_eval(value)
    except Exception:
        return None
    if isinstance(parsed, list):
        return parsed
    return None


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except Exception:
        return False


def _walk_procedure(elem: ET.Element, inherited_aliases: Dict[str, str]) -> Iterable[Tuple[ET.Element, Dict[str, str]]]:
    aliases = dict(inherited_aliases)
    assignment = elem.attrib.get("device_assignment")
    if assignment:
        for alias, device_type in _parse_device_assignment(assignment):
            if alias:
                aliases[alias] = device_type
    yield elem, aliases
    for child in list(elem):
        yield from _walk_procedure(child, aliases)


def _declared_devices(synthesis: ET.Element) -> Set[str]:
    device_section = _child(synthesis, "Device")
    return {node.attrib.get("type", "").strip() for node in _children(device_section, "Device") if node.attrib.get("type")}


def _declared_containers(synthesis: ET.Element) -> Set[str]:
    container_section = _child(synthesis, "Container")
    return {
        node.attrib.get("id", "").strip()
        for node in _children(container_section, "Container")
        if node.attrib.get("id")
    }


def _declared_metaops(synthesis: ET.Element) -> Set[str]:
    metaop_section = _child(synthesis, "MetaOperation")
    return {
        node.attrib.get("type", "").strip()
        for node in _children(metaop_section, "MetaOperation")
        if node.attrib.get("type")
    }


def _validate_top_level(root: ET.Element, errors: List[str], warnings: List[str]) -> Optional[ET.Element]:
    if root.tag != "Task":
        errors.append(f"Root tag must be Task, found {root.tag!r}.")
        return None
    if not root.attrib.get("name"):
        warnings.append("Task is missing a name attribute.")
    if not root.attrib.get("version"):
        warnings.append("Task is missing a version attribute.")

    metadata = _child(root, "MetaData")
    if metadata is None:
        warnings.append("Task is missing MetaData.")
    elif _child(metadata, "StartDateTime") is None:
        warnings.append("MetaData is missing StartDateTime.")

    synthesis = _child(root, "Synthesis")
    if synthesis is None:
        errors.append("Task is missing Synthesis.")
        return None

    for tag in ("Device", "Container", "MetaOperation", "Procedure"):
        if _child(synthesis, tag) is None:
            errors.append(f"Synthesis is missing {tag}.")
    return synthesis


def _validate_leaf(
    elem: ET.Element,
    aliases: Dict[str, str],
    containers: Set[str],
    devices: Set[str],
    declared_metaops: Set[str],
    metaop_params: Dict[str, Set[str]],
    required_params: Dict[str, Set[str]],
    errors: List[str],
    warnings: List[str],
) -> None:
    tag = elem.tag
    path_id = elem.attrib.get("id", "")
    label = f"{tag}{f'#{path_id}' if path_id else ''}"

    if tag not in metaop_params:
        errors.append(f"Unsupported MetaOP/control tag {tag!r}.")
        return

    if tag not in declared_metaops:
        warnings.append(f"{label} is used in Procedure but not declared under Synthesis/MetaOperation.")

    allowed = metaop_params[tag]
    for attr in elem.attrib:
        if attr not in allowed:
            warnings.append(f"{label} has non-catalog parameter {attr!r}.")

    for required in required_params.get(tag, set()):
        if not elem.attrib.get(required):
            errors.append(f"{label} is missing required parameter {required!r}.")

    if tag == "HydrogelSolidAdd" and not (elem.attrib.get("amount") or elem.attrib.get("add_weight")):
        errors.append(f"{label} must include amount or add_weight.")

    if tag in LIST_PAIR_OPS:
        volume_list = elem.attrib.get("volume_list")
        well_list = elem.attrib.get("container_well_list")
        if volume_list or well_list:
            if not volume_list or not well_list:
                errors.append(f"{label} must include both volume_list and container_well_list.")
            else:
                volumes = _parse_literal_list(volume_list)
                wells = _parse_literal_list(well_list)
                if volumes is None:
                    errors.append(f"{label} volume_list is not a Python/JSON-like list.")
                if wells is None:
                    errors.append(f"{label} container_well_list is not a Python/JSON-like list.")
                if volumes is not None and wells is not None and len(volumes) != len(wells):
                    errors.append(f"{label} volume_list and container_well_list lengths differ.")
        elif not elem.attrib.get("amount"):
            warnings.append(f"{label} has no amount or volume_list.")

    for attr in OBJECT_ATTRS:
        value = elem.attrib.get(attr)
        if value and value not in containers:
            errors.append(f"{label} references undeclared container/object {value!r} in {attr}.")

    involved_objects = elem.attrib.get("involved_objects")
    if involved_objects:
        for obj in _split_csv(involved_objects):
            if obj not in containers:
                errors.append(f"{label} references undeclared involved object {obj!r}.")

    known_devices = devices | set(aliases)
    for attr in DEVICE_ATTRS:
        value = elem.attrib.get(attr)
        if value and value not in known_devices:
            errors.append(f"{label} references undeclared device or alias {value!r} in {attr}.")

    involved_devices = elem.attrib.get("involved_devices")
    if involved_devices:
        for device in _split_csv(involved_devices):
            if device not in known_devices:
                errors.append(f"{label} references undeclared involved device or alias {device!r}.")

    for time_attr in ("estimated_time", "time"):
        value = elem.attrib.get(time_attr)
        if value and not _is_number(value):
            warnings.append(f"{label} has non-numeric {time_attr}={value!r}.")


def validate(path: Path, env_config: Optional[Path] = None) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    try:
        metaop_params, required_params = _primitive_catalog_from_env(env_config)
    except Exception as exc:
        return ValidationResult([f"Cannot read environment config: {exc}"], [])

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return ValidationResult([f"XML parse error: {exc}"], [])
    except OSError as exc:
        return ValidationResult([f"Cannot read file: {exc}"], [])

    root = tree.getroot()
    synthesis = _validate_top_level(root, errors, warnings)
    if synthesis is None:
        return ValidationResult(errors, warnings)

    devices = _declared_devices(synthesis)
    containers = _declared_containers(synthesis)
    declared_metaops = _declared_metaops(synthesis)
    procedure = _child(synthesis, "Procedure")

    if not devices:
        warnings.append("No devices declared.")
    if not containers:
        warnings.append("No containers declared.")
    if not declared_metaops:
        warnings.append("No MetaOperations declared.")
    for metaop in declared_metaops:
        if metaop not in metaop_params:
            warnings.append(f"Declared MetaOperation {metaop!r} is not in the active primitive catalog.")

    if procedure is None:
        return ValidationResult(errors, warnings)

    for elem, aliases in _walk_procedure(procedure, {}):
        if elem is procedure:
            continue
        if elem.tag in CONTROL_TAGS:
            if elem.tag == "Option":
                alternatives = [child for child in list(elem) if child.tag == "Alternative"]
                if len(alternatives) < 2:
                    errors.append("Option must contain at least two Alternative children.")
            if elem.tag == "Alternative" and not list(elem):
                errors.append("Alternative must contain at least one child operation or control node.")
            assignment = elem.attrib.get("device_assignment")
            if assignment:
                for alias, device_type in _parse_device_assignment(assignment):
                    if not alias or not device_type:
                        errors.append(f"{elem.tag} has invalid device_assignment entry {assignment!r}.")
                    elif device_type not in devices:
                        errors.append(
                            f"{elem.tag} assigns alias {alias!r} to undeclared device type {device_type!r}."
                        )
            continue
        _validate_leaf(
            elem,
            aliases,
            containers,
            devices,
            declared_metaops,
            metaop_params,
            required_params,
            errors,
            warnings,
        )

    return ValidationResult(errors, warnings)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TaskDefinition XML for lab-task-language v1.")
    parser.add_argument("xml_file", type=Path)
    parser.add_argument("--env-config", type=Path, help="Optional JSON/YAML lab environment with operation_primitives.")
    parser.add_argument("--quiet", action="store_true", help="Print only errors and final status.")
    args = parser.parse_args(argv)

    result = validate(args.xml_file, args.env_config)

    if result.errors:
        print("ERRORS:")
        for error in result.errors:
            print(f"- {error}")
    if result.warnings and not args.quiet:
        print("WARNINGS:")
        for warning in result.warnings:
            print(f"- {warning}")

    if result.ok:
        print(f"OK: {args.xml_file} passed static validation with {len(result.warnings)} warning(s).")
        return 0

    print(f"FAILED: {args.xml_file} has {len(result.errors)} error(s) and {len(result.warnings)} warning(s).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
