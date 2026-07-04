---
name: protocol-orchestrator
description: Orchestrates multi-pass extraction of experimental preparation protocols from paper markdown into protocol JSON. Invoke when building, checking, or revising material-preparation workflows from literature.
---

# Protocol Orchestrator

This skill extracts a preparation protocol from scientific paper markdown into a final JSON protocol.

The workflow is designed for tasks where a single prompt is not reliable enough. Use staged extraction, evidence grounding, and explicit self-checking before finalizing the JSON.

## Goal

Produce one final protocol JSON consistent with the project shot format and grounded in the source paper.

The final output must prioritize:

1. Source consistency
2. Chronological continuity
3. Explicit parameter grounding
4. Controlled operation typing
5. Minimal hallucination

## Required Working Style

- Work from overall structure to local details.
- Do not jump directly from full paper text to final JSON.
- First identify the protocol frame, then step skeleton, then step details.
- Treat missing information as `not reported` in reasoning; never invent values.
- Prefer a conservative omission over an unsupported completion.
- When a field is uncertain, re-read the source evidence before deciding.

## Canonical References

Before extracting, read these files in the same skill directory:

- `references/output-contract.md`
- `references/operation-types.md`

The current workspace canonical shot is in skil directory：

- `references/ODMA_GelMA_RSF_CHI_protocol.json`

Use this shot as a granularity and structure reference only, not as content to copy.

## Execution Artifacts And Paths

For each markdown input, create one run directory:

- `dataset/output/protocol_orchestrator/<markdown_stem>/`

Use the following fixed artifact names inside that directory:

1. `00_scope.json`
2. `01_evidence_segments.json`
3. `02_protocol_skeleton.json`
4. `03_protocol_details.json`
5. `04_validation_report.json`
6. `05_final_protocol.json`

Additional optional artifacts may be stored beside them when useful:

- `00_notes.md`
- `01_evidence_quotes.md`
- `stage_prompt.txt`
- `stage_raw_response.txt`

The final protocol may then be copied or saved to the project final target location only after validation passes. The canonical finalized artifact for the skill run itself is still `05_final_protocol.json`.

## Execution Workflow

### Phase 0: Scope The Task

Determine whether the target text is actually a preparation protocol.

Identify:

- target material or construct
- main preparation section
- whether protocol evidence is concentrated or scattered
- whether the paper includes repeated cycles, branching, or nested sub-protocols

If the text is not primarily about preparation, state that clearly and extract only the preparation-relevant portion.

Inputs:

- source markdown

Output file:

- `dataset/output/protocol_orchestrator/<markdown_stem>/00_scope.json`

Required contents:

- `paper_file`
- `protocol_relevance`
- `target_material_or_construct`
- `main_preparation_sections`
- `evidence_distribution`
- `branching_or_cycles`
- `scope_notes`

### Phase 1: Build An Evidence Set

Extract verbatim evidence segments related to preparation only.

Include evidence for:

- materials and reagents
- quantities, concentrations, pH, temperature, time
- containers and directly used instruments
- action verbs
- intermediate products
- repeated or cyclic operations
- washing / drying / curing / immersion / post-treatment

Exclude evidence that is only about:

- characterization
- biological assays
- performance evaluation
- discussion
- references

unless it adds a missing preparation fact that is explicitly stated there.

Inputs:

- source markdown
- `00_scope.json`

Output file:

- `dataset/output/protocol_orchestrator/<markdown_stem>/01_evidence_segments.json`

Required contents:

- `paper_file`
- `selected_segments`

Each segment must contain:

- `segment_id`
- `section_hint`
- `why_selected`
- `verbatim_text`

### Phase 2: Build A Protocol Skeleton

Construct a draft protocol frame before filling details.

At this stage produce:

- protocol name
- ordered step list
- for each step: `step_name`, `Type`, `Product`

Do not try to fully populate parameters yet.

Check:

- Does each step produce something needed later?
- Is the order chronologically valid?
- Are repeated steps represented explicitly or with a justified loop statement?

Inputs:

- `01_evidence_segments.json`
- `references/output-contract.md`
- `references/operation-types.md`
- `references/ODMA_GelMA_RSF_CHI_protocol.json`

Output file:

- `dataset/output/protocol_orchestrator/<markdown_stem>/02_protocol_skeleton.json`

Required contents:

- `Protocol`
- `Operations`

Each operation skeleton must contain:

- `step_id`
- `step_name`
- `Type`
- `Product`
- `evidence_refs`

At this stage, `Type` must already use the exact controlled strings from `references/operation-types.md`.

### Phase 3: Fill Step Details

Populate each step with:

