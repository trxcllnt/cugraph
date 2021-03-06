#=============================================================================
# Copyright (c) 2018-2020, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#=============================================================================

cmake_minimum_required(VERSION 3.12 FATAL_ERROR)

project(CUGRAPH VERSION 0.16.0 LANGUAGES C CXX CUDA)

###################################################################################################
# - build type ------------------------------------------------------------------------------------

# Set a default build type if none was specified
set(DEFAULT_BUILD_TYPE "Release")

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  message(STATUS "Setting build type to '${DEFAULT_BUILD_TYPE}' since none specified.")
  set(CMAKE_BUILD_TYPE "${DEFAULT_BUILD_TYPE}" CACHE
      STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
    "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

###################################################################################################
# - compiler options ------------------------------------------------------------------------------

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_C_COMPILER $ENV{CC})
set(CMAKE_CXX_COMPILER $ENV{CXX})
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_CUDA_STANDARD 14)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

if(CMAKE_COMPILER_IS_GNUCXX)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Werror -Wno-error=deprecated-declarations")
endif(CMAKE_COMPILER_IS_GNUCXX)

find_package(CUDA)

# Check for aarch64 vs workstation architectures
if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64")
  message(STATUS "CMAKE Detected aarch64 CPU architecture, selecting appropriate gencodes")
  # This is being build for Linux4Tegra or SBSA ARM64 CUDA
  set(GPU_ARCHS "62") # Default minimum CUDA GenCode - not supported by gunrock
  if(CUDA_VERSION_MAJOR GREATER_EQUAL 9)
    set(GPU_ARCHS "${GPU_ARCHS};72")
    set(GUNROCK_GENCODE "-DGUNROCK_GENCODE_SM72=TRUE")
  endif()
  if(CUDA_VERSION_MAJOR GREATER_EQUAL 11)
    # This is probably for SBSA CUDA, or a next gen Jetson
    set(GPU_ARCHS "${GPU_ARCHS};75;80")
    set(GUNROCK_GENCODE "${GUNROCK_GENCODE} -DGUNROCK_GENCODE_SM75=TRUE -DGUNROCK_GENCODE_SM80=TRUE ")
  endif()

else()
  message(STATUS "CMAKE selecting appropriate gencodes for x86 or ppc64 CPU architectures")
  # System architecture was not aarch64,
  # this is datacenter or workstation class hardware
  set(GPU_ARCHS "60") # Default minimum supported CUDA gencode
  set(GUNROCK_GENCODE "-DGUNROCK_GENCODE_SM60=TRUE")
  if(CUDA_VERSION_MAJOR GREATER_EQUAL 9)
    set(GPU_ARCHS "${GPU_ARCHS};70")
    set(GUNROCK_GENCODE "${GUNROCK_GENCODE} -DGUNROCK_GENCODE_SM70=TRUE")
  endif()
  if(CUDA_VERSION_MAJOR GREATER_EQUAL 10)
    set(GPU_ARCHS "${GPU_ARCHS};75")
    set(GUNROCK_GENCODE "${GUNROCK_GENCODE} -DGUNROCK_GENCODE_SM75=TRUE")
  endif()
  if(CUDA_VERSION_MAJOR GREATER_EQUAL 11)
    set(GPU_ARCHS "${GPU_ARCHS};80")
    set(GUNROCK_GENCODE "${GUNROCK_GENCODE} -DGUNROCK_GENCODE_SM80=TRUE")
  endif()

endif()

message("-- Building for GPU_ARCHS = ${GPU_ARCHS}")
foreach(arch ${GPU_ARCHS})
  set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -gencode arch=compute_${arch},code=sm_${arch}")
endforeach()

list(GET GPU_ARCHS -1 ptx)
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -gencode arch=compute_${ptx},code=compute_${ptx}")

set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} --expt-extended-lambda")
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -Werror=cross-execution-space-call -Wno-deprecated-declarations -Xptxas --disable-warnings")
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -Xcompiler -Wall,-Wno-error=sign-compare,-Wno-error=unused-but-set-variable")

