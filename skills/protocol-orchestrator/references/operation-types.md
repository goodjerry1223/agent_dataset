## Controlled Operation Types v0.1

Use this controlled list for `Operations[].Type`.

The purpose is to reduce free-form variation and keep protocol extraction auditable.

Validation note:

- type strings must be used exactly as written below
- matching is case-sensitive
- keep lowercase spelling and original hyphenation
- do not replace a controlled type with a natural-language paraphrase

## The 25 Recommended Types

1. `synthesis`
2. `dissolution`
3. `mixing`
4. `dispersion`
5. `pH-adjustment`
6. `transfer`
7. `casting`
8. `molding`
9. `crosslinking`
10. `uv-irradiation`
11. `heating`
12. `cooling`
13. `incubation`
14. `immersion`
15. `washing`
16. `drying`
17. `lyophilization`
18. `dialysis`
19. `filtration`
20. `sterilization`
21. `centrifugation`
22. `sonication`
23. `emulsification`
24. `thawing`
25. `seeding`

## Mapping Guidance

### `synthesis`

Use for a reaction or formation step when the paper describes a new product being generated and no narrower type above is better.

### `dissolution`

Use when a material is dissolved into a solvent or buffer.

### `mixing`

Use when components are combined without a stronger process label such as crosslinking or dissolution.

### `dispersion`

Use when particles, fibers, nanosheets, or other dispersed phases are introduced into a matrix or solvent.

### `pH-adjustment`

Use only when the text explicitly states pH tuning or buffer-driven pH control as a step.

### `transfer`

Use when a prepared solution, suspension, or intermediate is moved into another container, mold, insert, or substrate.

### `casting`

Use for casting a liquid or precursor into a plate, dish, mold, or surface before later curing or drying.

### `molding`

Use when shape formation is explicitly mold-based rather than generic casting.

### `crosslinking`

Use when gelation or network formation is described but not specifically via UV wording in the type label.

### `uv-irradiation`

Use when UV exposure or photocuring is explicitly stated.

### `heating`

Use when heating is the main action of the step rather than just one condition inside another step.

### `cooling`

Use when cooling is the main action of the step rather than just a condition change.

### `incubation`

Use when the protocol requires holding material or cell-laden constructs under controlled time and temperature conditions.

### `immersion`

Use for soaking, dipping, placing into solution, or layer-by-layer surface treatment steps.

### `washing`

Use for rinse or wash steps.

### `drying`

Use for drying, air-drying, vacuum-drying, oven-drying, or unspecified drying.

### `lyophilization`

Use specifically for freeze-drying / lyophilization.

### `dialysis`

Use specifically for dialysis.

### `filtration`

Use specifically for filtration or membrane filtration.

### `sterilization`

Use when sterilization is explicitly part of sample preparation.

### `centrifugation`

Use when a sample is centrifuged to separate phases, pellet solids, clarify
supernatant, or concentrate a biological fraction.

### `sonication`

Use when ultrasound treatment is explicitly applied to disperse, exfoliate,
degas, or homogenize a material system.

### `emulsification`

Use when droplets or emulsions are intentionally generated, including
microfluidic droplet formation, shear-driven emulsification, or oil-water
emulsion preparation.

### `thawing`

Use when a frozen reagent, intermediate, or biological sample is intentionally
returned to a usable liquid or soft state before a later preparation step.

### `seeding`

Use when cells or other biological payloads are deliberately introduced onto or
into a prepared scaffold, hydrogel, membrane, or substrate as part of sample
preparation.

## Practical Rules

- Prefer `uv-irradiation` over generic `crosslinking` when UV is explicit.
- Prefer `immersion` over generic `synthesis` for RSF/CHI soaking-style steps.
- Prefer `drying` or `washing` as separate steps when the paper gives them explicit procedural status.
- Prefer `centrifugation` when the text explicitly uses centrifuge conditions
  such as `g`, `rpm`, or pellet/supernatant handling.
- Prefer `emulsification` over generic `dispersion` when the source explicitly
  describes droplet generation or emulsion formation.
- Prefer `thawing` when a frozen intermediate is deliberately brought back to a
  workable state before later use.
- If a step contains two sequential actions with distinct products, split it.
- If the paper states a repeated cycle such as `(RSF/CHI)n`, represent the cycle explicitly in description and keep the operation types constrained to the list above.
