import argparse
from pathlib import Path
from importlib import import_module

import ifcopenshell
import ifcopenshell.geom
import OCC.Core.BRepAlgoAPI
import pandas as pd
from ifcopenshell.util.element import get_decomposition
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.TopTools import TopTools_HSequenceOfShape
from OCC.Display.OCCViewer import rgb_color
from OCC.Display.SimpleGui import init_display
from OCC.Extend.TopologyUtils import TopologyExplorer
from tqdm import tqdm

import filters
import fixes
import stylings
from utils import (
    get_bounding_box,
    get_elements_and_shapes,
    get_geometries,
)

# os.environ["PYTHONOCC_OFFSCREEN_RENDERER"] = "1"

display, start_display, add_menu, add_function_to_menu = None, None, None, None


def draw_shapes(display, elements, shapes, color_fn=None, skip_colorless=False):
    for element, shape in zip(elements, shapes):
        try:
            geometry = shape.geometry
            if color_fn is None:
                r, g, b, a = shape.styles[0]
                if r < 0 or g < 0 or b < 0 or a < 0:
                    continue
            else:
                (r, g, b, a), found = color_fn(element, shape)
                if skip_colorless and not found:
                    continue
                # a = 0.7
            color = rgb_color(r, g, b)
            display.DisplayShape(geometry, color=color, transparency=abs(1 - a))
        except RuntimeError as e:
            print(f"Exception: name={element.Name}, exception={e}")


def draw_sections(display, elements, shapes, shape_faces, color_fn=None, skip_colorless=False):
    for element, shape, faces in zip(elements, shapes, shape_faces):
        if color_fn is None:
            r, g, b, a = shape.styles[0]
            if r < 0 or g < 0 or b < 0 or a < 0:
                continue
        else:
            (r, g, b, a), found = color_fn(element, shape)
            if skip_colorless and not found:
                continue
            # a = 0.7
        color = rgb_color(r, g, b)
        for face in faces:
            display.DisplayShape(face, color=color, transparency=abs(1 - a))


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


def process_using_storeys(ifc_path, out_dir, filter_fn, color_fn, skip_colorless=False):
    model = ifcopenshell.open(ifc_path)
    print("Loading and filtering elements and shapes...")
    elements, shapes = get_elements_and_shapes(model.by_type("IfcElement"), filter_fn)
    print("Done")

    print("Drawing shapes for 3D...")
    display.EraseAll()
    draw_shapes(display, elements, shapes, color_fn=color_fn, skip_colorless=skip_colorless)
    print("Done")

    global_bbox = get_bounding_box(get_geometries(shapes))

    level_items = []
    storeys = list(model.by_type("IfcBuildingStorey"))
    for s0, s1 in zip(storeys[:-1], storeys[1:]):
        name = s0.Name
        section_height = (s0.Elevation + s1.Elevation) / 2000
        print(f"Storey: {name}")

        section_surface = get_section_surface(
            section_height, global_bbox[0], global_bbox[1], global_bbox[3], global_bbox[4]
        )
        section_elements = get_decomposition(s0)
        elements, shapes = get_elements_and_shapes(section_elements, context["filter_fn"])
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
    path_to_export = str(out_dir / "3D.png")
    display.ExportToImage(path_to_export)

    for name, sp, ss, sf in tqdm(level_items, desc="Floor plan", total=len(level_items)):
        display.EraseAll()
        draw_sections(display, sp, ss, sf, color_fn=color_fn, skip_colorless=skip_colorless)
        display.View_Top()
        display.FitAll()
        path_to_export = str(out_dir / f"{name}_floor_plan.png")
        display.ExportToImage(path_to_export)

    for name, sp, ss, _ in tqdm(level_items, desc="Level 3D", total=len(level_items)):
        display.EraseAll()
        draw_shapes(display, sp, ss, color_fn=color_fn, skip_colorless=skip_colorless)
        display.View_Iso()
        display.FitAll()
        path_to_export = str(out_dir / f"{name}_3D.png")
        display.ExportToImage(path_to_export)


