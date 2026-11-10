cmake_minimum_required(VERSION 3.20)
project(swarmforge_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release)
endif()

option(SWARMFORGE_BUILD_TESTS "Build C++ unit tests" ON)
option(SWARMFORGE_BUILD_BENCHMARKS "Build C++ benchmarks" ON)

add_library(swarmforge_core STATIC
  src/geometry/geometry_utils.cpp
  src/motion/differential_drive.cpp
  src/motion/velocity_limiter.cpp
  src/motion/trajectory.cpp)
target_include_directories(swarmforge_core PUBLIC include)
set_target_properties(swarmforge_core PROPERTIES POSITION_INDEPENDENT_CODE ON)
if(MSVC)
  target_compile_options(swarmforge_core PRIVATE /W4)
else()
  target_compile_options(swarmforge_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Plain C ABI, loaded from Python with ctypes (always built).
add_library(swarmforge_native SHARED src/bindings/c_api.cpp)
target_link_libraries(swarmforge_native PRIVATE swarmforge_core)
set_target_properties(swarmforge_native PROPERTIES CXX_VISIBILITY_PRESET hidden)

# Optional pybind11 module (swarmforge._core). Skipped silently when pybind11 is unavailable.
find_package(pybind11 CONFIG QUIET)
if(pybind11_FOUND)
  pybind11_add_module(_core src/bindings/pybind_module.cpp)
  target_link_libraries(_core PRIVATE swarmforge_core)
  install(TARGETS _core LIBRARY DESTINATION swarmforge)
endif()
install(TARGETS swarmforge_native LIBRARY DESTINATION swarmforge RUNTIME DESTINATION swarmforge)

if(SWARMFORGE_BUILD_TESTS)
  enable_testing()
  foreach(t geometry differential_drive velocity_limiter trajectory)
    add_executable(test_${t} tests/test_${t}.cpp)
    target_link_libraries(test_${t} PRIVATE swarmforge_core)
    add_test(NAME ${t} COMMAND test_${t})
  endforeach()
endif()

if(SWARMFORGE_BUILD_BENCHMARKS)
  add_executable(bench_kinematics benchmarks/bench_kinematics.cpp)
  target_link_libraries(bench_kinematics PRIVATE swarmforge_core)
endif()
