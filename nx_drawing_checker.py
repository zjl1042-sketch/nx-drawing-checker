"""Review drawing evidence before modeling and verify selected geometry afterward.

The tool deliberately does not infer 3D topology from pixels. A person records
which views support each feature; the checks make those judgments testable.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image


DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/main"


def extract_docx(source: Path, output: Path) -> list[dict]:
    """Copy embedded images in document order without changing their pixels."""
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        relationships = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
        targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships.findall(f"{{{PKG_REL}}}Relationship")
        }
        document = ET.fromstring(archive.read("word/document.xml"))
        items = []
        seen = set()
        for image in document.iter(f"{{{DRAWING}}}blip"):
            relation = image.attrib.get(f"{{{DOC_REL}}}embed")
            if not relation or relation in seen:
                continue
            seen.add(relation)
            target = targets[relation].lstrip("/")
            member = target if target.startswith("word/") else f"word/{target}"
            data = archive.read(member)
            suffix = Path(member).suffix.lower()
            path = output / f"drawing-{len(items) + 1:02d}{suffix}"
            path.write_bytes(data)
            with Image.open(path) as picture:
                width, height = picture.size
            items.append(
                {
                    "file": path.name,
                    "width": width,
                    "height": height,
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
    (output / "index.json").write_text(
        json.dumps({"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "images": items}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return items


def load_case(path: Path) -> dict:
    case = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(case, dict) or not case.get("part") or not case.get("views"):
        raise ValueError("case needs a part name and views")
    return case


def review(case: dict) -> list[str]:
    """Return omissions that could allow an unsupported 3D interpretation."""
    problems = []
    views = case["views"]
    if not case.get("features"):
        problems.append("no features recorded")
    for feature in case.get("features", []):
        name = feature.get("name", "<unnamed>")
        if feature.get("material") not in {"solid", "void"}:
            problems.append(f"{name}: material must be solid or void")
        cited = {entry.get("view") for entry in feature.get("evidence", [])}
        if not cited or None in cited or not cited <= set(views):
            problems.append(f"{name}: evidence must name existing views")
        if any(not entry.get("observation", "").strip() for entry in feature.get("evidence", [])):
            problems.append(f"{name}: each cited view needs a concrete observation")
        if feature.get("material") == "void":
            if feature.get("extent") not in {"through", "blind", "cavity"}:
                problems.append(f"{name}: void extent must be through, blind, or cavity")
            if len(cited) < 2:
                problems.append(f"{name}: void needs evidence from two different views")
            basis = feature.get("depth_basis")
            has_section = any(views.get(view, {}).get("kind") == "section" for view in cited)
            if basis:
                kind = basis.get("kind")
                source = basis.get("view")
                valid = kind in {"section", "hidden_lines", "callout", "user_confirmation"} and bool(basis.get("observation", "").strip())
                if kind != "user_confirmation":
                    valid = valid and source in cited
                if kind == "section":
                    valid = valid and views.get(source, {}).get("kind") == "section"
                if kind == "hidden_lines":
                    valid = valid and views.get(source, {}).get("kind") == "orthographic"
                if not valid:
                    problems.append(f"{name}: invalid or incomplete void depth basis")
            elif not has_section:
                problems.append(f"{name}: void depth needs a section or explicit depth_basis")
            if not feature.get("checks"):
                problems.append(f"{name}: void needs at least one post-model check")
        for dimension in feature.get("dimensions", []):
            if dimension.get("status") not in {"stated", "estimated"}:
                problems.append(f"{name}: dimension status must be stated or estimated")
            if dimension.get("status") == "estimated" and not dimension.get("reason"):
                problems.append(f"{name}: estimated dimension needs a reason")
            if dimension.get("view") not in views:
                problems.append(f"{name}: dimension needs an existing source view")
    return problems


def crop_views(case: dict, case_path: Path, output: Path) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    cropped = []
    for name, view in case["views"].items():
        source = (case_path.parent / view["image"]).resolve()
        with Image.open(source) as picture:
            x, y, width, height = view["box"]
            if min(x, y) < 0 or min(width, height) <= 0 or x + width > picture.width or y + height > picture.height:
                raise ValueError(f"{name}: crop is outside source image")
            target = output / f"{name}.png"
            picture.crop((x, y, x + width, y + height)).save(target)
            cropped.append(target)
    return cropped


def read_stl(path: Path) -> list[tuple[tuple[float, float, float], ...]]:
    data = path.read_bytes()
    triangles = []
    if len(data) >= 84 and len(data) == 84 + struct.unpack_from("<I", data, 80)[0] * 50:
        count = struct.unpack_from("<I", data, 80)[0]
        for index in range(count):
            floats = struct.unpack_from("<12f", data, 84 + 50 * index)
            triangles.append((floats[3:6], floats[6:9], floats[9:12]))
    else:
        vertices = []
        for line in data.decode("utf-8").splitlines():
            tokens = line.strip().split()
            if tokens[:1] == ["vertex"] and len(tokens) == 4:
                vertices.append(tuple(float(value) for value in tokens[1:]))
        if len(vertices) % 3:
            raise ValueError("ASCII STL vertex count is not divisible by 3")
        triangles = [tuple(vertices[index:index + 3]) for index in range(0, len(vertices), 3)]
    if not triangles:
        raise ValueError("STL has no triangles")
    return triangles


def validate_mesh(triangles) -> None:
    """Parity tests need finite, closed facets with two faces per mesh edge."""
    edges = Counter()
    for triangle in triangles:
        if any(not math.isfinite(value) for vertex in triangle for value in vertex):
            raise ValueError("mesh contains non-finite coordinates")
        vertices = [tuple(round(value, 6) for value in vertex) for vertex in triangle]
        if len(set(vertices)) != 3:
            raise ValueError("mesh contains a degenerate triangle")
        for index in range(3):
            edges[tuple(sorted((vertices[index], vertices[(index + 1) % 3])))] += 1
    unclosed = sum(count != 2 for count in edges.values())
    if unclosed:
        raise ValueError(f"mesh is open or non-manifold: {unclosed} edges do not have exactly two faces")


def _minus(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def intersections(start, end, triangles) -> list[float]:
    """Distances along a finite segment where it crosses a triangle mesh."""
    direction = _minus(end, start)
    hits = []
    for a, b, c in triangles:
        edge1, edge2 = _minus(b, a), _minus(c, a)
        p = _cross(direction, edge2)
        determinant = _dot(edge1, p)
        if abs(determinant) < 1e-10:
            continue
        inverse = 1.0 / determinant
        t = _minus(start, a)
        u = inverse * _dot(t, p)
        if u < -1e-9 or u > 1 + 1e-9:
            continue
        q = _cross(t, edge1)
        v = inverse * _dot(direction, q)
        if v < -1e-9 or u + v > 1 + 1e-9:
            continue
        position = inverse * _dot(edge2, q)
        if 1e-9 < position < 1 - 1e-9:
            hits.append(position)
    hits.sort()
    unique = []
    for hit in hits:
        if not unique or hit - unique[-1] > 1e-7:
            unique.append(hit)
    return unique


def point_inside(point, triangles, maximum_x: float) -> bool:
    # Oblique ray avoids coplanar/axis-aligned mesh edges in ordinary CAD STL.
    distance = max(1.0, maximum_x - point[0] + 1.0)
    target = (point[0] + distance, point[1] + distance * 0.193649, point[2] + distance * 0.071927)
    return len(intersections(point, target, triangles)) % 2 == 1


def run_checks(case: dict, triangles) -> list[dict]:
    max_x = max(vertex[0] for triangle in triangles for vertex in triangle)
    results = []
    for feature in case.get("features", []):
        for check in feature.get("checks", []):
            kind = check["kind"]
            if kind in {"clear_line", "solid_line"}:
                count = len(intersections(check["start"], check["end"], triangles))
                if kind == "clear_line":
                    passed = count == 0 and not any(point_inside(point, triangles, max_x) for point in (check["start"], check["end"]))
                else:
                    passed = count >= 2
                detail = f"{count} surface crossings"
            elif kind == "clear_points":
                occupied = sum(point_inside(point, triangles, max_x) for point in check["points"])
                passed = occupied == 0
                detail = f"{occupied}/{len(check['points'])} test points contain solid"
            elif kind == "clear_spherical_cap":
                center = check["center"]
                radius = float(check["radius"]) - float(check.get("margin", 0))
                step = float(check["step"])
                if step <= 0 or radius <= 0:
                    raise ValueError("cap step and effective radius must be positive")
                zmin, zmax = check["z_range"]
                count = occupied = 0
                for z_index in range(math.ceil((zmax - zmin) / step) + 1):
                    z = zmin + z_index * step
                    if z > zmax:
                        continue
                    for x_index in range(math.ceil(2 * radius / step) + 1):
                        x = center[0] - radius + x_index * step
                        for y_index in range(math.ceil(2 * radius / step) + 1):
                            y = center[1] - radius + y_index * step
                            if (x - center[0]) ** 2 + (y - center[1]) ** 2 + (z - center[2]) ** 2 >= radius ** 2:
                                continue
                            count += 1
                            occupied += point_inside((x, y, z), triangles, max_x)
                if count == 0:
                    raise ValueError("spherical cap check sampled no points")
                passed = occupied == 0
                detail = f"{occupied}/{count} cavity test points contain solid"
            elif kind == "inner_sphere_surface":
                center = check["center"]
                radius = float(check["radius"])
                tolerance = float(check["tolerance"])
                start_radius = radius - max(2.0, tolerance * 3)
                end_radius = radius + max(8.0, tolerance * 5)
                failed = 0
                samples = 0
                for theta_deg in check["polar_degrees"]:
                    theta = math.radians(theta_deg)
                    for phi_deg in check["azimuth_degrees"]:
                        phi = math.radians(phi_deg)
                        direction = (math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta))
                        start = [center[index] + start_radius * direction[index] for index in range(3)]
                        end = [center[index] + end_radius * direction[index] for index in range(3)]
                        hits = intersections(start, end, triangles)
                        samples += 1
                        if point_inside(start, triangles, max_x) or not hits or abs(start_radius + hits[0] * (end_radius - start_radius) - radius) > tolerance:
                            failed += 1
                if not samples:
                    raise ValueError("inner sphere check needs directions")
                passed = failed == 0
                detail = f"{failed}/{samples} inner-wall rays deviate from R{radius} by more than {tolerance} mm"
            else:
                raise ValueError(f"unknown check kind: {kind}")
            results.append({"feature": feature["name"], "check": check.get("name", kind), "passed": passed, "detail": detail})
    if not results:
        raise ValueError("case has no model checks")
    return results


def check_history(case: dict, history: dict) -> list[dict]:
    requirements = case.get("history_requirements", {})
    features = history.get("features", [])
    counts = Counter(item["type"] for item in features)
    checks = [("单位", history.get("units") == case.get("units"), str(history.get("units"))),
              ("实体数量", history.get("solid_bodies") == requirements.get("solid_bodies", 1), str(history.get("solid_bodies")))]
    errors = sum(len(item.get("errors", [])) for item in features)
    checks.append(("NX 特征错误", errors == 0, f"{errors} 条错误"))
    for kind, minimum in requirements.get("minimum_features", {}).items():
        checks.append((f"{kind} 数量", counts[kind] >= minimum, f"{counts[kind]}，至少 {minimum}"))
    for required in requirements.get("required_features", []):
        matches = [item for item in features if item["type"] == required["type"] and required["name_contains"] in item["name"]]
        checks.append((required["name_contains"], bool(matches), f"{len(matches)} 个匹配特征"))
    return [{"feature": "NX 建模历史", "check": name, "passed": passed, "detail": detail} for name, passed, detail in checks]


def report(case: dict, problems: list[str], checks: list[dict] | None = None) -> str:
    lines = [f"# {case['part']} · 读图与模型校核", "", f"单位：{case.get('units', '未注明')}", "", "## 视图", ""]
    for name, view in case["views"].items():
        lines.append(f"- **{name}**（{view['kind']}）：{view.get('note', '')}")
    lines += ["", "## 特征与证据", ""]
    for feature in case.get("features", []):
        lines.append(f"### {feature['name']}")
        lines.append("")
        lines.append(f"{feature['material']} · {feature.get('extent', '表面/外形')}")
        lines.append("")
        for evidence in feature.get("evidence", []):
            lines.append(f"- {evidence['view']}：{evidence['observation']}")
        if feature.get("depth_basis"):
            basis = feature["depth_basis"]
            lines.append(f"- 深度依据（{basis['kind']}）：{basis['observation']}")
        for dimension in feature.get("dimensions", []):
            reason = f"；估计依据：{dimension['reason']}" if dimension.get("status") == "estimated" else ""
            lines.append(f"- {dimension['name']} = {dimension['value']}（{dimension['status']}，{dimension['view']}{reason}）")
        lines.append("")
    lines += ["## 读图检查", "", "通过" if not problems else "未通过", ""]
    lines.extend(f"- {problem}" for problem in problems)
    if checks is not None:
        lines += ["", "## 模型几何检查", ""]
        lines.extend(f"- {'通过' if item['passed'] else '失败'}：{item['feature']} / {item['check']}，{item['detail']}" for item in checks)
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="extract original DOCX images in document order")
    extract.add_argument("docx", type=Path)
    extract.add_argument("output", type=Path)
    crop = commands.add_parser("crop", help="make lossless-resolution crops of named views")
    crop.add_argument("case", type=Path)
    crop.add_argument("output", type=Path)
    preview = commands.add_parser("preview", help="render orthographic views and a section outline")
    preview.add_argument("stl", type=Path)
    preview.add_argument("output", type=Path)
    preview.add_argument("--section-axis", choices=["x", "y", "z"], default="y")
    preview.add_argument("--section-position", type=float, default=0)
    for name in ("review", "check-stl"):
        command = commands.add_parser(name)
        command.add_argument("case", type=Path)
        if name == "check-stl":
            command.add_argument("stl", type=Path)
            command.add_argument("--history", type=Path, help="NX journal's feature-history JSON")
        command.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "extract":
            print(json.dumps(extract_docx(args.docx, args.output), ensure_ascii=False, indent=2))
            return 0
        if args.command == "preview":
            from nx_preview import render_mesh
            for path in render_mesh(read_stl(args.stl), args.output, args.section_axis, args.section_position):
                print(path)
            return 0
        case = load_case(args.case)
        if args.command == "crop":
            for path in crop_views(case, args.case, args.output):
                print(path)
            return 0
        problems = review(case)
        checks = None
        if args.command == "check-stl" and not problems:
            triangles = read_stl(args.stl)
            validate_mesh(triangles)
            checks = run_checks(case, triangles)
            if args.history:
                history = json.loads(args.history.read_text(encoding="utf-8"))
                if history.get("stl_sha256") != hashlib.sha256(args.stl.read_bytes()).hexdigest():
                    raise ValueError("history and STL do not match; export both together again")
                checks += check_history(case, history)
            elif case.get("history_requirements"):
                raise ValueError("case requires an NX history export; supply --history")
        content = report(case, problems, checks)
        if args.report:
            args.report.write_text(content, encoding="utf-8")
        else:
            print(content)
        return 1 if problems or checks is not None and any(not item["passed"] for item in checks) else 0
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
