## Output Contract

The target output is a final protocol JSON in the same general style as the
workspace shot example.

The final artifact must contain exactly these top-level keys:

- `Protocol`
- `Stages`
- `Materials`
- `Instruments`
- `Containers`
- `Operations`
- `relationship`

Optional top-level key:

- `Missing information`



## Extraction Strategy

Build the JSON from overall structure to local detail.

Recommended internal order:

1. Determine protocol identity and target construct.
2. Determine the major preparation stages.
3. Determine dependencies and parallelizable stage groups.
4. Determine ordered operations inside each stage.
5. Assign one controlled `Type` per operation.
6. Fill intermediates, materials, containers, instruments, and parameters.
7. Audit against the source paper before finalizing.

Recommended artifact sequence for one skill run:

1. `01_scope.json`
2. `02_evidence_segments.json`
3. `03_protocol_skeleton.json`
4. `04_protocol_details.json`
5. `05_validation_report.json`
6. `dataset/<Protocol>.json`

The final output file must be written to `dataset/<Protocol>.json`, where the
file stem exactly matches the final `Protocol` field.

## Stage Schema

`Stages` is mandatory in the final protocol JSON. Each stage must contain:

- `stage_name`
- `order`
- `summary`
- `depends_on`

Use `Stages` to represent the large preparation phases required for downstream
TaskDefinition or workflow-code generation.

`Stages[].depends_on` is the single source of truth for stage dependency and
must use stage names directly.

Example:

```json
["PRP Preparation", "GelMA Synthesis"]
```

Downstream code should derive serial and parallel relations from this field
rather than treating multiple dependency fields as independent facts.

## Minimal Operation Schema

Each operation in the final protocol JSON must contain exactly:

- `Type`
- `Object`
- `Container`
- `Description`
- `Instrument parameters`
- `Product`
- `belongto`

`belongto` must reference one existing `Stages[].stage_name`.

No operation should use free-form field names outside this schema in the final
protocol JSON.

## Relationship Schema

`relationship` is mandatory in the final protocol JSON and must summarize
dependencies between major stages.

Use this structure:

```json
{
  "serial_dependencies": [
    {"from": "PRP Preparation", "to": "Precursor Preparation"}
  ],
  "parallel_groups": [
    ["PRP Preparation", "GelMA Synthesis"]
  ]
}
```

Rules:

- every `from` and `to` value must reference an existing `stage_name`
- `serial_dependencies` must be mechanically derived from `Stages[].depends_on`
- `parallel_groups` must only include stages with no unresolved dependency
  conflict
- `relationship` is a derived export view, not an additional reasoning target

## Diagnostic Output Policy

If the source does not contain a complete preparation workflow, still produce a
protocol JSON with the mandatory top-level keys.

The diagnostic classification itself belongs in `01_scope.json` and
`05_validation_report.json`, not as extra top-level fields in the final JSON.

For `partial_protocol_found`:

- fill `Stages`, `Materials`, `Instruments`, `Containers`, and `Operations`
  only with explicitly supported preparation details
- add a top-level `Missing information` list that explains which required
  details are unavailable
- do not complete the workflow from general chemistry knowledge or from the shot
  example

For `no_protocol_found`:

- set `Stages`, `Materials`, `Instruments`, `Containers`, and `Operations` to
  empty lists
- set `relationship` to empty lists for both serial and parallel relations
- set `Protocol` to a concise diagnostic name ending with `_Protocol`, such as
  `<paper_stem>_No_Preparation_Protocol`
- add a top-level `Missing information` list with the unavailable categories

## Controlled Detail Policy

- `Materials`: only explicitly reported materials, reagents, solvents,
  additives, initiators, cells, or intermediates directly used in preparation
- `Instruments`: only instruments directly used for preparation, not
  characterization-only equipment
- `Containers`: only containers directly used for preparation or holding when
  part of the preparation flow
- `Instrument parameters`: use a mapping from instrument or container to a list
  of explicit conditions

## Missing Information Policy

When information is not explicitly reported:

- do not fabricate it
- do not import it from the shot
- omit unsupported values from the final JSON

Use conservative descriptions rather than speculative completions.

## Continuity Rules

Before finalizing, confirm:

- every stage has a valid source-evidence basis
- every operation belongs to one valid stage
- every intermediate has a valid origin
- every later step refers to an existing material or intermediate
- every repeated cycle is represented consistently
- no step order contradicts the source
- stage dependency statements do not contradict the source

## Evidence Reference Rules

Whenever an intermediate artifact uses `evidence_refs`, it must use this form:

```json
["segment_001", "segment_002"]
```

Rules:

- each item must be one `segment_id` from `02_evidence_segments.json`
- do not use free-form quotes or prose inside `evidence_refs`
- if a quote excerpt is needed, store it in a separate field such as
  `evidence_quote`

## Validation Rules

Before accepting the final protocol:

1. top-level keys must be exactly:
   - `Protocol`
   - `Stages`
   - `Materials`
   - `Instruments`
   - `Containers`
   - `Operations`
   - `relationship`
   - optional `Missing information`
2. every stage must contain:
   - `stage_name`
   - `order`
   - `summary`
   - `depends_on`
3. every operation must contain exactly:
   - `Type`
   - `Object`
   - `Container`
   - `Description`
   - `Instrument parameters`
   - `Product`
   - `belongto`
4. every `Operations[].Type` must match one exact controlled string from
   `references/operation-types.md`
5. operation type matching is case-sensitive and hyphen-sensitive
6. unsupported combined labels such as `wash and dry` must be split into
   separate operations when they represent sequential steps
7. every later-consumed intermediate must have an earlier origin inside
   `Operations`
8. every explicit condition in `Instrument parameters` must be anchored in
   evidence
9. characterization-only equipment must not appear in `Instruments`
10. every `Operations[].belongto` must reference one existing
    `Stages[].stage_name`
11. `relationship` must be mechanically consistent with `Stages[].depends_on`
12. if `01_scope.json` classifies the paper as not
    `complete_protocol_found`, the final JSON must include
    `Missing information` explaining why the workflow is incomplete or absent

The validation result should be written to `05_validation_report.json` before
finalizing `dataset/<Protocol>.json`.

## Validation Report Schema

The validation report should prioritize one pass over the final operations,
with one evidence anchor per operation or a recorded failure if no anchor can be
found.

Required top-level keys:

- `status` with value `pass` or `fail`
- `checked_files`
- `operation_checks`
- `missing_operations`
- `revision_actions`

Each item in `operation_checks` must contain:

- `operation_index`
- `operation_product`
- `belongto`
- `evidence_refs`
- `evidence_quote`
- `validation_result` with value `pass` or `fail`
- `issues`

Each item in `issues` must contain:

- `issue_type`
- `details`

Allowed `issue_type` values:

- `missing_evidence`
- `order_error`
- `parameter_error`
- `type_error`
- `stage_ref_error`

## Shot Usage Policy

Current canonical shot files:

- `references/ODMA_GelMA_RSF_CHI_protocol.json`
- `references/PRP_GelMA_Microsphere_Composite_Protocol.json`

The shot examples are for:

- top-level shape
- naming style
- preferred granularity target
- stage and dependency expression style

The shot example is **not** for:

- copying materials
- copying instruments
- copying containers
- copying operation content
