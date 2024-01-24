from abc import abstractmethod

from OCC.Display.OCCViewer import rgb_color

# os.environ["PYTHONOCC_OFFSCREEN_RENDERER"] = "1"


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
        color = rgb_color(r, g, b)
        for face in faces:
            display.DisplayShape(face, color=color, transparency=abs(1 - a))


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
            color = rgb_color(r, g, b)
            display.DisplayShape(geometry, color=color, transparency=abs(1 - a))
        except RuntimeError as e:
            print(f"Exception: name={element.Name}, exception={e}")


class Formatter:
    @abstractmethod
    def process(self, name, elements, shapes, faces):
        raise NotImplementedError()


class FloorPlanFormatter(Formatter):
    def __init__(self, context):
        self.context = context
        self.display = context["display"]

    def process(self, name, elements, shapes, faces):
        self.display.EraseAll()
        draw_sections(
            self.display,
            elements,
            shapes,
            faces,
            color_fn=self.context["color_fn"],
            skip_colorless=self.context["args"].skip_colorless,
        )
        self.display.View_Top()
        self.display.FitAll()
        path_to_export = str(self.context["output_dir"] / f"{name}_floor_plan.png")
        self.display.ExportToImage(path_to_export)


class Floor3DFormatter(Formatter):
    def __init__(self, context):
        self.context = context
        self.display = context["display"]

    def process(self, name, elements, shapes, _):
        self.display.EraseAll()
        draw_shapes(
            self.display,
            elements,
            shapes,
            color_fn=self.context["color_fn"],
            skip_colorless=self.context["args"].skip_colorless,
        )
        self.display.View_Iso()
        self.display.FitAll()
        path_to_export = str(self.context["output_dir"] / f"{name}_3D.png")
        self.display.ExportToImage(path_to_export)
