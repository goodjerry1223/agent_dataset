## Output Contract

The target output is a protocol JSON in the same general style as the workspace shot example:

- `Protocol`
- `Materials`
- `Instruments`
- `Containers`
- `Operations`

These top-level keys are mandatory for the final protocol artifact.

## Extraction Strategy

Build the JSON from overall structure to local detail.

Recommended internal order:

1. Determine protocol identity and target construct.
2. Determine ordered operations.
3. Assign one controlled `Type` per operation.
4. Fill intermediates and products.
5. Fill materials, containers, instruments, and parameters.
6. Audit continuity and unsupported details.

Recommended artifact sequence for one skill run:

1. `00_scope.json`
2. `01_evidence_segments.json`
3. `02_protocol_skeleton.json`
4. `03_protocol_details.json`
5. `04_validation_report.json`
6. `05_final_protocol.json`

## Minimal Operation Schema

Each operation should eventually contain:

- `Type`
- `Object`
- `Container`
- `Description`
- `Instrument parameters`
- `Product`

No operation should use free-form field names outside this schema in the final protocol JSON.

## Controlled Detail Policy

- `Materials`: only explicitly reported materials, reagents, solvents, additives, initiators, cells, or intermediates directly used in preparation.
- `Instruments`: only instruments directly used for preparation, not characterization-only equipment.
- `Containers`: only containers directly used for preparation or culture/holding when part of the preparation flow.
- `Instrument parameters`: use a mapping from instrument or container to a list of explicit conditions.

## Missing Information Policy

When information is not explicitly reported:

- do not fabricate it
- do not import it from the shot
- omit unsupported values from the final JSON

Use conservative descriptions rather than speculative completions.

## Continuity Rules

Before finalizing, confirm:

- every intermediate has a valid origin
- every later step refers to an existing material or intermediate
- every repeated cycle is represented consistently
- no step order contradicts the source

## Validation Rules

Before accepting the final protocol:

1. top-level keys must be exactly:
   - `Protocol`
   - `Materials`
   - `Instruments`
   - `Containers`
   - `Operations`
2. every operation must contain exactly:
   - `Type`
   - `Object`
   - `Container`
   - `Description`
   - `Instrument parameters`
   - `Product`
3. every `Operations[].Type` must match one exact controlled string from `references/operation-types.md`
4. operation type matching is case-sensitive and hyphen-sensitive
5. unsupported combined labels such as `wash and dry` must be split into separate operations when they represent sequential steps
6. every later-consumed intermediate must have an earlier origin inside `Operations`
7. every explicit condition in `Instrument parameters` must be anchored in evidence
8. characterization-only equipment must not appear in `Instruments`

The validation result should be written to `04_validation_report.json` before finalizing `05_final_protocol.json`.

## Shot Usage Policy

Current canonical shot file:

- `e:\学习\agent for robotics\GELMA\.agents\skills\protocol-orchestrator\references\ODMA_GelMA_RSF_CHI_protocol.json`

The shot example is for:

- top-level shape
- naming style
- preferred granularity target

The shot example is **not** for:

- copying materials
- copying instruments
- copying containers
- copying operation content
