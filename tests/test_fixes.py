import OCC
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace
from OCC.Core.gp import gp_Pnt
from OCC.Core.TopTools import TopTools_HSequenceOfShape
from OCC.Display.SimpleGui import init_display

import fixes

display, start_display, add_menu, add_function_to_menu = init_display()


points = [
    gp_Pnt(0, 0, 0),
    gp_Pnt(1, 0, 0),
    gp_Pnt(1, 1, 0),
    gp_Pnt(0, 1, 0),
]
points2 = [
    gp_Pnt(2, 0, 0),
    gp_Pnt(4, 0, 0),
    gp_Pnt(4, 1, 0),
    gp_Pnt(2, 1, 0),
]

edges = []
# square
for i in range(len(points)):
    edge = BRepBuilderAPI_MakeEdge(points[i], points[(i + 1) % len(points)]).Edge()
    edges.append(edge)
# rectangle
for i in range(len(points2)):
    edge = BRepBuilderAPI_MakeEdge(points2[i], points2[(i + 1) % len(points2)]).Edge()
    edges.append(edge)

edge_shapes = TopTools_HSequenceOfShape()
wire_shapes = TopTools_HSequenceOfShape()

for e in edges:
    edge_shapes.Append(e)


print(f"Before: {len(edge_shapes)}")
wire_shapes = fixes.ConnectEdgesToWiresFixed(edge_shapes, 1e-3, False)
print(f"After: {len(wire_shapes)}")

wires = []
for i in range(wire_shapes.Size()):
    wires.append(wire_shapes.Value(i + 1))

faces = []
for w in wires:
    faces.append(BRepBuilderAPI_MakeFace(w).Face())

# for e in edges:
#     display.DisplayColoredShape(e, "BLUE", update=True)
for w in wires:
    display.DisplayColoredShape(w, "RED")
for f in faces:
    object = display.DisplayColoredShape(f, "BLUE")[0]
    object.SetTransparency(0.6)

display.View_Top()
display.FitAll()
display.ExportToImage("./test.png")

start_display()
