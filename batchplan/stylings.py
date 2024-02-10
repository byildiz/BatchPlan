import matplotlib.colors as mcolors
import pandas as pd

from .utils import get_name


def all_black():
    def fn(el, sh):
        return (0, 0, 0, 0), True

    return fn


def hash_color():
    cmap = mcolors.CSS4_COLORS
    color_names = list(cmap)

    def fn(el, sh):
        type = el.is_a()
        h = hash(type)
        k = color_names[h % len(cmap)]
        return mcolors.to_rgba(cmap[k]), True

    return fn


REF_COL = "Product Ref"
NAME_COL = "Product Name"
SCORE_COL = "Element Environmental Score"


def carbon_color():
    df = pd.read_csv("totem_mapping_materials_assigned.csv")
    cols = [REF_COL, NAME_COL]
    df[cols] = df[cols].ffill()
    df = df[df["Selected"] == 1]
    scores = df[SCORE_COL]
    scores = (scores - scores.min()) / (scores.max() - scores.min())
    df[SCORE_COL] = scores
    # cmap = matplotlib.colormaps["RdYlGn"]
    cmap = mcolors.LinearSegmentedColormap.from_list("gyr", ["g", "y", "r"], N=1024)

    def fn(el, sh):
        name = get_name(el)
        df2 = df[df[NAME_COL] == name]
        if len(df2) == 0:
            print(f"Warning: No associated score for: Type: {el.is_a()}, Name: {name}")
            score = 0.5
            found = False
        else:
            score = df2[SCORE_COL].tolist()[0]
            found = True
        return cmap(score), found

    return fn
