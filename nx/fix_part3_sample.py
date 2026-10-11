"""Case-specific correction of the supplied spherical-cover sample.

run_journal.exe fix_part3_sample.py -args input.prt separate-output.prt
Refuses existing output and any sketch coordinates other than the known sample.
"""
import os
import sys
import NXOpen

source, output = sys.argv[-2:]
if os.path.exists(output) or os.path.abspath(source) == os.path.abspath(output):
    raise ValueError("use a fresh separate output part")
session = NXOpen.Session.GetSession()
part, status = session.Parts.OpenBaseDisplay(source)
if status: status.Dispose()
mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Correct longround port position and through cut")
sketches = [f for f in part.Features if f.FeatureType == "SKETCH"]
extrudes = [f for f in part.Features if f.FeatureType == "EXTRUDE"]
if len(sketches) != 2 or len(extrudes) != 3:
    raise ValueError("unexpected sample history")
for feature in sketches:
    sketch = feature.Sketch
    curves = sketch.GetAllGeometry()
    centers = sorted(round(c.CenterPoint.X, 6) for c in curves if isinstance(c, NXOpen.Arc))
    if centers != [-66.0, -47.0]:
        raise ValueError("unexpected sample coordinates")
    sketch.Activate(NXOpen.Sketch.ViewReorient.FalseValue)
    for curve in curves:
        if isinstance(curve, NXOpen.Line):
            a, b = curve.StartPoint, curve.EndPoint
            curve.SetEndpoints(NXOpen.Point3d(a.X+5, a.Y, a.Z), NXOpen.Point3d(b.X+5, b.Y, b.Z))
        elif isinstance(curve, NXOpen.Arc):
            c = curve.CenterPoint
            curve.SetParameters(curve.Radius, NXOpen.Point3d(c.X+5, c.Y, c.Z), curve.StartAngle, curve.EndAngle)
        else:
            raise ValueError("unexpected sketch curve type")
    sketch.Update()
    sketch.Deactivate(NXOpen.Sketch.ViewReorient.FalseValue, NXOpen.Sketch.UpdateLevel.Model)
for feature, start in [(extrudes[0], "0"), (extrudes[1], "-1")]:
    builder = part.Features.CreateExtrudeBuilder(feature)
    try:
        builder.Limits.StartExtend.Value.RightHandSide = start
        builder.CommitFeature()
    finally:
        builder.Destroy()
if session.UpdateManager.DoUpdate(mark):
    raise ValueError("NX model update reported errors")
if len([b for b in part.Bodies if b.IsSolidBody]) != 1:
    raise ValueError("result must contain one solid body")
part.ModelingViews.WorkView.Fit()
saved = part.SaveAs(output)
if saved: saved.Dispose()
