cmake_minimum_required(VERSION 3.20)

project(Fixes)

find_package(Python3 REQUIRED COMPONENTS Development.Module Interpreter)
include_directories(${Python3_INCLUDE_DIRS})
message(STATUS ${Python3_VERSION})
message(STATUS ${Python3_INCLUDE_DIRS})
message(STATUS ${Python3_LIBRARIES})

find_package(OpenCASCADE 7.7.2 REQUIRED)
include_directories(${OpenCASCADE_INCLUDE_DIR})
message(STATUS ${OpenCASCADE_INCLUDE_DIR})
message(STATUS ${OpenCASCADE_LIBRARIES})
message(STATUS ${OpenCASCADE_FoundationClasses_LIBRARIES})
message(STATUS ${OpenCASCADE_ModelingData_LIBRARIES})
message(STATUS ${OpenCASCADE_ModelingAlgorithms_LIBRARIES})

find_package(SWIG 4 REQUIRED COMPONENTS python)
include(${SWIG_USE_FILE})
message(STATUS ${SWIG_VERSION})
message(STATUS ${SWIG_EXECUTABLE})

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/swig)

set_source_files_properties(swig/Fixes.i PROPERTIES CPLUSPLUS ON)
swig_add_library(Fixes LANGUAGE python SOURCES swig/Fixes.i swig/Fixes.cxx)
target_link_libraries(Fixes ${Python3_LIBRARIES} ${OpenCASCADE_FoundationClasses_LIBRARIES} ${OpenCASCADE_ModelingData_LIBRARIES} ${OpenCASCADE_ModelingAlgorithms_LIBRARIES})

if(APPLE)
	set_property(TARGET Fixes APPEND PROPERTY LINK_FLAGS "-flat_namespace")
endif()

if(CALL_FROM_SETUP_PY)
	set(SWIG_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
else()
	set(SWIG_INSTALL_PREFIX ${Python3_SITELIB})
endif()

get_property(WRAPPER_PY_FILE TARGET Fixes PROPERTY SWIG_SUPPORT_FILES)

install(FILES ${WRAPPER_PY_FILE} DESTINATION ${SWIG_INSTALL_PREFIX} COMPONENT bindings)

install(TARGETS Fixes COMPONENT bindings LIBRARY DESTINATION ${SWIG_INSTALL_PREFIX} ARCHIVE DESTINATION ${SWIG_INSTALL_PREFIX} RUNTIME DESTINATION ${SWIG_INSTALL_PREFIX})