# Option to enable line info in CUDA device compilation to allow introspection when profiling /
# memchecking
option(CMAKE_CUDA_LINEINFO "Enable the -lineinfo option for nvcc (useful for cuda-memcheck / profiler" OFF)
if (CMAKE_CUDA_LINEINFO)
    set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -lineinfo")
endif(CMAKE_CUDA_LINEINFO)

# Debug options
if(CMAKE_BUILD_TYPE MATCHES Debug)
    message(STATUS "Building with debugging flags")
    set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -G -Xcompiler -rdynamic")
endif(CMAKE_BUILD_TYPE MATCHES Debug)

# To apply RUNPATH to transitive dependencies (this is a temporary solution)
set(CMAKE_SHARED_LINKER_FLAGS "-Wl,--disable-new-dtags")
set(CMAKE_EXE_LINKER_FLAGS "-Wl,--disable-new-dtags")

option(BUILD_TESTS "Configure CMake to build tests"
       ON)

###################################################################################################
# - cmake modules ---------------------------------------------------------------------------------

set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/Modules/" ${CMAKE_MODULE_PATH})

include(FeatureSummary)
include(CheckIncludeFiles)
include(CheckLibraryExists)
if(BUILD_TESTS)
    include(CTest)
endif(BUILD_TESTS)

###################################################################################################
# - find boost ------------------------------------------------------------------------------------

find_package(Boost REQUIRED)
if(Boost_FOUND)
    message(STATUS "Boost found in ${Boost_INCLUDE_DIRS}")
else()
    message(FATAL_ERROR "Boost not found, please check your settings.")
endif(Boost_FOUND)

###################################################################################################
# - find openmp -----------------------------------------------------------------------------------

find_package(OpenMP)
if(OpenMP_FOUND)
    # find_package(OPenMP) does not automatically add OpenMP flags to CUDA
    set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -Xcompiler=${OpenMP_CXX_FLAGS}")
endif(OpenMP_FOUND)

###################################################################################################
# - find libcypher-parser -------------------------------------------------------------------------

find_path(LIBCYPHERPARSER_INCLUDE "cypher-parser.h"
          HINTS "$ENV{CONDA_PREFIX}/include")

find_library(LIBCYPHERPARSER_LIBRARY STATIC "libcypher-parser.a"
             HINTS "$ENV{CONDA_PREFIX}/lib")

add_library(libcypher-parser STATIC IMPORTED ${LIBCYPHERPARSER_LIBRARY})
if (LIBCYPHERPARSER_INCLUDE AND LIBCYPHERPARSER_LIBRARY)
    set_target_properties(libcypher-parser PROPERTIES IMPORTED_LOCATION ${LIBCYPHERPARSER_LIBRARY})
endif (LIBCYPHERPARSER_INCLUDE AND LIBCYPHERPARSER_LIBRARY)

###################################################################################################
# - find gtest ------------------------------------------------------------------------------------

if(BUILD_TESTS)
    include(ConfigureGoogleTest)

    if(GTEST_FOUND)
        message(STATUS
            "Google C++ Testing Framework (Google Test) found in ${GTEST_ROOT}")
    else()
        message(AUTHOR_WARNING
            "Google C++ Testing Framework (Google Test) not found: automated tests are disabled.")
    endif(GTEST_FOUND)
endif(BUILD_TESTS)

###################################################################################################
# - RMM -------------------------------------------------------------------------------------------

find_path(RMM_INCLUDE "rmm"
    HINTS
    "$ENV{RMM_ROOT}/include"
    "$ENV{CONDA_PREFIX}/include/rmm"
    "$ENV{CONDA_PREFIX}/include")

message(STATUS "RMM: RMM_INCLUDE set to ${RMM_INCLUDE}")

###################################################################################################
# - Fetch Content ---------------------------------------------------------------------------------
include(FetchContent)

# - THRUST/CUB
message("Fetching Thrust")

FetchContent_Declare(
    thrust
    GIT_REPOSITORY https://github.com/thrust/thrust.git
    # August 28, 2020
    GIT_TAG        52a8bda46c5c2128414d1d47f546b486ff0be2f0
)

