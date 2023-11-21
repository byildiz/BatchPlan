from pathlib import Path

import ifcopenshell
import pandas as pd
import fire

from utils import get_bounding_box, get_geometries, get_products_and_shapes


def calculate_global_bbox(input_path, output_path="global_bboxes.csv"):
    ifc_paths = list(Path(input_path).glob("*/3D/IFC/*.ifc"))
    bboxes = []
    for ifc_path in ifc_paths:
        print(ifc_path)
        ifc_file = ifcopenshell.open(ifc_path)
        _, shapes = get_products_and_shapes(ifc_file.by_type("IfcProduct"))
        bbox = get_bounding_box(get_geometries(shapes))
        bboxes.append([str(ifc_path), *bbox])
    df = pd.DataFrame(bboxes, columns=("ifc", "xmin", "ymin", "zmin", "xmax", "ymax", "zmax"))
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    fire.Fire({"calculate_global_bbox": calculate_global_bbox})
