// #include<ShapeAnalysis.hxx>
// #include<ShapeAnalysis_BoxBndTree.hxx>
// #include<ShapeAnalysis_CanonicalRecognition.hxx>
// #include<ShapeAnalysis_CheckSmallFace.hxx>
// #include<ShapeAnalysis_Curve.hxx>
// #include<ShapeAnalysis_DataMapIteratorOfDataMapOfShapeListOfReal.hxx>
// #include<ShapeAnalysis_DataMapOfShapeListOfReal.hxx>
// #include<ShapeAnalysis_Edge.hxx>
// #include<ShapeAnalysis_FreeBoundData.hxx>
// #include<ShapeAnalysis_FreeBounds.hxx>
// #include<ShapeAnalysis_FreeBoundsProperties.hxx>
// #include<ShapeAnalysis_Geom.hxx>
// #include<ShapeAnalysis_HSequenceOfFreeBounds.hxx>
// #include<ShapeAnalysis_SequenceOfFreeBounds.hxx>
// #include<ShapeAnalysis_ShapeContents.hxx>
// #include<ShapeAnalysis_ShapeTolerance.hxx>
// #include<ShapeAnalysis_Shell.hxx>
// #include<ShapeAnalysis_Surface.hxx>
// #include<ShapeAnalysis_TransferParameters.hxx>
// #include<ShapeAnalysis_TransferParametersProj.hxx>
// #include<ShapeAnalysis_Wire.hxx>
// #include<ShapeAnalysis_WireOrder.hxx>
// #include<ShapeAnalysis_WireVertex.hxx>

#include <Standard.hxx>
// #include <Standard_DefineAlloc.hxx>
// #include <Standard_Handle.hxx>
// #include <ShapeAnalysis_FreeBounds.hxx>
#include <TopTools_HSequenceOfShape.hxx>

extern "C" {
opencascade::handle<TopTools_HSequenceOfShape>
ConnectEdgesToWiresFixed(opencascade::handle<TopTools_HSequenceOfShape> &edges,
                         const double toler, const bool shared);
}