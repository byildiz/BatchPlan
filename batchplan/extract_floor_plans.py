import argparse
import glob
from importlib import import_module
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import OCC.Core.BRepAlgoAPI
import pandas as pd
from ifcopenshell.util.element import get_decomposition
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.TopTools import TopTools_HSequenceOfShape
from OCC.Display.SimpleGui import init_display
from OCC.Extend.TopologyUtils import TopologyExplorer
from tqdm import tqdm

from . import filters, fixes, formatters, stylings
from .formatters import draw_shapes
from .utils import (
    get_bounding_box,
    get_elements_and_shapes,
    get_geometries,
)


def get_section_surface(section_height, xmin, ymin, xmax, ymax):
    section_plane = OCC.Core.gp.gp_Pln(OCC.Core.gp.gp_Pnt(0, 0, section_height), OCC.Core.gp.gp_Dir(0, 0, 1))
    return OCC.Core.BRepBuilderAPI.BRepBuilderAPI_MakeFace(section_plane, xmin - 1, xmax + 1, ymin - 1, ymax + 1).Face()


def get_section_faces(section_surface, shape):
    section = BRepAlgoAPI_Section(section_surface, shape.geometry).Shape()
    section_edges = list(TopologyExplorer(section).edges())

    if len(section_edges) == 0:
        return []

    edge_shapes = TopTools_HSequenceOfShape()
    for edge in section_edges:
        edge_shapes.Append(edge)
    wire_shapes = fixes.ConnectEdgesToWiresFixed(edge_shapes, 1e-5, True)

    faces = []
    for j in range(len(wire_shapes)):
        wire_shape = wire_shapes.Value(j + 1)
        face = BRepBuilderAPI_MakeFace(wire_shape).Face()
        faces.append(face)
    return faces


def process_using_storeys(context):
    model = ifcopenshell.open(context["ifc_path"])
    print("Loading and filtering elements and shapes...")
    elements, shapes = get_elements_and_shapes(model, filter_fn=context.get("filter_fn"))
    print("Done")
    print("Total # elements:", len(elements))

    display = context["display"]
    print("Drawing shapes for 3D...")
    display.EraseAll()
    draw_shapes(display, elements, shapes, color_fn=context["color_fn"], skip_colorless=context["args"].skip_colorless)
    print("Done")

    global_bbox = get_bounding_box(get_geometries(shapes))

    level_items = []
    storeys = list(model.by_type("IfcBuildingStorey"))
    for s0, s1 in zip(storeys[:-1], storeys[1:]):
        name = s0.Name
        # find the middle of two storeys in meters
        section_height = (s0.Elevation + s1.Elevation) / 2000
        print(f"Storey: {name}")

        section_surface = get_section_surface(
            section_height, global_bbox[0], global_bbox[1], global_bbox[3], global_bbox[4]
        )
        section_elements = get_decomposition(s0)
        elements, shapes = get_elements_and_shapes(section_elements, filter_fn=context.get("filter_fn"))
        section_elements = []
        section_shapes = []
        section_faces = []
        for element, shape in zip(elements, shapes):
            faces = get_section_faces(section_surface, shape)
            if len(faces) > 0:
                section_elements.append(element)
                section_shapes.append(shape)
                section_faces.append(faces)

        if len(section_shapes) > 0:
            level_items.append((name, section_elements, section_shapes, section_faces))

            # now we can calculate a more strict bbox
            bbox = get_bounding_box(get_geometries(section_shapes))
            section_surface = get_section_surface(section_height, bbox[0], bbox[1], bbox[3], bbox[4])
            display.DisplayShape(section_surface, transparency=0.7)

    display.View_Iso()
    display.FitAll()
    path_to_export = str(context["output_dir"] / "3D.png")
    display.ExportToImage(path_to_export)

    for name, se, ss, sf in tqdm(level_items, desc="Running formatters", total=len(level_items)):
        for formatter in context["formatters"]:
            formatter.process(name, se, ss, sf)


