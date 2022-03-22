#=============================================================================
# Copyright (c) 2022, NVIDIA CORPORATION.
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

set(CUGRAPH_MIN_VERSION_cugraph_ops "${CUGRAPH_VERSION_MAJOR}.${CUGRAPH_VERSION_MINOR}.00")
set(CUGRAPH_BRANCH_VERSION_cugraph_ops "${CUGRAPH_VERSION_MAJOR}.${CUGRAPH_VERSION_MINOR}")

function(find_and_configure_cugraph_ops)

    set(oneValueArgs VERSION FORK PINNED_TAG CLONE_ON_PIN)
    cmake_parse_arguments(PKG "" "${oneValueArgs}" "" ${ARGN} )

    if(PKG_CLONE_ON_PIN AND NOT PKG_PINNED_TAG STREQUAL "branch-${CUGRAPH_BRANCH_VERSION_cugraph_ops}")
        message("Pinned tag found: ${PKG_PINNED_TAG}. Cloning cugraph-ops locally.")
        set(CPM_DOWNLOAD_cugraph-ops ON)
    endif()

    rapids_cpm_find(cugraph-ops ${PKG_VERSION}
      GLOBAL_TARGETS      cugraph-ops::cugraph-ops++
      BUILD_EXPORT_SET    cugraph-exports
      INSTALL_EXPORT_SET  cugraph-exports
        CPM_ARGS
            GIT_REPOSITORY https://github.com/${PKG_FORK}/cugraph-ops.git
            GIT_TAG        ${PKG_PINNED_TAG}
            OPTIONS
                "BUILD_CUGRAPH_OPS_CPP_LIBRARY ON"
                "BUILD_CUGRAPH_OPS_CPP_TESTS OFF"
                "BUILD_CUGRAPH_OPS_PYTHON_LIBRARY ${PKG_BUILD_CUGRAPH_OPS_PYTHON_LIBRARY}"
    )

endfunction()

###
# Change pinned tag and fork here to test a commit in CI
#
# To use a locally-built cugraph-ops package, set the CMake variable
# `-D cugraph-ops_ROOT=/path/to/cugraph-ops/build`
#
# To use a local clone of cugraph-ops source and allow CMake to build
# cugraph-ops as part of building cugraph itself, set the CMake variable
# `-D CPM_cugraph-ops_SOURCE=/path/to/cugraph-ops`
###
find_and_configure_cugraph_ops(VERSION    ${CUGRAPH_MIN_VERSION_cugraph_ops}
                               FORK       rapidsai
                               PINNED_TAG branch-${CUGRAPH_BRANCH_VERSION_cugraph_ops}
                               # When PINNED_TAG above doesn't match cugraph,
                               # force local cugraph-ops clone in build directory
                               # even if it's already installed.
                               CLONE_ON_PIN     ON
                               BUILD_CUGRAPH_OPS_PYTHON_LIBRARY ${BUILD_CUGRAPH_OPS_PYTHON_LIBRARY}
                               )
