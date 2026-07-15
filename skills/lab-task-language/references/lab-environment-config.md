# Lab Environment Config

Use this reference when a user provides a JSON or YAML lab environment file.
The file describes execution capability for TaskDefinition generation. It is
not evidence for missing protocol chemistry.

## File Format

JSON and YAML are both accepted. Prefer YAML for hand-authored configs.

Recommended top-level keys:

```yaml
name: example_lab
version: 1
start_datetime: "2025-11-04T09:00:00"

devices: []
agents: []
objects: []
reagent_sources: []
operation_primitives: {}
operation_type_mapping: {}
duration_defaults: {}
generation_policy: {}
```

Do not require user-authored environment files to live inside this skill. The
user may pass any readable path, for example:

```text
/path/to/my_lab.yaml
configs/labs/demo_lab.json
```

The `skills/lab-task-language/environments/` folder is only for bundled examples.
Do not edit the skill directory when a user only wants to run the same protocol
against a different lab.

## Devices

Declare devices available to the scheduler:

```yaml
devices:
  - id: flex
    type: robot_flex
    aliases: [pipette_box_1]
  - id: stirrer_01
    type: magnetic_stirrer
    aliases: [_stirrer]
```

Rules:

- `type` values must match TaskDefinition device types such as `robot_flex`,
  `robot_jaka`, `magnetic_stirrer`, `ultrasonic`, `AUBO_and_scale`,
  `vacuum_oven`, or `plate_stack`.
- Use `aliases` to guide XML `device_assignment`; aliases must be XML-safe.
- If two devices share a type, use different aliases in stage sequences.

## Agents

Declare agents if relevant:

```yaml
agents:
  - human
  - flex
```

`human` should normally be present because unsupported protocol operations fall
back to `HumanOperation`.

## Objects

Objects describe initial scheduler state:

```yaml
objects:
  - id: empty_reservoir_1
    type: reservoir
    location: {device: plate_stack, slot: C1}
    meta: {cap_state: closed}
```

Rules:

- `id` becomes a candidate XML container id.
- `type` becomes the XML `Container/@type`.
- `location` and `meta` document the initial state; the XML validator does not
  read them, but the generator should use them for object selection.

## Reagent Sources

Use `reagent_sources` to connect protocol reagent names to concrete source
containers:

```yaml
reagent_sources:
  - reagent: PBS
    aliases: [phosphate buffered saline, phosphate buffer saline]
    object_id: reservoir_PBS
    container_type: reservoir:PBS
    physical_state: liquid
```

Rules:

- Match reagent names case-insensitively against `Materials[]`,
  `Operations[].Object`, and `Operations[].Description`.
- If no matching reagent source exists, do not generate automated liquid or
  solid additions for that reagent.
- Source containers must be declared in `objects` or generated under
  `Synthesis/Container`.

## Operation Primitives

`operation_primitives` is the active operation catalog for the user's lab. It
replaces the older fixed MetaOP catalog. Each primitive should define what it
does, who or what can execute it, and which XML attributes are required or
optional. New configs should use the `parameters` mapping form because each
parameter carries its own meaning, type, and unit constraints.

```yaml
operation_primitives:
  HydrogelLiquidAdd:
    description: Add one liquid reagent from a source container to a target container.
    executors: [robot_flex, human]
    default_device_alias: pipette_box_1
    parameters:
      source_object:
        required: true
        type: container_id
        description: Declared source container id that holds the liquid reagent.
      target_object:
        required: true
        type: container_id
        description: Declared destination container id receiving the liquid.
      device:
        required: true
        type: device_alias_or_type
        description: Device alias or type that performs the liquid transfer.
      amount:
        required: false
        type: number
        unit: microliter
        description: Single transfer volume in microliters when reported.
      volume_list:
        required: false
        type: list[number]
        unit: microliter
        description: List of per-well or per-position volumes in microliters.
      container_well_list:
        required: false
        type: list[string]
        description: List of target wells or positions matching volume_list.
      reagent_name:
        required: false
        type: string
        description: Human-readable reagent name copied from protocol evidence.
      estimated_time:
        required: false
        type: seconds
        description: Scheduling estimate in seconds, not a scientific condition.
  HydrogelStir:
    description: Stir a target container for a reported duration.
    executors: [magnetic_stirrer]
    default_device_alias: _stirrer
    parameters:
      target_object:
        required: true
        type: container_id
        description: Declared container id to stir.
      time:
        required: true
        type: seconds
        description: Stirring duration in seconds from the protocol JSON.
      device:
        required: true
        type: device_alias_or_type
        description: Stirrer alias or device type.
      temperature:
        required: false
        type: number
        unit: celsius
        description: Stirring temperature in degrees Celsius when reported.
      speed:
        required: false
        type: number
        unit: rpm
        description: Stirring speed in rpm when reported.
      estimated_time:
        required: false
        type: seconds
        description: Scheduling estimate in seconds.
  HumanOperation:
    description: Manual fallback operation.
    executors: [human]
    parameters:
      description:
        required: true
        type: string
        description: Manual instruction preserving the protocol operation intent.
      estimated_time:
        required: true
        type: seconds
        description: Scheduling estimate in seconds.
      involved_objects:
        required: false
        type: csv[container_id]
        description: Comma-separated declared container ids occupied by the manual step.
      involved_devices:
        required: false
        type: csv[device_alias_or_type]
        description: Comma-separated declared device aliases or types occupied by the manual step.
```

