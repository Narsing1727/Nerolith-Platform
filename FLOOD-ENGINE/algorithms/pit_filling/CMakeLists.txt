cmake_minimum_required(VERSION 3.20)
project(test_pit_filling CXX)
set(CMAKE_CXX_STANDARD 17)

add_executable(test_wang_liu
    wang_liu.cpp
    test_wang_liu.cpp
)
