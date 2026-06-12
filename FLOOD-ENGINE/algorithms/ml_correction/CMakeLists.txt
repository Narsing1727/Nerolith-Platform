cmake_minimum_required(VERSION 3.20)
project(test_ml_correction CXX)
set(CMAKE_CXX_STANDARD 17)

add_executable(test_physics_ml_blend
    physics_ml_blend.cpp
    test_physics_ml_blend.cpp
)
