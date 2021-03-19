#!/bin/env python3

import sys
import os
from typing import List, Dict, Tuple

import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../ARAXQuery/")
from ARAX_query import ARAXQuery
from ARAX_response import ARAXResponse
import Expand.expand_utilities as eu
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../UI/OpenAPI/python-flask-server/")
from openapi_server.models.edge import Edge
from openapi_server.models.node import Node
from openapi_server.models.query_graph import QueryGraph


def _run_query_and_do_standard_testing(actions_list: List[str], kg_should_be_incomplete=False, debug=False,
                                       should_throw_error=False) -> Tuple[Dict[str, Dict[str, Node]], Dict[str, Dict[str, Edge]]]:
    # Run the query
    araxq = ARAXQuery()
    response = araxq.query({"operations": {"actions": actions_list}})
    message = araxq.message
    if response.status != 'OK':
        print(response.show(level=ARAXResponse.DEBUG))
    assert response.status == 'OK' or should_throw_error

    # Convert output knowledge graph to a dictionary format for faster processing (organized by QG IDs)
    dict_kg = eu.convert_standard_kg_to_qg_organized_kg(message.knowledge_graph)
    nodes_by_qg_id = dict_kg.nodes_by_qg_id
    edges_by_qg_id = dict_kg.edges_by_qg_id

    # Optionally print more detail
    if debug:
        _print_nodes(nodes_by_qg_id)
        _print_edges(edges_by_qg_id)
        _print_counts_by_qgid(nodes_by_qg_id, edges_by_qg_id)
        print(response.show(level=ARAXResponse.DEBUG))

    # Run standard testing (applies to every test case)
    assert eu.qg_is_fulfilled(message.query_graph, dict_kg, enforce_required_only=True) or kg_should_be_incomplete or should_throw_error
    _check_for_orphans(nodes_by_qg_id, edges_by_qg_id)
    _check_property_format(nodes_by_qg_id, edges_by_qg_id)
    _check_node_categories(message.knowledge_graph.nodes, message.query_graph)
    _check_counts_of_curie_qnodes(nodes_by_qg_id, message.query_graph)

    return nodes_by_qg_id, edges_by_qg_id


def _print_counts_by_qgid(nodes_by_qg_id: Dict[str, Dict[str, Node]], edges_by_qg_id: Dict[str, Dict[str, Edge]]):
    print(f"KG counts:")
    if nodes_by_qg_id or edges_by_qg_id:
        for qnode_key, corresponding_nodes in sorted(nodes_by_qg_id.items()):
            print(f"  {qnode_key}: {len(corresponding_nodes)}")
        for qedge_key, corresponding_edges in sorted(edges_by_qg_id.items()):
            print(f"  {qedge_key}: {len(corresponding_edges)}")
    else:
        print("  KG is empty")


def _print_nodes(nodes_by_qg_id: Dict[str, Dict[str, Node]]):
    for qnode_key, nodes in sorted(nodes_by_qg_id.items()):
        for node_key, node in sorted(nodes.items()):
            print(f"{qnode_key}: {node.category}, {node_key}, {node.name}, {node.qnode_keys}")


def _print_edges(edges_by_qg_id: Dict[str, Dict[str, Edge]]):
    for qedge_key, edges in sorted(edges_by_qg_id.items()):
        for edge_key, edge in sorted(edges.items()):
            print(f"{qedge_key}: {edge_key}, {edge.subject}--{edge.predicate}->{edge.object}, {edge.qedge_keys}")


def _print_node_counts_by_prefix(nodes_by_qg_id: Dict[str, Dict[str, Node]]):
    node_counts_by_prefix = dict()
    for qnode_key, nodes in nodes_by_qg_id.items():
        for node_key, node in nodes.items():
            prefix = node_key.split(':')[0]
            if prefix in node_counts_by_prefix.keys():
                node_counts_by_prefix[prefix] += 1
            else:
                node_counts_by_prefix[prefix] = 1
    print(node_counts_by_prefix)


def _check_for_orphans(nodes_by_qg_id: Dict[str, Dict[str, Node]], edges_by_qg_id: Dict[str, Dict[str, Edge]]):
    node_keys = set()
    node_keys_used_by_edges = set()
    for qnode_key, nodes in nodes_by_qg_id.items():
        for node_key, node in nodes.items():
            node_keys.add(node_key)
    for qedge_key, edges in edges_by_qg_id.items():
        for edge_key, edge in edges.items():
            node_keys_used_by_edges.add(edge.subject)
            node_keys_used_by_edges.add(edge.object)
    assert node_keys == node_keys_used_by_edges or len(node_keys_used_by_edges) == 0


def _check_property_format(nodes_by_qg_id: Dict[str, Dict[str, Node]], edges_by_qg_id: Dict[str, Dict[str, Edge]]):
    for qnode_key, nodes in nodes_by_qg_id.items():
        for node_key, node in nodes.items():
            assert node_key and isinstance(node_key, str)
            assert isinstance(node.name, str) or node.name is None
            assert node.qnode_keys and isinstance(node.qnode_keys, list)
            assert node.category and isinstance(node.category, list)
    for qedge_key, edges in edges_by_qg_id.items():
        for edge_key, edge in edges.items():
            assert edge_key and isinstance(edge_key, str)
            assert edge.qedge_keys and isinstance(edge.qedge_keys, list)
            assert edge.predicate and isinstance(edge.predicate, str)
            assert edge.subject and isinstance(edge.subject, str)
            assert edge.object and isinstance(edge.object, str)


