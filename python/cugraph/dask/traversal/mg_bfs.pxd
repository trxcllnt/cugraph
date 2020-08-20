#
# Copyright (c) 2020, NVIDIA CORPORATION.
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
#

from cugraph.structure.graph_new cimport *
from libcpp cimport bool


cdef extern from "algorithms.hpp" namespace "cugraph":

    cdef void bfs[VT,ET,WT](
        const handle_t &handle,
        const GraphCSRView[VT,ET,WT] &graph,
        VT *distances,
        VT *predecessors,
        double *sp_counters,
        const VT start_vertex,
        bool directed) except +