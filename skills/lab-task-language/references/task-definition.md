# TaskDefinition XML Reference

Use this file when constructing the XML skeleton and choosing control-flow nodes.

## Top-Level Shape

```xml
<Task name="Task_Name" version="0.3">
  <MetaData>
    <StartDateTime value="2025-11-04T09:00:00"/>
  </MetaData>
  <Synthesis>
    <Device>
      <Device type="robot_flex"/>
      <Device type="magnetic_stirrer"/>
    </Device>
    <Container>
      <Container id="reservoir_DI_Water" type="reservoir:DI_Water"/>
      <Container id="well_plate_prod_1" type="well_plate"/>
    </Container>
    <MetaOperation>
      <MetaOperation type="MoveToObject"/>
      <MetaOperation type="HydrogelLiquidAdd"/>
    </MetaOperation>
    <Procedure>
      ...control nodes and MetaOP leaves...
    </Procedure>
  </Synthesis>
</Task>
```

Required sections:

- `Task`: root element with `name` and `version`.
- `MetaData/StartDateTime`: initial task time as ISO-like string.
- `Synthesis/Device`: device type declarations.
- `Synthesis/Container`: container/object declarations.
- `Synthesis/MetaOperation`: MetaOP type declarations.
- `Synthesis/Procedure`: executable workflow tree.

## Control Nodes

`Sequence`: children must execute in order.

```xml
<Sequence id="prepare_solution">
  ...
</Sequence>
```

`OrderAny` or `Unordered`: children are independent and may be scheduled in any order or in parallel if resources allow.

```xml
<OrderAny id="parallel_batches">
  <Sequence id="batch_1">...</Sequence>
  <Sequence id="batch_2">...</Sequence>
</OrderAny>
```

`Option`: planner must choose one `Alternative`. Use for human-vs-robot choices or method choices.

```xml
<Option id="add_liquid_choice">
  <Alternative>
    <HumanOperation description="add liquid manually" involved_objects="plate_1" estimated_time="300"/>
  </Alternative>
  <Alternative>
    <HydrogelLiquidAdd source_object="reservoir" target_object="plate_1" amount="1000" device="pipette_box_1"/>
  </Alternative>
</Option>
```

`Alternative`: a branch inside `Option`. It may contain one leaf operation or a nested `Sequence`.

## Leaf Nodes

Leaf nodes are MetaOP elements such as `MoveToObject`, `HydrogelLiquidAdd`, or `HumanOperation`. Put parameters directly on attributes:

```xml
<HydrogelStir target_object="reservoir_for_PMBAA" time="1800" temperature="28" speed="350" device="_stirrer"/>
```

## Device Assignment

Any non-leaf control node can define `device_assignment`:

```xml
<Sequence id="stir_solution" device_assignment="_stirrer:magnetic_stirrer, stack_1:plate_stack">
```

The alias is visible to that node and its descendants. Sibling nodes cannot see each other's aliases. Prefer aliases when later operations must use the same physical device choice.

## Compatibility Notes

- Existing data often uses `OrderAny`; documentation may also call this `Unordered`.
- Existing data uses `MoveToObject`, not the older `MoveTo` spelling.
- Container ids are task-local symbols; they do not need to match environment object ids exactly.
- Device declarations are usually by type, while containers are concrete ids.
