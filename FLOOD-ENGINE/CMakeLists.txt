cmake_minimum_required(VERSION 3.20)
project(FloodEngine CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/output)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/output)

include_directories(
    ${CMAKE_SOURCE_DIR}/core
    ${CMAKE_SOURCE_DIR}/api
    ${CMAKE_SOURCE_DIR}/ml/inference
)

set(ENGINE_SOURCES
    core/raster.cpp
    core/flow_direction.cpp
    core/flow_accumulation.cpp
    core/timestep_flood.cpp
    core/swe_integration.cpp
    core/blend_integration.cpp
    ml/inference/randomForest.cpp
)

# DLL for Qt
add_library(FloodEngine SHARED
    ${ENGINE_SOURCES}
    api/FloodEngineAPI.cpp
)
set_target_properties(FloodEngine PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON)

# CLI exe — links engine sources directly, no DLL needed
add_executable(FloodEngineCLI main.cpp ${ENGINE_SOURCES})