FetchContent_GetProperties(thrust)
if(NOT thrust_POPULATED)
  FetchContent_Populate(thrust)
  # We are not using the thrust CMake targets, so no need to call `add_subdirectory()`.
endif()
set(THRUST_INCLUDE_DIR "${thrust_SOURCE_DIR}")

###################################################################################################
# - External Projects -----------------------------------------------------------------------------

# https://cmake.org/cmake/help/v3.0/module/ExternalProject.html
include(ExternalProject)

# - CUHORNET
set(CUHORNET_DIR ${CMAKE_CURRENT_BINARY_DIR}/cuhornet CACHE STRING "Path to cuhornet repo")
set(CUHORNET_INCLUDE_DIR ${CUHORNET_DIR}/src/cuhornet CACHE STRING "Path to cuhornet includes")


ExternalProject_Add(cuhornet
  GIT_REPOSITORY    https://github.com/rapidsai/cuhornet.git
  GIT_TAG           9cb8e8803852bd895a9c95c0fe778ad6eeefa7ad
  PREFIX            ${CUHORNET_DIR}
  CONFIGURE_COMMAND ""
  BUILD_COMMAND     ""
  INSTALL_COMMAND   ""
)

# - GUNROCK
set(CUGUNROCK_DIR ${CMAKE_CURRENT_BINARY_DIR}/cugunrock CACHE STRING
  "Path to cugunrock repo")

ExternalProject_Add(cugunrock
  GIT_REPOSITORY    https://github.com/rapidsai/cugunrock.git
  GIT_TAG           0b92fae6ee9026188a811b4d08915779e7c97178
  PREFIX            ${CUGUNROCK_DIR}
  CMAKE_ARGS        -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR>
                    -DGUNROCK_BUILD_SHARED_LIBS=OFF
                    -DGUNROCK_BUILD_TESTS=OFF
                    -DCUDA_AUTODETECT_GENCODE=FALSE
                    ${GUNROCK_GENCODE}
  BUILD_BYPRODUCTS  ${CUGUNROCK_DIR}/lib/libgunrock.a
)

add_library(gunrock STATIC IMPORTED)

add_dependencies(gunrock cugunrock)

set_property(TARGET gunrock PROPERTY IMPORTED_LOCATION ${CUGUNROCK_DIR}/lib/libgunrock.a)

# - NCCL
if(NOT NCCL_PATH)
    find_package(NCCL REQUIRED)
else()
    message("-- Manually set NCCL PATH to ${NCCL_PATH}")
    set(NCCL_INCLUDE_DIRS ${NCCL_PATH}/include)
    set(NCCL_LIBRARIES ${NCCL_PATH}/lib/libnccl.so)
endif(NOT NCCL_PATH)

# - raft - (header only) -----------------------------------------------------

# Only cloned if RAFT_PATH env variable is not defined

if(DEFINED ENV{RAFT_PATH})
  message(STATUS "RAFT_PATH environment variable detected.")
  message(STATUS "RAFT_DIR set to $ENV{RAFT_PATH}")
  set(RAFT_DIR "$ENV{RAFT_PATH}")

  ExternalProject_Add(raft
    DOWNLOAD_COMMAND  ""
    SOURCE_DIR        ${RAFT_DIR}
    CONFIGURE_COMMAND ""
    BUILD_COMMAND     ""
    INSTALL_COMMAND   "")

else(DEFINED ENV{RAFT_PATH})
  message(STATUS "RAFT_PATH environment variable NOT detected, cloning RAFT")
  set(RAFT_DIR ${CMAKE_CURRENT_BINARY_DIR}/raft CACHE STRING "Path to RAFT repo")

  ExternalProject_Add(raft
    GIT_REPOSITORY    https://github.com/rapidsai/raft.git
    GIT_TAG           515ed005aebc2276d52308516e623a4ab0b5e82c
    PREFIX            ${RAFT_DIR}
    CONFIGURE_COMMAND ""
    BUILD_COMMAND     ""
    INSTALL_COMMAND   "")

  # Redefining RAFT_DIR so it coincides with the one inferred by env variable.
  set(RAFT_DIR "${RAFT_DIR}/src/raft/")
