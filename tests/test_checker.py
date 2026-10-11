import io
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image

from nx_drawing_checker import check_history, crop_views, extract_docx, read_stl, review, run_checks, validate_mesh


def box(low, high):
    vertices = [(x, y, z) for x in (low[0], high[0]) for y in (low[1], high[1]) for z in (low[2], high[2])]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return [tuple(vertices[i] for i in indices) for a, b, c, d in faces for indices in ((a, b, c), (a, c, d))]


def case_with(checks):
    return {
        "part": "fixture", "units": "mm",
        "views": {"plan": {"kind": "orthographic"}, "section": {"kind": "section"}},
        "features": [{"name": "window", "material": "void", "extent": "through", "evidence": [
            {"view": "plan", "observation": "enclosed window outline"},
            {"view": "section", "observation": "no floor in the section"}], "checks": checks}]
    }


class CheckerTests(unittest.TestCase):
    def test_void_requires_section_and_two_views(self):
        case = case_with([{"kind": "clear_line", "start": [0, 0, -2], "end": [0, 0, 2]}])
        self.assertEqual([], review(case))
        case["features"][0]["evidence"] = case["features"][0]["evidence"][:1]
        self.assertTrue(any("section" in item for item in review(case)))
        self.assertTrue(any("two" in item for item in review(case)))

    def test_through_window_catches_wrong_floor(self):
        frame = box((-3, -1, -1), (-1, 1, 1)) + box((1, -1, -1), (3, 1, 1))
        case = case_with([{"kind": "clear_line", "start": [0, 0, -2], "end": [0, 0, 2]}])
        self.assertTrue(run_checks(case, frame)[0]["passed"])
        wrong = frame + box((-0.8, -0.8, -0.2), (0.8, 0.8, 0.2))
        self.assertFalse(run_checks(case, wrong)[0]["passed"])

    def test_hidden_contour_can_support_depth_without_inventing_section(self):
        case = case_with([{"kind": "clear_line", "start": [0, 0, -2], "end": [0, 0, 2]}])
        case["views"]["section"]["kind"] = "orthographic"
        self.assertTrue(review(case))
        case["features"][0]["depth_basis"] = {
            "kind": "hidden_lines", "view": "section",
            "observation": "hidden bore walls join the inner cavity contour without a closing floor"}
        self.assertEqual([], review(case))

    def test_cavity_catches_intruding_solid(self):
        frame = box((-3, -1, -1), (-1, 1, 1)) + box((1, -1, -1), (3, 1, 1))
        case = case_with([{"kind": "clear_points", "points": [[0, 0, 0]]}])
        self.assertTrue(run_checks(case, frame)[0]["passed"])
        self.assertFalse(run_checks(case, frame + box((-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)))[0]["passed"])

    def test_clear_line_inside_solid_does_not_pass(self):
        case = case_with([{"kind": "clear_line", "start": [-0.2, 0, 0], "end": [0.2, 0, 0]}])
        self.assertFalse(run_checks(case, box((-1, -1, -1), (1, 1, 1)))[0]["passed"])

    def test_open_mesh_is_rejected(self):
        mesh = box((-1, -1, -1), (1, 1, 1))
        validate_mesh(mesh)
        with self.assertRaisesRegex(ValueError, "open"):
            validate_mesh(mesh[:-1])

    def test_history_rejects_flat_import_without_required_sketches(self):
        case = {"units": "mm", "history_requirements": {"minimum_features": {"SKETCH": 2}}}
        history = {"units": "mm", "solid_bodies": 1, "features": [{"type": "IMPORT", "name": "imported solid"}]}
        self.assertTrue(any(not item["passed"] for item in check_history(case, history)))
        history["features"] += [{"type": "SKETCH", "name": "one"}, {"type": "SKETCH", "name": "two"}]
        self.assertTrue(all(item["passed"] for item in check_history(case, history)))

    def test_ascii_and_binary_stl(self):
        mesh = box((-1, -1, -1), (1, 1, 1))
        with tempfile.TemporaryDirectory() as folder:
            ascii_path = Path(folder) / "ascii.stl"
            text = "solid cube\n" + "".join("facet normal 0 0 0\nouter loop\n" + "".join(f"vertex {x} {y} {z}\n" for x, y, z in tri) + "endloop\nendfacet\n" for tri in mesh) + "endsolid cube\n"
            ascii_path.write_text(text)
            binary_path = Path(folder) / "binary.stl"
            data = b"solid binary header".ljust(80, b" ") + struct.pack("<I", len(mesh))
            data += b"".join(struct.pack("<12fH", 0, 0, 0, *[n for vertex in tri for n in vertex], 0) for tri in mesh)
            binary_path.write_bytes(data)
            self.assertEqual(read_stl(ascii_path), read_stl(binary_path))

    def test_docx_preserves_bytes_and_document_order(self):
        pictures = []
        for size in ((10, 20), (30, 40)):
            buffer = io.BytesIO()
            Image.new("RGB", size).save(buffer, format="PNG")
            pictures.append(buffer.getvalue())
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.docx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("word/_rels/document.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Target="media/one.png"/><Relationship Id="r2" Target="media/two.png"/></Relationships>')
                archive.writestr("word/document.xml", '<document xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><a:blip r:embed="r2"/><a:blip r:embed="r1"/><a:blip r:embed="r2"/></document>')
                archive.writestr("word/media/one.png", pictures[0])
                archive.writestr("word/media/two.png", pictures[1])
            output = Path(folder) / "output"
            items = extract_docx(source, output)
            self.assertEqual([(30, 40), (10, 20)], [(item["width"], item["height"]) for item in items])
            self.assertEqual(pictures[1], (output / items[0]["file"]).read_bytes())
            self.assertEqual(pictures[0], (output / items[1]["file"]).read_bytes())

    def test_crop_bounds(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            Image.new("RGB", (20, 30)).save(root / "source.png")
            case = {"views": {"plan": {"image": "source.png", "box": [5, 10, 8, 12]}}}
            paths = crop_views(case, root / "case.json", root / "crops")
            with Image.open(paths[0]) as image:
                self.assertEqual((8, 12), image.size)
            case["views"]["plan"]["box"] = [15, 10, 8, 12]
            with self.assertRaisesRegex(ValueError, "outside"):
                crop_views(case, root / "case.json", root / "crops")


if __name__ == "__main__":
    unittest.main()
