cmake_minimum_required(VERSION 3.20)
project(test_flow_direction CXX)
set(CMAKE_CXX_STANDARD 17)

add_executable(test_d8
    d8.cpp
    test_d8.cpp
)