endif(DEFINED ENV{RAFT_PATH})


###################################################################################################
# - library targets -------------------------------------------------------------------------------

# target_link_directories is added in cmake 3.13, and cmake advises to use this instead of
# link_directoires (we should switch to target_link_directories once 3.13 becomes the minimum
# required version).
link_directories(
     # CMAKE_CUDA_IMPLICIT_LINK_DIRECTORIES is an undocumented/unsupported variable containing the
     # link directories for nvcc.
    "${CMAKE_CUDA_IMPLICIT_LINK_DIRECTORIES}")

add_library(cugraph SHARED
    src/db/db_object.cu
    src/db/db_parser_integration_test.cu
    src/db/db_operators.cu
    src/utilities/spmv_1D.cu
    src/utilities/cython.cu
    src/structure/graph.cu
    src/link_analysis/pagerank.cu
    src/link_analysis/pagerank_1D.cu
    src/link_analysis/gunrock_hits.cpp
    src/traversal/bfs.cu
    src/traversal/sssp.cu
    src/link_prediction/jaccard.cu
    src/link_prediction/overlap.cu
    src/layout/force_atlas2.cu
    src/converters/renumber.cu
    src/converters/COOtoCSR.cu
    src/community/spectral_clustering.cu
    src/community/louvain.cu
    src/community/leiden.cu
    src/community/ktruss.cu
    src/community/ECG.cu
    src/community/triangles_counting.cu
    src/community/extract_subgraph_by_vertex.cu
    src/cores/core_number.cu
    src/traversal/two_hop_neighbors.cu
    src/components/connectivity.cu
    src/centrality/katz_centrality.cu
    src/centrality/betweenness_centrality.cu
    src/experimental/graph.cu
    src/experimental/graph_view.cu
    src/experimental/bfs.cu
    src/experimental/sssp.cu
    src/experimental/pagerank.cu
    src/experimental/katz_centrality.cu
)

#
# NOTE:  This dependency will force the building of cugraph to
#        wait until after cugunrock is constructed.
#
add_dependencies(cugraph cugunrock)
add_dependencies(cugraph raft)

