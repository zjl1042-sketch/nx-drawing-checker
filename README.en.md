# NX Drawing Checker

[简体中文](README.md) · [Reproducible demo](examples/README.md) · [Contributing](CONTRIBUTING.md)

Evidence-led review of mechanical drawings and sampled geometry checks for Siemens NX parts.
It targets two concrete mistakes: leaving a floor in an intended through opening, and
allowing external material to intrude into a smooth internal cavity.

The workflow is: extract original images → identify views → record feature evidence →
model in NX → validate selected geometry and editable feature history. A reusable
[Codex skill](SKILL.md) describes the workflow. The checker is a Python CLI; using it
does not require an OpenAI API key.

## Install and try without NX

Requires Python 3.10+ and Pillow. Clone this repository first, then:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/synthetic_demo.py
```

On Windows use `.venv\Scripts\Activate.ps1` in PowerShell. The demo creates synthetic
closed meshes, detects an obstruction, then verifies a clear variant. It needs no
private drawings, NX installation, or CAD license.

## Commands

- `extract`: preserve embedded DOCX image bytes and their document order.
- `crop`: crop named views at original pixel resolution.
- `review`: check recorded evidence, void extent, depth basis, and dimensions.
- `check-stl`: validate a closed STL and execute the selected line/point/surface checks.
- `preview`: render projections and section outlines for comparison.

```bash
nx-drawing-checker review cases/part-2.json --report review.md
```

The `cases/part-2.json` and `cases/part-3.json` files describe specific historical
models, not universal templates. Image-dependent commands require the original
local inputs. Reconfigure coordinates, units, evidence, and sampling for each part.
NX journals in `nx/` require Siemens NX on Windows. `export_for_check.py` exports
STL and matching history metadata without saving the input part. Supply the matching
`--history` file for cases that require editable feature history.

## Scope and evidence

The repository includes automated tests and [maintainer-recorded NX 2007 validation](VALIDATION.md).
The original private drawings and `.prt` models are not distributed. The public
synthetic demo is independently reproducible; it does not reproduce the private
NX session. The validation notes explicitly list incomplete checks.

This tool does not infer correct topology from arbitrary pixels, train a vision
model, certify manufacturing tolerances, or check every surface. Human-recorded
evidence must be correct; passing sampled checks proves only the stated checks.
STL previews are not native NX drawings. Siemens NX is a separate proprietary
product; this project is not affiliated with or endorsed by Siemens.

## Development and license

See [CONTRIBUTING.md](CONTRIBUTING.md) and [ROADMAP.md](ROADMAP.md).
The code is available under the [MIT License](LICENSE).