def process(ifc_path, levels, out_dir, filter_fn, color_fn, skip_colorless=False):
    model = ifcopenshell.open(ifc_path)
    print("Loading elements and shapes...")
    elements, shapes = get_elements_and_shapes(model, filter_fn)
    print(len(elements))
    print("Done")

    print("Drawing shapes for 3D...")
    display.EraseAll()
    draw_shapes(display, elements, shapes, color_fn=color_fn, skip_colorless=skip_colorless)
    print("Done")

    global_bbox = get_bounding_box(get_geometries(shapes))

    level_items = []
    for name, section_height in tqdm(levels, desc="Levels", total=len(levels)):
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
    path_to_export = str(out_dir / "3D.png")
    display.ExportToImage(path_to_export)

    for name, sp, ss, sf in tqdm(level_items, desc="Floor plan", total=len(level_items)):
        display.EraseAll()
        draw_sections(display, sp, ss, sf, color_fn=color_fn, skip_colorless=skip_colorless)
        display.View_Top()
        display.FitAll()
        path_to_export = str(out_dir / f"{name}_floor_plan.png")
        display.ExportToImage(path_to_export)

    for name, sp, ss, _ in tqdm(level_items, desc="Level 3D", total=len(level_items)):
        display.EraseAll()
        draw_shapes(display, sp, ss, color_fn=color_fn, skip_colorless=skip_colorless)
        display.View_Iso()
        display.FitAll()
        path_to_export = str(out_dir / f"{name}_3D.png")
        display.ExportToImage(path_to_export)


def main():
    global display, start_display, add_menu, add_function_to_menu

    parser = argparse.ArgumentParser()
    parser.add_argument("ifc")
    parser.add_argument("--use-storey", action="store_true")
    parser.add_argument("--load-plugin", action="store_true")
    parser.add_argument("--filter-fn", default="default_filter")
    parser.add_argument("--color-fn", default="all_black")
    parser.add_argument("--skip-colorless", action="store_true")
    parser.add_argument("--width", default=2048)
    parser.add_argument("--height", default=2048)
    args = parser.parse_args()

    plugin = None
    if args.load_plugin:
        try:
            plugin = import_module("plugin")
        except ModuleNotFoundError as e:
            print(f"Importing the plugin failed: {e}")
            exit()

    display, start_display, add_menu, add_function_to_menu = init_display(
        size=(int(args.width), int(args.height)),
        display_triedron=False,
        background_gradient_color1=[255, 255, 255],
        background_gradient_color2=[255, 255, 255],
    )

    if hasattr(plugin, args.filter_fn):
        filter_fn = getattr(plugin, args.filter_fn)
    else:
        filter_fn = getattr(filters, args.filter_fn)
    filter_fn = filter_fn()

    if hasattr(plugin, args.color_fn):
        color_fn = getattr(plugin, args.color_fn)
    else:
        color_fn = getattr(stylings, args.color_fn)
    color_fn = color_fn()

    ifc_path = Path(args.ifc)
    project_root = ifc_path.parent.parent.parent
    out_dir = project_root / "2D/Renders" / ifc_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.use_storey:
        process_using_storeys(ifc_path, out_dir, filter_fn, color_fn, skip_colorless=args.skip_colorless)
    else:
        floor_file = project_root / f"Tabular/Floors/{ifc_path.stem}.csv"
        if not floor_file.exists():
            raise ValueError(f"Floor file doesn't exist: {floor_file}")
        columns = ["l", "e"]
        levels = pd.read_csv(floor_file, names=columns).to_dict("records")
        levels = [(l0["l"], (l0["e"] + l1["e"]) / 2000) for l0, l1 in zip(levels[:-1], levels[1:])]
        process(ifc_path, levels, out_dir, filter_fn, color_fn, skip_colorless=args.skip_colorless)


# TODO Merge mark_floor plans and extract_floor_plans with Fire and name the combined program as BatchPlan
# TODO Make section extraction not only Z direction but also X and Y directions
if __name__ == "__main__":
    main()