###################################################################################################
# - include paths ---------------------------------------------------------------------------------
target_include_directories(cugraph
    PRIVATE
    "${THRUST_INCLUDE_DIR}"
    "${CMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES}"
    "${LIBCYPHERPARSER_INCLUDE}"
    "${Boost_INCLUDE_DIRS}"
    "${RMM_INCLUDE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../thirdparty"
    "${CUHORNET_INCLUDE_DIR}/hornet/include"
    "${CUHORNET_INCLUDE_DIR}/hornetsnest/include"
    "${CUHORNET_INCLUDE_DIR}/xlib/include"
    "${CUHORNET_INCLUDE_DIR}/primitives"
    "${CMAKE_CURRENT_SOURCE_DIR}/src"
    "${CUGUNROCK_DIR}/include"
    "${NCCL_INCLUDE_DIRS}"
    "${RAFT_DIR}/cpp/include"
    PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

###################################################################################################
# - link libraries --------------------------------------------------------------------------------

target_link_libraries(cugraph PRIVATE
    gunrock cublas cusparse curand cusolver cudart cuda ${LIBCYPHERPARSER_LIBRARY} ${MPI_CXX_LIBRARIES} ${NCCL_LIBRARIES})

if(OpenMP_CXX_FOUND)
target_link_libraries(cugraph PRIVATE
###################################################################################################
###   Use ${OpenMP_CXX_LIB_NAMES} instead of OpenMP::OpenMP_CXX to avoid the following warnings.
###
###   Cannot generate a safe runtime search path for target TARGET_NAME
###   because files in some directories may conflict with libraries in implicit
###   directories:
###   ...
###
###   libgomp.so is included in the conda base environment and copied to every new conda
###   environment. If a full file path is provided (e.g ${NCCL_LIBRARIES}), cmake
###   extracts the directory path and adds the directory path to BUILD_RPATH (if BUILD_RPATH is not
###   disabled).
###
###   cmake maintains a system specific implicit directories (e.g. /lib, /lib/x86_64-linux-gnu,
###   /lib32, /lib32/x86_64-linux-gnu, /lib64, /lib64/x86_64-linux-gnu, /usr/lib,
###   /usr/lib/gcc/x86_64-linux-gnu/7, /usr/lib/x86_64-linux-gnu, /usr/lib32,
###   /usr/lib32/x86_64-linux-gnu, /usr/lib64, /usr/lib64/x86_64-linux-gnu,
###   /usr/local/cuda-10.0/lib64", /usr/local/cuda-10.0/lib64/stubs).
###
###   If a full path to libgomp.so is provided (which is the case with OpenMP::OpenMP_CXX), cmake
###   checks whether there is any other libgomp.so with the different full path (after resolving
###   soft links) in the search paths (implicit directoires + BUILD_RAPTH). There is one in the
###   path included in BUILD_RPATH when ${NCCL_LIBRARIES} are added; this one can
###   potentially hide the one in the provided full path and cmake generates a warning (and RPATH
###   is searched before the directories in /etc/ld.so/conf; ld.so.conf does not coincide but
###   overlaps with implicit directories).
###
###   If we provide just the library names (gomp;pthread), cmake does not generate warnings (we
###   did not specify which libgomp.so should be loaded in runtime), and the one first found in
###   the search order is loaded (we can change the loaded library by setting LD_LIBRARY_PATH or
###   manually editing BUILD_RPATH).
###
###   Manually editing BUILD_RPATH:
###   set(TARGET_BUILD_RPATH "")
###   foreach(TMP_VAR_FULLPATH IN LISTS OpenMP_CXX_LIBRARIES)
###       get_filename_component(TMP_VAR_DIR ${TMP_VAR_FULLPATH} DIRECTORY)
###       string(APPEND TARGET_BUILD_RPATH "${TMP_VAR_DIR};")
###       get_filename_component(TMP_VAR_REALPATH ${TMP_VAR_FULLPATH} REALPATH)
###       get_filename_component(TMP_VAR_DIR ${TMP_VAR_REALPATH} DIRECTORY)
###       # cmake automatically removes duplicates, so skip checking.
###       string(APPEND TARGET_BUILD_RPATH "${TMP_VAR_DIR};")
###   endforeach()
###   string(APPEND TARGET_BUILD_RPATH "${CONDA_PREFIX}/lib")
###   message(STATUS "TARGET_BUILD_RPATH=${TARGET_BUILD_RPATH}")
###   set_target_properties(target PROPERTIES
###       BUILD_RPATH "${TARGET_BUILD_RPATH}")
    ${OpenMP_CXX_LIB_NAMES})
endif(OpenMP_CXX_FOUND)

###################################################################################################
# - generate tests --------------------------------------------------------------------------------

if(BUILD_TESTS)
    if(GTEST_FOUND)
        # target_link_directories is added in cmake 3.13, and cmake advises to use this instead of
        # link_directoires (we should switch to target_link_directories once 3.13 becomes the
        # minimum required version).
        link_directories(${GTEST_LIBRARY_DIR})
        add_subdirectory(${CMAKE_SOURCE_DIR}/tests)
    endif(GTEST_FOUND)
endif(BUILD_TESTS)

###################################################################################################
# - install targets -------------------------------------------------------------------------------

install(TARGETS cugraph LIBRARY
    DESTINATION lib)

install(DIRECTORY include/
    DESTINATION include/cugraph)

install(DIRECTORY ${RAFT_DIR}/cpp/include/raft/
    DESTINATION include/cugraph/raft)
###################################################################################################
# - make documentation ----------------------------------------------------------------------------
# requires doxygen and graphviz to be installed
# from build directory, run make docs_cugraph

# doc targets for cuGraph
add_custom_command(OUTPUT CUGRAPH_DOXYGEN
                   WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/doxygen
                   COMMAND doxygen Doxyfile
                   VERBATIM)

add_custom_target(docs_cugraph DEPENDS CUGRAPH_DOXYGEN)
