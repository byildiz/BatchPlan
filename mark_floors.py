import argparse
import csv
import functools
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
from ifcopenshell.util.placement import get_storey_elevation
from OCC.Display.OCCViewer import rgb_color
from OCC.Display.SimpleGui import init_display
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow

from utils import get_bounding_box

display = None
main_window = None

settings = ifcopenshell.geom.settings()
settings.set(settings.USE_PYTHON_OPENCASCADE, True)

shape_to_element = {}
floors = []


def load_ifc(ifc_file, use_storeys):
    global shape_to_element, floors

    shape_to_element = {}
    floors = []
    display.EraseAll()

    print(f"Loading {ifc_file}")
    model = ifcopenshell.open(ifc_file)
    for el in model.by_type("IfcSlab"):
        if el.Representation is None or el.is_a() == "IfcSpace":
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, el)
            geometry = shape.geometry
            shape_to_element[geometry] = el
            r, g, b, a = shape.styles[0]
            if r < 0 or g < 0 or b < 0 or a < 0:
                continue
            if not el.is_a("IfcSlab"):
                continue
            color = rgb_color(r, g, b)
            display.DisplayShape(geometry, color=color, transparency=abs(1 - a))
        except RuntimeError as e:
            print(f"Exception: name={el.Name}, exception={e}")
    display.FitAll()

    if use_storeys:
        for el in model.by_type("IfcBuildingStorey"):
            floors.append((el.Name, get_storey_elevation(el)))

    print(f"Loaded {ifc_file}")


def main():
    global display, main_window
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--use-storeys", action="store_true")
    args = parser.parse_args()

    root_path = Path(args.root)
    ifc_files = list(root_path.glob("*/3D/IFC/*.ifc"))
    selected_ifc_file = None

    display, start_display, add_menu, add_function_to_menu = init_display(size=(1024, 768))

    main_window = None
    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, QMainWindow):
            main_window = widget
    main_window.setWindowTitle("BatchPlan")

    viewer = display.get_parent()
    label = QLabel("", viewer)
    label.setStyleSheet("QLabel { color: black; }")
    label.move(10, 10)
    label.show()

    def set_selected_ifc(ifc_file, _: None):
        nonlocal selected_ifc_file
        selected_ifc_file = ifc_file
        load_ifc(selected_ifc_file, args.use_storeys)
        main_window.setWindowTitle(f"BatchPlan ({Path(ifc_file).name})")
        update_text()

    def update_text():
        text = "\n".join([f"{n}, {z}" for n, z in floors])
        label.setText(text)
        label.adjustSize()

    def handle_selection(shapes, *_):
        for shape in shapes:
            bbox = get_bounding_box([shape])
            z = int(bbox[5] * 1000)
            floors.append((f"floor_{len(floors)}", z))
            update_text()

    def save():
        out_dir = selected_ifc_file.parent.parent.parent / "Tabular/Floors"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{selected_ifc_file.stem}.csv"
        with out_file.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(floors)
        print(f"Saved {out_file}")

    def remove_last():
        floors.pop()
        update_text()

    def remove_all():
        floors.clear()
        update_text()

    display.register_select_callback(handle_selection)
    add_menu("IFC Files")
    for ifc_file in ifc_files:
        func = functools.partial(set_selected_ifc, ifc_file)
        func.__name__ = str(ifc_file)
        add_function_to_menu("IFC Files", func)
    add_menu("Commands")
    add_function_to_menu("Commands", remove_last)
    add_function_to_menu("Commands", remove_all)
    add_function_to_menu("Commands", save)

    start_display()


if __name__ == "__main__":
    main()
