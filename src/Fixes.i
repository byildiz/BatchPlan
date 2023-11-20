%module fixes

%{
#include <TopTools_HSequenceOfShape.hxx>
#include "Fixes.hxx"
%}

%include "OCCHandle.i"

%wrap_handle(TopTools_HSequenceOfShape)

%include "Fixes.hxx"