def _check_node_categories(nodes: Dict[str, Node], query_graph: QueryGraph):
    for node in nodes.values():
        for qnode_key in node.qnode_keys:
            qnode = query_graph.nodes[qnode_key]
            if qnode.category:
                assert qnode.category in node.category  # Could have additional categories if it has multiple qnode keys


def _check_counts_of_curie_qnodes(nodes_by_qg_id: Dict[str, Dict[str, Node]], query_graph: QueryGraph):
    qnodes_with_single_curie = [qnode_key for qnode_key, qnode in query_graph.nodes.items() if qnode.id and isinstance(qnode.id, str)]
    for qnode_key in qnodes_with_single_curie:
        if qnode_key in nodes_by_qg_id:
            assert len(nodes_by_qg_id[qnode_key]) == 1
    qnodes_with_multiple_curies = [qnode_key for qnode_key, qnode in query_graph.nodes.items() if qnode.id and isinstance(qnode.id, list)]
    for qnode_key in qnodes_with_multiple_curies:
        qnode = query_graph.nodes[qnode_key]
        if qnode_key in nodes_by_qg_id:
            assert 1 <= len(nodes_by_qg_id[qnode_key]) <= len(qnode.id)


def test_one_hop_aceta():
    actions_list = [
        "add_qnode(id=CHEMBL.COMPOUND:CHEMBL112, key=n00)",
        "add_qnode(key=n01, category=biolink:Protein)",
        "add_qedge(subject=n00, object=n01, key=e00)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_one_hop_to_any_node():
    actions_list = [
        "add_qnode(id=REACT:R-HSA-2160456, key=n00)",
        "add_qnode(key=n01)",
        "add_qedge(subject=n00, object=n01, key=e00)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_one_hop_to_multiple_categories():
    actions_list = [
        "add_qnode(id=CHEMBL.COMPOUND:CHEMBL112, key=n00)",
        "add_qnode(key=n01, category=[biolink:Protein, biolink:Gene])",
        "add_qedge(subject=n00, object=n01, key=e00)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_one_hop_from_two_curies():
    actions_list = [
        "add_qnode(id=[CHEMBL.COMPOUND:CHEMBL112, CHEBI:5855], category=biolink:ChemicalSubstance, key=n00)",
        "add_qnode(key=n01, category=biolink:Protein)",
        "add_qedge(subject=n00, object=n01, key=e00, predicate=biolink:physically_interacts_with)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_one_hop_aceta_with_predicate():
    actions_list = [
        "add_qnode(id=CHEMBL.COMPOUND:CHEMBL112, key=n00)",
        "add_qnode(key=n01, category=biolink:Protein)",
        "add_qedge(subject=n00, object=n01, key=e00, predicate=physically_interacts_with)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_curie_to_curie():
    actions_list = [
        "add_qnode(id=CHEMBL.COMPOUND:CHEMBL25, key=n00)",
        "add_qnode(id=CHEMBL.COMPOUND:CHEMBL833, key=n01)",
        "add_qedge(subject=n00, object=n01, key=e00)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_many_curie_to_many_curie():
    actions_list = [
        "add_qnode(id=[CHEMBL.COMPOUND:CHEMBL25,CHEBI:5855], key=n00)",
        "add_qnode(id=CHEMBL.COMPOUND:CHEMBL112, key=n01)",
        "add_qedge(subject=n00, object=n01, key=e00)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_two_hop_smaller():
    actions_list = [
        "add_qnode(id=MONDO:0012496, key=n00)",
        "add_qnode(category=biolink:PhenotypicFeature, key=n01)",
        "add_qnode(category=biolink:Drug, key=n02)",
        "add_qedge(subject=n00, object=n01, key=e00)",
        "add_qedge(subject=n01, object=n02, key=e01)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_two_hop_multiple_predicates():
    actions_list = [
        "add_qnode(id=DOID:14330, key=n00)",
        "add_qnode(key=n01, category=biolink:Protein)",
        "add_qnode(key=n02, category=biolink:ChemicalSubstance)",
        "add_qedge(subject=n00, object=n01, key=e00)",
        "add_qedge(subject=n01, object=n02, predicate=[physically_interacts_with, molecularly_interacts_with], key=e01)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_two_hop_2():
    actions_list = [
        "add_qnode(id=DOID:9406, key=n00)",
        "add_qnode(key=n01, category=biolink:ChemicalSubstance)",
        "add_qnode(key=n02, category=biolink:Protein)",
        "add_qedge(subject=n00, object=n01, key=e00)",
        "add_qedge(subject=n01, object=n02, key=e01)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


def test_two_hop_massive():
    actions_list = [
        "add_qnode(name=dementia, key=n00)",
        "add_qnode(key=n01, category=biolink:PhenotypicFeature)",
        "add_qnode(key=n02, category=biolink:Disease)",
        "add_qedge(subject=n00, object=n01, key=e00)",
        "add_qedge(subject=n01, object=n02, key=e01)",
        "expand(kp=ARAX/KG2)",
        "return(message=true, store=false)",
    ]
    nodes_by_qg_id, edges_by_qg_id = _run_query_and_do_standard_testing(actions_list)


if __name__ == "__main__":
    pytest.main(['-v', 'test_query_speed.py'])
