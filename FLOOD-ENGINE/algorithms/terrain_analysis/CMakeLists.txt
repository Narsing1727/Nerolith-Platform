cmake_minimum_required(VERSION 3.20)
project(test_terrain_analysis CXX)
set(CMAKE_CXX_STANDARD 17)

add_executable(test_twi
    twi.cpp
    test_twi.cpp
)
