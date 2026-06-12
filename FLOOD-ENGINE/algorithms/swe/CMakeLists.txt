cmake_minimum_required(VERSION 3.20)
project(test_swe CXX)
set(CMAKE_CXX_STANDARD 17)

add_executable(test_diffusive_wave
    diffusive_wave.cpp
    test_diffusive_wave.cpp
)
