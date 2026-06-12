cmake_minimum_required(VERSION 3.20)
project(test_infiltration CXX)
set(CMAKE_CXX_STANDARD 17)

add_executable(test_green_ampt
    green_ampt.cpp
    test_green_ampt.cpp
)
