"""NXOpen journal: export a temporary STL and the native feature list.

Run with NX's run_journal.exe:
  run_journal export_for_check.py -args input.prt output.stl
The input part is opened for inspection; this journal never saves it.
"""

import hashlib
import json
import os
import sys

import NXOpen


def main():
    if len(sys.argv) < 3:
        raise ValueError("pass input.prt and output.stl after -args")
    source, output = sys.argv[-2:]
    if os.path.exists(output):
        raise ValueError("output already exists; use a fresh temporary path")
    session = NXOpen.Session.GetSession()
    part, status = session.Parts.OpenBaseDisplay(source)
    if status:
        status.Dispose()
    bodies = [body for body in part.Bodies if body.IsSolidBody]
    if not bodies:
        raise ValueError("part has no solid body")
    creator = session.DexManager.CreateStlCreator()
    try:
        creator.OutputFile = output
        creator.OutputType = NXOpen.STLCreator.OutputTypeEnum.Binary
        creator.ChordalTol = 0.05
        creator.AngularTol = 10.0
        creator.AdjacencyTol = 0.01
        creator.AutoNormalGen = True
        for body in bodies:
            creator.ExportSelectionBlock.Add(body)
        creator.Commit()
    finally:
        creator.Destroy()
    history = {
        "units": "mm" if part.PartUnits == NXOpen.BasePart.Units.Millimeters else "inch",
        "source_sha256": hashlib.sha256(open(source, "rb").read()).hexdigest(),
        "stl_sha256": hashlib.sha256(open(output, "rb").read()).hexdigest(),
        "solid_bodies": len(bodies),
        "faces": sum(len(body.GetFaces()) for body in bodies),
        "features": [{"type": item.FeatureType, "name": item.Name,
                      "errors": list(item.GetFeatureErrorMessages()),
                      "warnings": list(item.GetFeatureWarningMessages())} for item in part.Features],
        "stl_chordal_tolerance": 0.05,
    }
    with open(output + ".history.json", "w") as handle:
        json.dump(history, handle, indent=2)


if __name__ == "__main__":
    main()
