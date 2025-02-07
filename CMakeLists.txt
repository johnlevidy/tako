cmake_minimum_required(VERSION 3.11)
project(milestone1 CXX)

# Set the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Fetch gsl-lite (header-only) ---
include(FetchContent)
FetchContent_Declare(
  gsl-lite
  GIT_REPOSITORY https://github.com/gsl-lite/gsl-lite.git
  GIT_TAG v0.42.0            # Use the tag "v0.42.0" as specified
  SOURCE_SUBDIR include     # Only fetch the header files from the "include" folder
)
FetchContent_MakeAvailable(gsl-lite)

# --- Define an interface target for gsl-lite as GSL::GSL ---
if (NOT TARGET GSL::GSL)
  add_library(GSL INTERFACE)
  # Add the directory that contains gsl.hpp so that the user can simply do #include <gsl.hpp>
  target_include_directories(GSL INTERFACE ${gsl-lite_SOURCE_DIR}/include)
  add_library(GSL::GSL ALIAS GSL)
endif()

# --- Fetch tartanllama expected (header-only) ---
FetchContent_Declare(
  tl_expected
  GIT_REPOSITORY https://github.com/TartanLlama/expected.git
  GIT_TAG v1.1.0             # Adjust the version/tag as needed; for example "0.8.0"
  SOURCE_SUBDIR include    # Only fetch the header files from the "include" folder
)
FetchContent_MakeAvailable(tl_expected)

# --- Define an interface target for tartanllama expected as TL::expected ---
if (NOT TARGET TL::expected)
  add_library(TL_EXPECTED INTERFACE)
  # Add the directory that directly contains the "tl" folder so that
  # you can include <tl/expected.hpp> without an extra "include/" prefix.
  target_include_directories(TL_EXPECTED INTERFACE ${tl_expected_SOURCE_DIR}/include)
  add_library(TL::expected ALIAS TL_EXPECTED)
endif()

# --- Define source file and executable ---
set(SOURCE_FILE "${CMAKE_SOURCE_DIR}/python/test_types/milestone1_main.cc")
add_executable(milestone1 ${SOURCE_FILE})

# --- Use these include directories for milestone1 ---
target_include_directories(milestone1 PRIVATE
    "${CMAKE_SOURCE_DIR}/python/test_types"
    "${CMAKE_SOURCE_DIR}/python/milestone1/test_types/milestone1"
    "${CMAKE_SOURCE_DIR}/c/src/runtime"
)

# --- Link dependencies ---
target_link_libraries(milestone1 PRIVATE GSL::GSL TL::expected)
