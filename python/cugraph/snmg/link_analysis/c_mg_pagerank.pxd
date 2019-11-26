# Copyright (c) 2019, NVIDIA CORPORATION.
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

# cython: profile=False
# distutils: language = c++
# cython: embedsignature = True
# cython: language_level = 3

from cugraph.structure.c_graph cimport *
from libcpp cimport bool

cdef extern from "cugraph.h" namespace "cugraph":

    cdef void snmg_pagerank (
            gdf_column **src_col_ptrs, 
            gdf_column **dest_col_ptrs, 
            gdf_column *pr_col, 
            const size_t n_gpus, 
            const float damping_factor, 
            const int n_iter) except +
