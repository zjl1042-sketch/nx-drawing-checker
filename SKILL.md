---
name: nx-drawing-checker
description: Review mechanical part drawings before NX modeling and check through openings, internal cavities, and editable feature history after modeling. Use for engineering drawings intended for NX or when a user reports mistaken cavities or material removal; exclude unrelated images and general 3D artwork.
---

# Drawing evidence and NX verification

Use this skill with the available NX modeling skill for actual NX operations. Resolve the skill directory to the project root; consult [README.md](README.md) for installation and commands. The bundled `.venv/bin/nx-drawing-checker` is available in this installation. Do not assume an NX version, machine path, coordinate system, or units for a new part.

## Reading the drawing

Inspect the original drawing at native resolution and separate the views. For DOCX inputs use the document-reading skill for text, then this project's `extract` command to retain original embedded image bytes. Use `crop` for pixel-preserving view crops. Enlargement does not restore missing lines or numbers.

For each critical feature record material versus void, through versus blind versus cavity, dimensions, and concrete observations in at least two views. Distinguish section hatching, visible outlines, hidden lines, and centerlines. An isometric opening alone cannot establish its depth. Never label an unhatched external view as a formal section just to pass validation.

Use `depth_basis` to identify the actual support for void depth: section, hidden_lines, callout, or user_confirmation. Only record a user confirmation that actually occurred. Conflicting or missing topology evidence requires clarification; dimensional estimates cannot resolve whether a space is hollow.

Mark each dimension stated or estimated, cite its view, and justify estimates. Account for datums and projection direction before interpreting dimension extension lines. Do not infer a numeric center position from apparent picture scale when a locating dimension exists.

[Case 2](cases/part-2.json) and [case 3](cases/part-3.json) illustrate the schema. Their coordinates and confirmed interpretations apply only to those samples. Define new cases for new parts. Run `review` before modeling, then inspect any claims that the checker cannot independently prove from pixels.

## Modeling and checking

Build real NX sketches and independent additive/subtractive features, with useful names, dimensions, and an editable history. Check operation limits: a subtractive extrusion starting too high can leave an unintended floor; an additive boss starting too high can fail to meet a curved shell. Confirm the complete profile and its connection to the interior.

Export a temporary STL and its history metadata using [nx/export_for_check.py](nx/export_for_check.py). Run `check-stl --history`. It checks the recorded sample locations and history requirements, not every surface or dimension. Feature counts alone cannot prove a complete operation sequence.

Render projections and appropriate sections with `preview`, compare them with the source views, and inspect the NX viewport and feature tree using the NX skill. For curved cavities, use clear-volume samples and wall-distance checks. For ports, place checks near both end caps and lateral edges as well as the center; sample paths must lie strictly inside the intended opening, away from tangent boundaries. Use retained-material checks to detect accidental removal of supports.

A passing report means the specified evidence and geometric checks passed. Report unresolved dimensions, ambiguous drawings, and unverified views plainly. When correcting a part, work on a separate staged result, reopen it, check model update errors and body count, then place the verified `.prt` in the user's requested destination. Preserve the requested NX history. Clear task-owned temporary images, meshes, staging parts and logs after retaining necessary Markdown results.

[nx/fix_part3_sample.py](nx/fix_part3_sample.py) is a guarded one-off correction for the original sample coordinates. It is not a general repair tool and refuses repeated or different inputs.