Rules:

- Generate only primitives listed under `operation_primitives`, except that
  `HumanOperation` may be injected by the validator as a compatibility fallback.
- If a primitive is absent from `operation_primitives`, treat it as unavailable
  for this lab.
- `HumanOperation` should normally be declared because unsupported protocol
  operations must not be dropped.
- `description` is recommended for every primitive. It helps the generator pick
  the right primitive without relying on a fixed built-in catalog.
- `parameters` defines the XML attributes allowed for that primitive. Each
  parameter must include `required: true|false`, `type`, and a concise
  `description`. Include `unit` when values are numeric physical quantities.
- `required_parameters` and `optional_parameters` list forms are accepted for
  backward compatibility, but they omit parameter semantics and should not be
  used for new configs.
- `default_device_alias` must resolve to a declared device alias or type when
  the primitive uses a device.
- A lab may use completely different primitive names from another lab, as long
  as the XML declares the same names under `Synthesis/MetaOperation`.

## Operation Type Mapping

Map protocol operation types to operation primitive choices:

```yaml
operation_type_mapping:
  mixing:
    preferred: [HydrogelLiquidAdd, HydrogelStir]
    fallback: HumanOperation
    allow_option: true
  centrifugation:
    preferred: []
    fallback: HumanOperation
    allow_option: false
```

Fields:

- `preferred`: ordered operation primitive candidates from
  `operation_primitives`.
- `fallback`: normally `HumanOperation`.
- `allow_option`: if true, emit a human/automated `Option` when both branches
  are valid.
- `requires_reported_container`: if true, do not automate when the protocol
  operation container is `not reported`.
- `requires_reported_duration`: if true, do not automate when a duration cannot
  be extracted from `Instrument parameters` or `Description`.

## Duration Defaults

Use `duration_defaults` only for scheduling estimates:

```yaml
duration_defaults:
  HumanOperation:
    default: 300
  protocol_types:
    filtration: 600
    centrifugation: 1800
```

Rules:

- These values may populate `estimated_time`.
- They must not be copied into scientific parameters such as centrifuge time,
  UV exposure time, dialysis duration, or incubation duration unless the same
  value appears in the protocol JSON.

## Generation Policy

```yaml
generation_policy:
  unsupported_operation: HumanOperation
  missing_required_automation_fact: HumanOperation
  include_human_alternative_for_automated_steps: false
  synthesize_missing_containers_for_manual_steps: true
  declare_only_used_devices: true
```

Policy meanings:

- `unsupported_operation`: must be `HumanOperation`.
- `missing_required_automation_fact`: must be `HumanOperation`.
- `include_human_alternative_for_automated_steps`: when true, generated
  automated steps may be wrapped in `Option`.
- `synthesize_missing_containers_for_manual_steps`: allows task-local synthetic
  containers for scheduler bookkeeping when the protocol says the container is
  `not reported`.
- `declare_only_used_devices`: declare only devices referenced by generated XML
  and `device_assignment`.

## Required Fallback Behavior

If a protocol operation cannot be executed by the configured lab, the generated
XML must contain a `HumanOperation` for that protocol operation. Do not silently
drop the operation.

The `HumanOperation/@description` must include enough of the protocol operation
description to preserve the experimental intent.
