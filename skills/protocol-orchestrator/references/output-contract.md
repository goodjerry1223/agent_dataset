## Output Contract

The target output is a protocol JSON in the same general style as the workspace shot example:

- `Status`
- `Reason`
- `Source`
- `Protocol`
- `Materials`
- `Instruments`
- `Containers`
- `Operations`

These top-level keys are mandatory for the final protocol artifact.

`Status` must be one of:

- `complete_protocol_found`
- `partial_protocol_found`
- `no_protocol_found`

`Reason` must briefly explain why the paper can or cannot support a complete preparation workflow.

`Source` must identify the source files used:

```json
{
  "pdf_file": "string or empty string",
  "markdown_file": "string",
  "conversion_status": "converted | skipped | failed"
}
```

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

1. `00_conversion.json`
2. `01_scope.json`
3. `02_evidence_segments.json`
4. `03_protocol_skeleton.json`
5. `04_protocol_details.json`
6. `05_validation_report.json`
7. `06_final_protocol.json`

## Minimal Operation Schema

Each operation should eventually contain:

- `Type`
- `Object`
- `Container`
- `Description`
- `Instrument parameters`
- `Product`

No operation should use free-form field names outside this schema in the final protocol JSON.

## Diagnostic Output Policy

If the source does not contain a complete preparation workflow, still produce a protocol JSON with the mandatory top-level keys.

For `partial_protocol_found`:

- Fill `Materials`, `Instruments`, `Containers`, and `Operations` only with explicitly supported preparation details.
- Use `Reason` to explain which required details are missing.
- Add a top-level `Missing information` list.
- Do not complete the workflow from general chemistry knowledge or from the shot example.

For `no_protocol_found`:

- Set `Materials`, `Instruments`, `Containers`, and `Operations` to empty lists.
- Set `Protocol` to a concise diagnostic name ending with `_protocol`, such as `<paper_stem>_no_preparation_protocol`.
- Use `Reason` to explain why no preparation workflow can be extracted.
- Add a top-level `Missing information` list with the unavailable categories.

Allowed diagnostic top-level key:

- `Missing information`

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
   - `Status`
   - `Reason`
   - `Source`
   - `Protocol`
   - `Materials`
   - `Instruments`
   - `Containers`
   - `Operations`
   - optional `Missing information` only when `Status` is `partial_protocol_found` or `no_protocol_found`
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
9. if `Status` is not `complete_protocol_found`, `Reason` and `Missing information` must explain why a complete workflow is unavailable

The validation result should be written to `05_validation_report.json` before finalizing `06_final_protocol.json`.

## Shot Usage Policy

Current canonical shot file:

- `references/ODMA_GelMA_RSF_CHI_protocol.json`

The shot example is for:

- top-level shape
- naming style
- preferred granularity target

The shot example is **not** for:

- copying materials
- copying instruments
- copying containers
- copying operation content
