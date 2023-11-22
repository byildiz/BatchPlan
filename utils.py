import re

import ifcopenshell
import ifcopenshell.geom
import matplotlib.colors as mcolors
import pandas as pd
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

EXCLUDED_ELEMENTS = ("IfcSite", "IfcSpace", "IfcOpeningElement")


def get_products_and_shapes(elements):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_PYTHON_OPENCASCADE, True)

    products = []
    shapes = []
    for el in elements:
        if not el.is_a("IfcProduct") or el.Representation is None or any([el.is_a(e) for e in EXCLUDED_ELEMENTS]):
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, el)
            products.append(el)
            shapes.append(shape)
        except RuntimeError as e:
            print(f"Exception: name={el.Name}, exception={e}")
    return products, shapes


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
def get_name(product):
    name = product.Name
    if ":" in product.Name:
        name = ":".join(product.Name.split(":")[:2])
    matches = re.findall("(.*)_|\s+[0-9]+ ?mm", name)
    if len(matches) > 0:
        name = matches[0]
    return name


def get_reference(ref_str):
    return re.findall("\((.*)(\.|\:).*\)\+?", ref_str)[0][0]


def get_hash_color_fn():
    cmap = mcolors.CSS4_COLORS
    color_names = list(cmap)

    def fn(product, shape):
        type = product.is_a()
        h = hash(type)
        k = color_names[h % len(cmap)]
        return mcolors.to_rgba(cmap[k]), True

    return fn


REF_COL = "Product Ref"
NAME_COL = "Product Name"
SCORE_COL = "Element Environmental Score"


def get_carbon_color_fn():
    df = pd.read_csv("totem_mapping_materials_assigned.csv")
    cols = [REF_COL, NAME_COL]
    df[cols] = df[cols].ffill()
    df = df[df["Selected"] == 1]
    scores = df[SCORE_COL]
    scores = (scores - scores.min()) / (scores.max() - scores.min())
    df[SCORE_COL] = scores
    # cmap = matplotlib.colormaps["RdYlGn"]
    cmap = mcolors.LinearSegmentedColormap.from_list("gyr", ["g", "y", "r"], N=1024)

    def fn(product, shape):
        name = get_name(product)
        df2 = df[df[NAME_COL] == name]
        if len(df2) == 0:
            print(f"Warning: No associated score for: Type: {product.is_a()}, Name: {name}")
            score = 0.5
            found = False
        else:
            score = df2[SCORE_COL].tolist()[0]
            found = True
        return cmap(score), found

    return fn
