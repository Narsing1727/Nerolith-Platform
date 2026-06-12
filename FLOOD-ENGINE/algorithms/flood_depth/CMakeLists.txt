cmake_minimum_required(VERSION 3.20)
project(test_flood_depth CXX)
set(CMAKE_CXX_STANDARD 17)

add_executable(test_manning
    manning.cpp
    test_manning.cpp
)
