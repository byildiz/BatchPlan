import re

import ifcopenshell
import ifcopenshell.geom
from ifcopenshell.util.selector import filter_elements
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh


def get_elements_and_shapes(model, filter_fn=None, filter=None):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_PYTHON_OPENCASCADE, True)

    rest = model
    if filter is not None and not isinstance(model, list):
        rest = filter_elements(model, filter)

    def cs(el):
        try:
            shape = ifcopenshell.geom.create_shape(settings, el)
            return shape
        except RuntimeError as e:
            print(f"Shape could not created for: type={el.is_a()}, name={el.Name}, exception={e}")
            return None

    elements = []
    shapes = []
    if filter_fn is not None:
        for el in rest:
            if not filter_fn(el):
                continue
            shape = cs(el)
            if shape is not None:
                elements.append(el)
                shapes.append(shape)
    else:
        for el in rest:
            shape = cs(el)
            if shape is not None:
                elements.append(el)
                shapes.append(shape)
    return elements, shapes


def get_geometries(shapes):
    return map(lambda s: s.geometry, shapes)


# https://github.com/tpaviot/pythonocc-demos/blob/master/examples/core_geometry_bounding_box.py
def get_bounding_box(shapes, tol=1e-6, use_mesh=False):
    bbox = Bnd_Box()
    bbox.SetGap(tol)
    for shape in shapes:
        if use_mesh:
            mesh = BRepMesh_IncrementalMesh()
            mesh.SetParallelDefault(True)
            mesh.SetShape(shape)
            mesh.Perform()
            if not mesh.IsDone():
                raise AssertionError("Mesh not done.")
        brepbndlib.Add(shape, bbox, use_mesh)
    return bbox.Get()


# tries to extract some meaningful name from KAAN projects
def get_name(element):
    name = element.Name
    if ":" in element.Name:
        name = ":".join(element.Name.split(":")[:2])
    matches = re.findall("(.*)_|\s+[0-9]+ ?mm", name)
    if len(matches) > 0:
        name = matches[0]
    return name


def get_reference(ref_str):
    return re.findall("\((.*)(\.|\:).*\)\+?", ref_str)[0][0]
