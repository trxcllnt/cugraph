# Copyright (c) 2019-2020, NVIDIA CORPORATION.
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

import gc
import time
from collections import defaultdict
import pytest
import pandas as pd

import cugraph
from cugraph.tests import utils

# Temporarily suppress warnings till networkX fixes deprecation warnings
# (Using or importing the ABCs from 'collections' instead of from
# 'collections.abc' is deprecated, and in 3.8 it will stop working) for
# python 3.7.  Also, this import networkx needs to be relocated in the
# third-party group once this gets fixed.
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import networkx as nx


print("Networkx version : {} ".format(nx.__version__))


def networkx_weak_call(M):
    Gnx = nx.from_pandas_edgelist(
        M, source="0", target="1", create_using=nx.DiGraph()
    )

    # Weakly Connected components call:
    t1 = time.time()
    result = nx.weakly_connected_components(Gnx)
    t2 = time.time() - t1
    print("Time : " + str(t2))

    labels = sorted(result)
    return labels


def cugraph_weak_call(cu_M):
    G = cugraph.DiGraph()
    G.from_cudf_edgelist(cu_M, source="0", destination="1")
    t1 = time.time()
    df = cugraph.weakly_connected_components(G)
    t2 = time.time() - t1
    print("Time : " + str(t2))

    label_vertex_dict = defaultdict(list)
    for i in range(len(df)):
        label_vertex_dict[df["labels"][i]].append(df["vertices"][i])
    return label_vertex_dict


def networkx_strong_call(M):
    Gnx = nx.from_pandas_edgelist(
        M, source="0", target="1", create_using=nx.DiGraph()
    )

    t1 = time.time()
    result = nx.strongly_connected_components(Gnx)
    t2 = time.time() - t1
    print("Time : " + str(t2))

    labels = sorted(result)
    return labels


def cugraph_strong_call(cu_M):
    # cugraph Pagerank Call
    G = cugraph.DiGraph()
    G.from_cudf_edgelist(cu_M, source="0", destination="1")
    t1 = time.time()
    df = cugraph.strongly_connected_components(G)
    t2 = time.time() - t1
    print("Time : " + str(t2))

    label_vertex_dict = defaultdict(list)
    for i in range(len(df)):
        label_vertex_dict[df["labels"][i]].append(df["vertices"][i])
    return label_vertex_dict


def which_cluster_idx(_cluster, _find_vertex):
    idx = -1
    for i in range(len(_cluster)):
        if _find_vertex in _cluster[i]:
            idx = i
            break
    return idx


# Test all combinations of default/managed and pooled/non-pooled allocation
@pytest.mark.parametrize("graph_file", utils.DATASETS)
def test_weak_cc(graph_file):
    gc.collect()

    M = utils.read_csv_for_nx(graph_file)
    netx_labels = networkx_weak_call(M)

    cu_M = utils.read_csv_file(graph_file)
    cugraph_labels = cugraph_weak_call(cu_M)

    # NetX returns a list of components, each component being a
    # collection (set{}) of vertex indices;
    #
    # while cugraph returns a component label for each vertex;

    nx_n_components = len(netx_labels)
    cg_n_components = len(cugraph_labels)

    # Comapre number of components
    assert nx_n_components == cg_n_components

    lst_nx_components = sorted(netx_labels, key=len, reverse=True)
    lst_nx_components_lens = [len(c) for c in lst_nx_components]

    cugraph_vertex_lst = cugraph_labels.values()
    lst_cg_components = sorted(cugraph_vertex_lst, key=len, reverse=True)
    lst_cg_components_lens = [len(c) for c in lst_cg_components]

    # Compare lengths of each component
    assert lst_nx_components_lens == lst_cg_components_lens

    # Compare vertices of largest component
    nx_vertices = sorted(lst_nx_components[0])
    first_vert = nx_vertices[0]

    idx = which_cluster_idx(lst_cg_components, first_vert)
    assert idx != -1, "Check for Nx vertex in cuGraph results failed"

    cg_vertices = sorted(lst_cg_components[idx])

    assert nx_vertices == cg_vertices


# Test all combinations of default/managed and pooled/non-pooled allocation


@pytest.mark.parametrize("graph_file", utils.STRONGDATASETS)
def test_strong_cc(graph_file):
    gc.collect()

    M = utils.read_csv_for_nx(graph_file)
    netx_labels = networkx_strong_call(M)

    cu_M = utils.read_csv_file(graph_file)
    cugraph_labels = cugraph_strong_call(cu_M)

    # NetX returns a list of components, each component being a
    # collection (set{}) of vertex indices;
    #
    # while cugraph returns a component label for each vertex;

    nx_n_components = len(netx_labels)
    cg_n_components = len(cugraph_labels)

    # Comapre number of components found
    assert nx_n_components == cg_n_components

    lst_nx_components = sorted(netx_labels, key=len, reverse=True)
    lst_nx_components_lens = [len(c) for c in lst_nx_components]

    cugraph_vertex_lst = cugraph_labels.values()
    lst_cg_components = sorted(cugraph_vertex_lst, key=len, reverse=True)
    lst_cg_components_lens = [len(c) for c in lst_cg_components]

    # Compare lengths of each component
    assert lst_nx_components_lens == lst_cg_components_lens

    # Compare vertices of largest component
    # note that there might be more than one largest component
    nx_vertices = sorted(lst_nx_components[0])
    first_vert = nx_vertices[0]

    idx = which_cluster_idx(lst_cg_components, first_vert)
    assert idx != -1, "Check for Nx vertex in cuGraph results failed"

    cg_vertices = sorted(lst_cg_components[idx])
    assert nx_vertices == cg_vertices


@pytest.mark.parametrize("graph_file", utils.DATASETS)
def test_weak_cc_nx(graph_file):
    gc.collect()

    M = utils.read_csv_for_nx(graph_file)
    Gnx = nx.from_pandas_edgelist(
        M, source="0", target="1", create_using=nx.DiGraph()
    )

    nx_wcc = nx.weakly_connected_components(Gnx)
    nx_result = sorted(nx_wcc)

    cu_wcc = cugraph.weakly_connected_components(Gnx)
    pdf = pd.DataFrame.from_dict(cu_wcc, orient='index').reset_index()
    pdf.columns = ["vertex", "labels"]
    cu_result = pdf["labels"].nunique()

    assert len(nx_result) == cu_result


@pytest.mark.parametrize("graph_file", utils.STRONGDATASETS)
def test_strong_cc_nx(graph_file):
    gc.collect()

    M = utils.read_csv_for_nx(graph_file)
    Gnx = nx.from_pandas_edgelist(
        M, source="0", target="1", create_using=nx.DiGraph()
    )

    nx_scc = nx.strongly_connected_components(Gnx)
    nx_result = sorted(nx_scc)

    cu_scc = cugraph.strongly_connected_components(Gnx)

    pdf = pd.DataFrame.from_dict(cu_scc, orient='index').reset_index()
    pdf.columns = ["vertex", "labels"]
    cu_result = pdf["labels"].nunique()

    assert len(nx_result) == cu_result