def process(context):
    model = ifcopenshell.open(context["ifc_path"])
    print("Loading elements and shapes...")
    elements, shapes = get_elements_and_shapes(model, filter_fn=context.get("filter_fn"), filter=context.get("filter"))
    print("Done")
    print("Total # elements:", len(elements))

    display = context["display"]
    print("Drawing shapes for 3D...")
    display.EraseAll()
    draw_shapes(display, elements, shapes, color_fn=context["color_fn"], skip_colorless=context["args"].skip_colorless)
    print("Done")

    global_bbox = get_bounding_box(get_geometries(shapes))

    levels = context["levels"]
    level_items = []
    for name, section_height in tqdm(levels, desc="Finding sections", total=len(levels)):
        section_surface = get_section_surface(
            section_height, global_bbox[0], global_bbox[1], global_bbox[3], global_bbox[4]
        )
        section_elements = []
        section_shapes = []
        section_faces = []
        for element, shape in zip(elements, shapes):
            faces = get_section_faces(section_surface, shape)
            if len(faces) > 0:
                section_elements.append(element)
                section_shapes.append(shape)
                section_faces.append(faces)

        if len(section_shapes) > 0:
            level_items.append((name, section_elements, section_shapes, section_faces))

            # now we can calculate a more strict bbox
            bbox = get_bounding_box(get_geometries(section_shapes))
            section_surface = get_section_surface(section_height, bbox[0], bbox[1], bbox[3], bbox[4])
            display.DisplayShape(section_surface, transparency=0.7)

    display.View_Iso()
    display.FitAll()
    path_to_export = str(context["output_dir"] / "3D.png")
    display.ExportToImage(path_to_export)

    for name, se, ss, sf in tqdm(level_items, desc="Running formatters", total=len(level_items)):
        for formatter in context["formatters"]:
            formatter.process(name, se, ss, sf)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ifc_paths")
    parser.add_argument("--output", default="output")
    parser.add_argument("--use-storey", action="store_true")
    parser.add_argument("--load-plugin", action="store_true")
    parser.add_argument("--formatter", action="append", default=["FloorPlanFormatter", "Floor3DFormatter"])
    parser.add_argument("--filter-fn", default="default_filter")
    parser.add_argument("--filter")
    parser.add_argument("--color-fn", default="all_black")
    parser.add_argument("--skip-colorless", action="store_true")
    parser.add_argument("--width", default=2048)
    parser.add_argument("--height", default=2048)
    args = parser.parse_args()

    context = {}
    context["args"] = args

    plugin = None
    if args.load_plugin:
        try:
            plugin = import_module("plugin")
        except ModuleNotFoundError as e:
            print(f"Importing the plugin failed: {e}")
            exit()

    display = init_display(
        size=(int(args.width), int(args.height)),
        display_triedron=False,
        background_gradient_color1=[255, 255, 255],
        background_gradient_color2=[255, 255, 255],
    )[0]
    context["display"] = display

    filter_fn = None
    if hasattr(plugin, args.filter_fn):
        filter_fn = getattr(plugin, args.filter_fn)
    elif hasattr(filters, args.filter_fn):
        filter_fn = getattr(filters, args.filter_fn)
    context["filter_fn"] = filter_fn()

    if args.use_storey and args.filter is not None:
        print("Warning: filter and use_storey options don't work together as expected.")
    context["filter"] = args.filter

    if hasattr(plugin, args.color_fn):
        color_fn = getattr(plugin, args.color_fn)
    else:
        color_fn = getattr(stylings, args.color_fn)
    context["color_fn"] = color_fn()

    context["formatters"] = []
    for name in args.formatter:
        if hasattr(plugin, name):
            Formatter = getattr(plugin, name)
        else:
            Formatter = getattr(formatters, name)
        context["formatters"].append(Formatter(context))

    ifc_paths = glob.glob(args.ifc_paths)
    if len(ifc_paths) == 0:
        print("No IFC file found!")
    for ifc_path in ifc_paths:
        print(f"Processing: {ifc_path}")
        ifc_path = Path(ifc_path)
        output_dir = Path(args.output) / ifc_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        context["output_dir"] = output_dir
        context["ifc_path"] = ifc_path
        if args.use_storey:
            process_using_storeys(context)
        else:
            level_file = ifc_path.parent / f"{ifc_path.stem}.csv"
            context["level_file"] = level_file
            if not level_file.exists():
                raise ValueError(f"Level file doesn't exist: {level_file}")
            columns = ["l", "e"]
            levels = pd.read_csv(level_file, names=columns).to_dict("records")
            context["levels"] = [(l0["l"], (l0["e"] + l1["e"]) / 2000) for l0, l1 in zip(levels[:-1], levels[1:])]
            process(context)


# TODO Merge mark_floor plans and extract_floor_plans with Fire and name the combined program as BatchPlan
# TODO Make section extraction not only Z direction but also X and Y directions
if __name__ == "__main__":
    main()
