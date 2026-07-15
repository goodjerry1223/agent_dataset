# Device and Container Rules

Use this file when declaring objects, choosing device aliases, or moving materials.

## Containers

- Declare every concrete object under `Synthesis/Container`.
- Treat container ids as task-local symbols, for example `well_plate_prod_1`, `reservoir_for_PMBAA`.
- Reuse a container id consistently across all operations.
- Do not use a reagent name as a container unless the reagent is represented by a reservoir container such as `reservoir_DI_Water`.

Common container types:

- `well_plate`
- `reservoir`
- `reservoir:DI_Water`
- `reservoir:CMC_Solution`
- `reservoir:PEDOT_Suspension`

## Devices

- Declare device types under `Synthesis/Device`.
- Device declarations are types, not necessarily concrete instances.
- Common device types include `plate_stack`, `robot_flex`, `robot_jaka`, `magnetic_stirrer`, `ultrasonic`, `AUBO_and_scale`, `vacuum_oven`.

## Device Aliases

Use `device_assignment` when a workflow needs a stable device choice:

```xml
<Sequence id="stir_PMBAA" device_assignment="_stirrer:magnetic_stirrer, stack_1:plate_stack">
```

Rules:

- Alias format: `alias:device_type`.
- Separate aliases with commas.
- Aliases are scoped to the node and descendants.
- Descendants inherit ancestor aliases.
- Siblings do not share aliases.
- Avoid redefining an alias in a child unless the protocol really needs shadowing.
- Use aliases such as `pipette_box_1:robot_flex`, `_stirrer:magnetic_stirrer`, `_scale:AUBO_and_scale`.

## Movement

Use `MoveToObject` before operations that require an object to be at a device:

```xml
<MoveToObject target_object="well_plate_prod_1" target_device="pipette_box_1" target_position="$internal_slot"/>
```

Common target positions:

- `$internal_slot`: an internal slot chosen by the device/environment.
- `$current_available_slot`: available storage slot, often on `plate_stack`.
- `$any`: any valid slot.
- Physical slots such as `A1`, `B2`, `D1`.

## HumanOperation

When a human takes an object away for a long manual operation, include affected objects and estimated time. If the manual work also depends on a device, include `involved_devices`.

```xml
<HumanOperation description="add stir bar to reservoir_for_PMBAA" involved_objects="reservoir_for_PMBAA" estimated_time="90"/>
```

Do not hide important resource occupancy in a vague description if it can be represented through `involved_objects` or `involved_devices`.
