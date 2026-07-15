---
name: protocol-orchestrator
description: Extracts experimental material-preparation workflows from paper markdown into protocol JSON. Invoke when building, checking, or revising material-preparation workflows from literature.
---

# Protocol Orchestrator

Extract one preparation workflow from one paper markdown into one final protocol
JSON.

## Goal

- stay grounded in the source markdown
- model large preparation stages before local operations
- capture stage dependencies, including parallel branches when supported
- keep unsupported values out of the final JSON
- finalize only after one explicit audit pass

## Read First

Always read these references before extracting:

- `references/output-contract.md`
- `references/operation-types.md`
- `references/ODMA_GelMA_RSF_CHI_protocol.json`
- `references/PRP_GelMA_Microsphere_Composite_Protocol.json`

Use the reference JSON files only for shape, granularity, and dependency style.
Do not copy their materials, instruments, containers, operations, or wording.

## Paths

- input markdown: `markdown/`
- intermediate artifacts: `dataset/output/<markdown_stem>/`
- final artifact: `dataset/<Protocol>.json`

Use these intermediate files:

1. `01_scope.json`
2. `02_evidence_segments.json`
3. `03_protocol_skeleton.json`
4. `04_protocol_details.json`
5. `05_validation_report.json`

## Working Rules

- Work in this order: scope -> evidence -> skeleton -> details -> audit -> final.
- Use markdown as the only source of truth.
- Never jump straight from full paper text to final JSON.
- Prefer conservative omission over unsupported completion.
- Treat missing information as `not reported`, not as something to infer.
- Downstream workflow generation should rely only on `dataset/<Protocol>.json`.

## Standard Format

The final protocol must follow `references/output-contract.md`.

`references/output-contract.md` is the only canonical source for final JSON
schema and validation rules. Do not add extra top-level keys that are not
defined there.

Important structure rules:

- `Stages[]` uses natural-language `stage_name`
- `Stages[].depends_on` must use stage names directly, for example
  `["PRP Preparation", "GelMA Synthesis"]`.
- `Operations[].belongto` must use one existing `stage_name`.
- `relationship.serial_dependencies[].from` and `.to` must use stage names.
- `relationship.parallel_groups` must contain stage-name arrays.
- `relationship` must be derived from `Stages[].depends_on`, not reasoned
  separately.

## Stage 1: Scope

Write `01_scope.json`.

Required keys:

- `paper_file`
- `protocol_relevance`
- `target_material_or_construct`
- `main_preparation_sections`
- `evidence_distribution`
- `branching_or_cycles`
- `reason_if_incomplete_or_absent`
- `missing_required_information`
- `scope_notes`

`protocol_relevance` must be one of:

- `complete_protocol_found`
- `partial_protocol_found`
- `no_protocol_found`

If the result is not `complete_protocol_found`, continue conservatively and
prepare a diagnostic final JSON using only the top-level keys allowed by
`references/output-contract.md`. Keep the diagnostic classification in
`01_scope.json` and `05_validation_report.json`.

## Stage 2: Evidence

Write `02_evidence_segments.json`.

Each selected segment must contain:

- `segment_id`
- `section_hint`
- `why_selected`
- `verbatim_text`

Include only preparation-relevant evidence:

- materials, reagents, additives, solvents
- quantities, concentrations, pH, time, temperature
- containers and directly used instruments
- action verbs and intermediate products
- repeated cycles, branching, serial dependency, parallel execution clues

Exclude characterization, assay, discussion, and performance sections unless
they explicitly provide missing preparation facts.

## Stage 3: Skeleton

Write `03_protocol_skeleton.json`.

Required top-level keys:

- `Protocol`
- `Stages`
- `Operations`
- `relationship`

Each stage skeleton must contain:

- `stage_name`
- `order`
- `summary`
- `depends_on`
- `evidence_refs`

Each operation skeleton must contain:

- `Type`
- `Product`
- `belongto`
- `evidence_refs`

Rules:

- `Type` must use one exact label from `references/operation-types.md`.
- `belongto` must reference one valid `stage_name`.
- `evidence_refs` must use `segment_id` values from `02_evidence_segments.json`.
- Build dependency structure at the stage level first, then place operations
  inside stages.

## Stage 4: Details

Write `04_protocol_details.json`.

Each final operation must contain exactly:

- `Type`
- `Object`
- `Container`
- `Description`
- `Instrument parameters`
- `Product`
- `belongto`

Rules:

- every object, parameter, and condition must be evidence-supported
- containers and instruments must be explicit in the source; otherwise omit them
- if a process is reported but a value is not, keep the process and omit the
  value
- keep `Stages`, `Operations[].belongto`, and `relationship` mutually
  consistent

## Stage 5: Audit

Write `05_validation_report.json`.

Required top-level keys:

- `status`
- `checked_files`
- `operation_checks`
- `missing_operations`
- `revision_actions`

For each operation, check:

- at least one evidence anchor exists
- operation order matches the source
- parameters match the source
- `Type` matches the controlled list exactly
- `belongto` points to one valid stage name
- `relationship` matches `Stages[].depends_on`

If audit fails, revise the skeleton or details and regenerate the audit report.

## Stage 6: Finalize

Write `dataset/<Protocol>.json` only after `05_validation_report.json` passes.

Rules:

- the filename stem must exactly match the final `Protocol` field
- finalize from the validated draft, not from memory
- do not emit a final JSON when audit fails

The final JSON should remain minimal and should not duplicate diagnostic fields
already captured in `01_scope.json` or `05_validation_report.json`.

## Dependency Guidance

Use stage dependencies only for large preparation phases, not for every single
operation.

Good serial example:

- `ODMA Synthesis` -> `Precursor Mixing` -> `Hydrogel Formation`

Good parallel example:

- `PRP Preparation` and `GelMA Synthesis` can run in parallel
- both must finish before `Precursor Preparation`

Parallel detection should come from source evidence such as:

- independent upstream preparation branches
- separate precursor or component preparation sections
- later merge steps that consume outputs from more than one earlier branch

Do not create a parallel group only because two stages look logically
independent. The paper must support that reading.

## What To Avoid

- do not copy content from the shot examples
- do not invent missing concentrations, times, temperatures, or ratios
- do not merge distinct intermediates without source support
- do not include characterization-only procedures as preparation steps
- do not replace controlled operation types with free-form paraphrases
