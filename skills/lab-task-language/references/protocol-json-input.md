# Protocol JSON Input

Use this reference when converting a final `protocol-orchestrator` artifact into
TaskDefinition XML.

## Accepted Input

The input must be one final protocol JSON file, normally:

```text
dataset/<Protocol>.json
```

Do not read `markdown/` or `dataset/output/<markdown_stem>/` during this skill.
Those files may explain why the protocol JSON was produced, but they are not
allowed sources for TaskDefinition generation.

## Required Protocol Fields

Expected top-level keys:

- `Protocol`
- `Stages`
- `Materials`
- `Instruments`
- `Containers`
- `Operations`
- `relationship`
- optional `Missing information`

Each operation is expected to contain:

- `Type`
- `Object`
- `Container`
- `Description`
- `Instrument parameters`
- `Product`
- `belongto`

## Conversion Order

1. Use `Protocol` as the XML `Task/@name`, sanitized to an XML-safe identifier.
2. Create one XML `Sequence` per `Stages[]` item.
3. Place each `Operations[]` item into the sequence named by
   `Operations[].belongto`.
4. Preserve operation order within a stage as it appears in `Operations[]`.
5. Use `relationship.parallel_groups` to wrap independent stage sequences in
   `OrderAny`.
6. Use `Stages[].depends_on` and `relationship.serial_dependencies` to keep
   dependent stages after prerequisite stages.

## Operation Mapping

Map `Operations[].Type` through the active environment config:

- If an operation type has a configured automated mapping and all required
  device/container/reagent facts are available, emit the configured operation
  primitive.
- If the environment allows both automated and human execution, emit an
  `Option` with a human `Alternative` and an automated `Alternative`.
- If the operation type is unsupported by the environment, emit one
  `HumanOperation`.
- If required automation facts are missing from the protocol JSON, emit
  `HumanOperation` even if the environment has a capable device.

Always preserve the protocol operation's `Description` in either XML attributes
or XML comments close to the generated step. The description is the most
important fallback when the action cannot be represented as a narrow operation
primitive.

If no environment file is supplied, do not infer automation support. Ask for a
lab environment file or use a bundled example only when the user explicitly
selects it.

## Containers

Create declared XML containers from:

1. explicit `Containers[]`
2. non-`not reported` values in `Operations[].Container`
3. environment `objects` and `reagent_sources` needed by mapped operations
4. synthetic task-local containers for products or intermediates when the
   protocol operation needs a target object but the source says `not reported`

Synthetic container ids must be clearly marked by name, for example
`manual_container_op_003` or `intermediate_gelma_precursor_solution`. Synthetic
containers do not add experimental facts; they only give the scheduler a
resource to track.

## Materials and Reagent Sources

Use `Materials[]` and `Operations[].Object` for reagent names. Use environment
`reagent_sources` to choose concrete source containers such as
`reservoir_PBS` or `reservoir_DI_Water`.

If a reagent appears in the protocol but no environment source container exists,
do not invent a source container for automated liquid addition. Use
`HumanOperation` or an `Option` only if the environment explicitly permits a
manual branch.

## Missing Information

If the protocol JSON has `Missing information`, do not complete those gaps from
environment defaults. Environment durations may be used only as scheduler
estimates, not as scientific protocol conditions.

Examples:

- Missing UV wavelength/intensity: use `HumanOperation` unless the environment
  explicitly has a generic UV curing primitive that does not require those
  values.
- Missing centrifuge speed/time: use `HumanOperation` or a manual centrifuge
  step with estimated scheduling time.
- `Container` is `not reported`: use a synthetic task-local container only when
  needed for scheduler continuity, and keep the step manual if automation needs
  a precise container.

## Mapping Report

When returning results, include a compact mapping report with:

- protocol operation index
- protocol `Type`
- stage
- generated XML node type
- reason: automated, option, unsupported, missing facts, or manual by config
