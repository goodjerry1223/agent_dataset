---
name: lab-task-language
description: Generate and validate TaskDefinition XML for the human-robot co-scheduling laboratory project from a protocol-orchestrator final protocol JSON plus an external laboratory environment JSON/YAML configuration. Use when converting extracted material-preparation protocol JSON into the project's TaskDefinition XML with environment-defined operation primitives, containers, device declarations, human fallbacks, and static validation.
---

# Lab Task Language

## Scope

Use this skill to convert a final protocol JSON produced by
`protocol-orchestrator` into a valid `TaskDefinition` XML file for the
human-robot co-scheduling laboratory project.

The protocol JSON is the only scientific source of truth. Do not read the
paper markdown, protocol-orchestrator intermediate artifacts, or external
domain knowledge to add missing experimental facts. The laboratory environment
configuration may only constrain execution choices: available devices,
containers, solvents/reagents, initial state, supported operation primitives,
operation mappings, required/optional primitive parameters, and expected
durations.

After generating XML, validate it with the bundled static validator before
returning it.

## Workflow

1. Read `references/protocol-json-input.md` to understand the required
   protocol JSON contract and how `Stages`, `Operations`, and `relationship`
   map to XML.
2. Read `references/lab-environment-config.md`. Load the user-supplied JSON or
   YAML environment file from its external path. If the user does not provide
   one, ask for it unless they explicitly want a bundled example.
3. Read `references/task-definition.md` for XML structure and control-flow
   nodes.
4. Read `references/device-and-container-rules.md` when assigning device
   aliases, containers, or object movement.
5. Build a conversion plan from the protocol JSON only:
   - stage order and dependencies from `Stages` and `relationship`
   - operation order from `Operations`
   - materials, instruments, and containers from the final protocol JSON
   - operation primitive choices from `environment.operation_primitives`
   - primitive parameter meanings from `parameters.*.description`, `type`, and
     `unit`
   - automatable/manual decision from `operation_type_mapping`
6. Draft XML with declared devices, containers, operation primitives, and a
   `Procedure`.
7. Validate the XML with `scripts/validate_task_xml.py --env-config <env>`.
   Fix every error. Warnings are acceptable only when intentionally documented
   in the response.
8. Return the XML path or XML content, the environment file used, and a short
    validation summary including which protocol operations became
    `HumanOperation`.

## Generation Rules

- Accept input as a final protocol JSON file, normally `dataset/<Protocol>.json`.
- Do not use markdown-derived facts unless they already appear in the final
  protocol JSON.
- Preserve the protocol stage structure. Use one `Sequence` per stage. Use
  `OrderAny` only for stage groups listed in `relationship.parallel_groups`.
- Preserve serial dependencies mechanically from `Stages[].depends_on` and
  `relationship.serial_dependencies`; do not invent new parallelism.
- Prefer explicit, schedulable operation primitive steps over long prose.
- Use the environment config to decide whether an operation is available in the
  configured lab. If the lab does not support the needed operation, emit a
  `HumanOperation` instead of an automated primitive.
- Use `HumanOperation` for unsupported, ambiguous, safety-sensitive,
  under-specified, or intentionally manual work.
- Use `Option` with two or more `Alternative` children only when the
  environment explicitly allows both automated and human execution for that
  operation. If automation is unavailable, emit only `HumanOperation`.
- Use `OrderAny` or `Unordered` only for child workflows that can be independently scheduled.
- Use `Sequence` for strict step order.
- Declare every container id that appears in `target_object`, `source_object`, or `involved_objects`.
- Declare every device type that appears in a `device_assignment` or direct device field.
- Use `device_assignment` aliases to keep a repeated device choice consistent inside a block, for example `_stirrer:magnetic_stirrer`.
- Include `estimated_time` on `HumanOperation` and on generated operation
  primitives when the user provides or implies a reliable duration.
- Do not invent operation primitives. If a required lab action has no matching
  primitive in the environment config, express it as `HumanOperation`.
- Do not guess primitive parameter semantics from the parameter name alone. Use
  the environment config's `operation_primitives.<name>.parameters` entries,
  especially `description`, `type`, `unit`, and `required`.
- Do not invent exact quantities, flow rates, durations, temperatures, speeds,
  wavelengths, or container types. If the protocol JSON says `not reported`,
  keep the execution step manual or use a conservative default duration from
  the environment only as scheduling metadata.
- If a protocol operation maps to several XML steps, keep them adjacent inside
  the stage sequence unless movement/open/close steps are required by the
  configured device rules.
- If a protocol operation has an explicit passive duration but no device action,
  use `Wait` only when the environment permits passive waiting; otherwise use
  `HumanOperation`.
- Keep generated ids stable, ASCII, and XML-safe. Prefer lowercase names derived
  from stages, products, and protocol operation indexes.
- In the final response, report a compact mapping table:
  `protocol operation index -> XML primitive/HumanOperation -> reason`.

## Environment Configuration

The user should provide a single external JSON or YAML file describing the lab.
It may live anywhere readable in the workspace or filesystem; it does not need
to be placed under `skills/lab-task-language/`. The skill must treat this file
as execution context, not as scientific evidence that can fill gaps in the
protocol.

Read `references/lab-environment-config.md` for the canonical schema. A bundled
example for the current GelMA/PRP paper is available only as a starter/sample:

```text
skills/lab-task-language/environments/yuan2024_gelma_prp_lab.yaml
```

## Validation Commands

Validate a generated task:

```bash
python skills/lab-task-language/scripts/validate_task_xml.py path/to/task.xml --env-config path/to/lab.yaml
```

Print a compact task summary:

```bash
python skills/lab-task-language/scripts/summarize_task_xml.py path/to/task.xml
```

## Reference Files

- `references/protocol-json-input.md`: protocol-orchestrator final JSON input
  contract and protocol-to-XML mapping rules.
- `references/lab-environment-config.md`: JSON/YAML environment schema and
  automation fallback rules.
- `references/task-definition.md`: XML structure, control-flow nodes, and task-level conventions.
- `references/device-and-container-rules.md`: device aliases, container identity, movement, and scope rules.
