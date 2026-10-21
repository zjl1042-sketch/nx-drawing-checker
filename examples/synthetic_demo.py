"""Generate public, synthetic STL fixtures and verify expected CLI exit codes.

Run from a source checkout after `python -m pip install -e .`.
These fixtures are mathematical solids, not NX exports or engineering drawings.
"""
import json
from pathlib import Path
import tempfile

from nx_drawing_checker import main


def box(low, high):
    vertices = [(x, y, z) for x in (low[0], high[0])
                for y in (low[1], high[1]) for z in (low[2], high[2])]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return [tuple(vertices[i] for i in indices) for a, b, c, d in faces
            for indices in ((a, b, c), (a, c, d))]


def write_stl(path, triangles):
    facets = []
    for triangle in triangles:
        vertices = "".join(f"vertex {x} {y} {z}\n" for x, y, z in triangle)
        facets.append("facet normal 0 0 0\nouter loop\n" + vertices + "endloop\nendfacet\n")
    path.write_text("solid synthetic\n" + "".join(facets) + "endsolid synthetic\n", encoding="utf-8")


def run_demo():
    case = {
        "part": "Synthetic clearance demo", "units": "mm",
        "views": {
            "plan": {"kind": "orthographic", "note": "Synthetic specification; no source drawing."},
            "section": {"kind": "section", "note": "Synthetic specification; clearance along Z."}},
        "features": [{"name": "specified clearance", "material": "void", "extent": "through",
            "evidence": [
                {"view": "plan", "observation": "Specification leaves the origin clear between two solids."},
                {"view": "section", "observation": "Specification requires Z=-2 to Z=2 to remain clear."}],
            "checks": [{"kind": "clear_line", "start": [0, 0, -2], "end": [0, 0, 2]}]}]}
    clear = box((-3, -1, -1), (-1, 1, 1)) + box((1, -1, -1), (3, 1, 1))
    blocked = clear + box((-0.8, -0.8, -0.2), (0.8, 0.8, 0.2))
    with tempfile.TemporaryDirectory(prefix="nx-checker-demo-") as folder:
        root = Path(folder)
        case_path = root / "case.json"
        case_path.write_text(json.dumps(case), encoding="utf-8")
        for name, mesh, expected in (("blocked", blocked, 1), ("clear", clear, 0)):
            stl = root / f"{name}.stl"
            write_stl(stl, mesh)
            actual = main(["check-stl", str(case_path), str(stl)])
            if actual != expected:
                raise RuntimeError(f"{name}: expected exit {expected}, got {actual}")
            print(f"DEMO {name}: expected={expected}, actual={actual}")
    print("DEMO PASS: blocked clearance rejected; clear version accepted.")


if __name__ == "__main__":
    run_demo()