- `Object`
- `Container`
- `Description`
- `Instrument parameters`
- `Product`

Rules:

- Every object must be supported by evidence.
- Every parameter must be attached to the correct step.
- Containers and instruments must be directly stated or strongly unavoidable from explicit wording.
- If the paper states a process but not the value, keep the process and omit the unsupported value.

Inputs:

- `01_evidence_segments.json`
- `02_protocol_skeleton.json`
- `references/output-contract.md`
- `references/operation-types.md`

Output file:

- `dataset/output/protocol_orchestrator/<markdown_stem>/03_protocol_details.json`

Required contents:

- `Protocol`
- `Materials`
- `Instruments`
- `Containers`
- `Operations`

Each final-draft operation must contain exactly the shot-style fields:

- `Type`
- `Object`
- `Container`
- `Description`
- `Instrument parameters`
- `Product`

### Phase 4: Continuity Audit

Perform a full internal audit before finalizing.

Check all of the following:

1. Every `Product` is either final or consumed later.
2. No step consumes an undefined intermediate.
3. No operation type falls outside the controlled list in `references/operation-types.md`.
4. No parameter appears without an anchor in the evidence.
5. No characterization-only device is included in `Instruments`.
6. The final JSON follows the required shot-style top-level structure.

If any check fails, revise the draft instead of returning it as-is.

Inputs:

- `01_evidence_segments.json`
- `03_protocol_details.json`
- `references/output-contract.md`
- `references/operation-types.md`

Output file:

- `dataset/output/protocol_orchestrator/<markdown_stem>/04_validation_report.json`

The validation report must contain:

- `status` with value `pass` or `fail`
- `checked_files`
- `top_level_shape`
- `operation_type_validation`
- `continuity_validation`
- `evidence_anchor_validation`
- `equipment_scope_validation`
- `naming_consistency_validation`
- `issues`
- `revision_actions`

Validation requirements:

1. Top-level keys must match `references/output-contract.md`.
2. Every operation `Type` must match one exact lowercase value from `references/operation-types.md`.
3. Combined actions such as washing-plus-drying must be split when the source treats them as sequential procedural steps.
4. Every later-used intermediate must have a defined origin.
5. Every explicit parameter must be traceable to at least one evidence segment.
6. Instruments and containers must stay inside preparation scope.
7. If `status` is `fail`, go back to Phase 2 or Phase 3, revise the draft artifacts, and regenerate `04_validation_report.json`.

### Phase 5: Finalize JSON

Return one final JSON only after the continuity audit passes.

The final JSON must be concise, mechanically readable, and consistent in naming across all steps.

Inputs:

- `03_protocol_details.json`
- `04_validation_report.json` with `status = pass`

Output file:

- `dataset/output/protocol_orchestrator/<markdown_stem>/05_final_protocol.json`

Finalization rules:

- `05_final_protocol.json` must be a clean final copy of the validated protocol.
- Do not finalize from memory alone; finalize from the validated draft artifact.
- Do not skip `04_validation_report.json`.
- If validation failed, no final JSON should be emitted for that run.

## Naming Rules

- Use concise English names.
- Keep the same intermediate name across all later references.
- Do not rename an intermediate product unless the paper clearly indicates a new state or product.
- Protocol names should describe the main material system and end with `_protocol`.

## Operation Typing Rules

- Use only the controlled operation list from `references/operation-types.md`.
- Choose the narrowest valid type.
- Do not invent a new type because the wording in the paper is unusual.
- If a step contains multiple actions, split the step unless the paper clearly treats them as a single inseparable operation.
- Use the exact lowercase spelling from `references/operation-types.md`; do not change case, spacing, or hyphenation.

## What To Avoid

- Do not collapse a multi-step protocol into one large summary step unless the source itself is only that coarse.
- Do not import materials, containers, or devices from the shot example.
- Do not infer missing concentrations, volumes, temperatures, or times.
- Do not silently merge distinct intermediates.
- Do not include analysis or assay procedures as preparation operations unless they directly prepare the final material.

## Preferred Output Discipline

Think in this order:

1. evidence
2. skeleton
3. details
4. audit
5. final JSON

If needed, keep intermediate reasoning artifacts outside the final answer, but do not skip the audit stage.

## Execution Order Summary

When this skill is invoked, follow this file flow:

1. read markdown and write `00_scope.json`
2. extract evidence and write `01_evidence_segments.json`
3. build ordered skeleton and write `02_protocol_skeleton.json`
4. fill full protocol draft and write `03_protocol_details.json`
5. validate against `references/output-contract.md` and `references/operation-types.md`, then write `04_validation_report.json`
6. only if validation passes, write `05_final_protocol.json`
