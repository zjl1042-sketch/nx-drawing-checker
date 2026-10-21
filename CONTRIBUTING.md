# Contributing

Bug reports, reproducible cases, documentation corrections, and small fixes are welcome.
Open an [issue](https://github.com/zjl1042-sketch/nx-drawing-checker/issues) before a large change.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/synthetic_demo.py
```

On Windows, activate `.venv\Scripts\Activate.ps1` in PowerShell instead.

## Report a problem

Include your Python/OS version, tool command, expected and actual behavior,
and a minimal synthetic or shareable input. For NX export issues also include
NX version, units, journal error, and whether the part contains editable history.
Never upload private coursework, customer drawings, proprietary parts, or credentials.

## Pull requests

Explain the concrete problem and validation. Add a regression test for geometry or
evidence-validation changes. Keep source-image bytes intact; do not invent missing
view evidence, dimensions, user confirmations, or accuracy claims. Clearly distinguish
synthetic checks from NX execution. Do not commit generated STL, original documents,
or `.prt` files. Reports can be shared only when you have permission.

Contributions are provided under the repository's [MIT License](LICENSE).
提交问题、文档和案例可使用中文或英文；请给出可复现步骤并保留证据边界。
