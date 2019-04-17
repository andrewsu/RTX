#!/usr/bin/python3
from __future__ import print_function
import sys
def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

import os
import argparse
import json
import sys
import time
import warnings
import networkx as nx

# PyCharm doesn't play well with relative imports + python console + terminal
try:
    from code.reasoningtool import ReasoningUtilities as RU
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import ReasoningUtilities as RU

import FormatOutput
import CustomExceptions

#### Import the Translator API classes
from swagger_server.models.message import Message
from swagger_server.models.result import Result
from swagger_server.models.knowledge_graph import KnowledgeGraph
from swagger_server.models.node import Node
from swagger_server.models.edge import Edge
from swagger_server.models.query_graph import QueryGraph
from swagger_server.models.q_node import QNode
from swagger_server.models.q_edge import QEdge
from swagger_server.models.edge_attribute import EdgeAttribute
from swagger_server.models.node_attribute import NodeAttribute

from KGNodeIndex import KGNodeIndex


class QueryGraphReasoner:

    def __init__(self):
        None


    def answer(self, query_graph, use_json=False):
        """
        Answer a question based on the input query_graph:
        :param query_graph: QueryGraph object
        :param use_json: If the answer should be in Translator standardized API output format
        :return: Result of the query in simplified or API format
        """

        #### Interpret the query_graph object to create a cypher query and encode the result in a response
        query_gen = RU.get_cypher_from_question_graph({'question_graph':query_graph})
        answer_graph_cypher = query_gen.cypher_query_answer_map()
        knowledge_graph_cypher = query_gen.cypher_query_knowledge_graph()
        
        res = RU.session.run(answer_graph_cypher)
        answer_graph_list = res.data()
        
        res = RU.session.run(knowledge_graph_cypher)
        knowledge_graph_dict = res.data()[0]

        # Need to convert the answer graphs and knowledge graph 
        # into formatted responses 




        #### Dang. I don't know how to do that, so instead do something super simple: describe qnode[0]
        # See Q3Solution.py and SimilarityQuestionSolution.py for more insight into generating 0.9.0


        #####################################################
        # This is the old code but I didn't want to delete it

    #### Pull out the first node and look it up in the KGNodeIndex
        
        """
        entity = query_graph.nodes[0].curie
        eprint("Looking up '%s' in KgNodeIndex" % entity)
        kgNodeIndex = KGNodeIndex()
        curies = kgNodeIndex.get_curies(entity)

        #### If not in the KG, then return no information
        if not curies:
            if not use_json:
                return None
            else:
                error_code = "TermNotFound"
                error_message = "This concept is not in our knowledge graph"
                response = FormatOutput.FormatResponse(0)
                response.add_error_message(error_code, error_message)
                return response.message

        # Get label/kind of node the source is
        eprint("Getting properties for '%s'" % curies[0])
        properties = RU.get_node_properties(curies[0])
        eprint("Properties are:")
        eprint(properties)

        #### By default, return the results just as a plain simple list of data structures
        if not use_json:
            return properties

        #### Or, if requested, format the output as the standardized API output format
        else:
            #### Create a stub Message object
            response = FormatOutput.FormatResponse(0)
            response.message.table_column_names = [ "id", "type", "name", "description", "uri" ]
            response.message.code_description = None

            #### Include the original query_graph in the envelope
            response.message.query_graph = query_graph

            #### Create a Node object and fill it
            node1 = Node()
            node1.id = properties["id"]
            node1.uri = properties["uri"]
            node1.type = [ properties["category"] ]
            node1.name = properties["name"]
            node1.description = properties["description"]

            #### Create the first result (potential answer)
            result1 = Result()
            result1.id = "http://rtx.ncats.io/api/v1/result/0000"
            result1.description = "The term %s is in our knowledge graph and is defined as %s" % ( properties["name"],properties["description"] )
            result1.confidence = 1.0
            result1.essence = properties["name"]
            result1.essence_type = properties["category"]
            node_types = ",".join(node1.type)
            result1.row_data = [ node1.id, node_types, node1.name, node1.description, node1.uri ]

            #### Create a KnowledgeGraph object and put the list of nodes and edges into it
            result_graph = KnowledgeGraph()
            result_graph.nodes = [ node1 ]

            #### Put the ResultGraph into the first result (potential answer)
            #This is legal but deprecated and discouraged in v0.9.1
            #result1.result_graph = result_graph

            #### Put the first result (potential answer) into the message
            results = [ result1 ]
            response.message.results = results

            #### Also put the union of all result_graph components into the top Message KnowledgeGraph
            #### Normally the knowledge_graph will be much more complex than this, but take a shortcut for this single-node result
            response.message.knowledge_graph = result_graph

            #### Also manufacture a query_graph post hoc
            qnode1 = QNode()
            qnode1.node_id = "n00"
            qnode1.curie = properties["id"]
            qnode1.type = None

            #### Create the corresponding knowledge_map for this result
            node_bindings = { "n00": [ properties["id"] ] }
            result1.node_bindings = node_bindings
            result1.edge_bindings = []

            return(response.message)
        """



    def from_dict(self,query_graph_dict):
        query_graph = QueryGraph()
        query_graph.nodes = []
        query_graph.edges = []
        if "nodes" in query_graph_dict:
            for node in query_graph_dict["nodes"]:
                qnode = QNode().from_dict(node)
                query_graph.nodes.append(qnode)
        if "edges" in query_graph_dict:
            for edge in query_graph_dict["edges"]:
                qedge = QEdge().from_dict(edge)
                query_graph.edges.append(qedge)
        return query_graph


    def describe(self):
        output = "Answers questions based on an input QueryGraph object\n"
        return output


# Tests
def tests():
    result = test1_2nodes()
    return(result)


# Test 1
def test1_2nodes():
    q = QueryGraphReasoner()
    query_graph_json_stream = '''{
    "edges": [
      {
        "edge_id": "e00",
        "source_id": "n00",
        "target_id": "n01",
        "type": "physically_interacts_with"
      }
    ],
    "nodes": [
      {
        "curie": "CHEMBL.COMPOUND:CHEMBL112",
        "node_id": "n00",
        "type": "chemical_substance"
      },
      {
        "curie": null,
        "is_set": null,
        "node_id": "n01",
        "type": "protein"
      }
    ]
    }'''

    query_graph_dict = json.loads(query_graph_json_stream)
    query_graph = QueryGraphReasoner().from_dict(query_graph_dict)
    result = q.answer(query_graph, use_json=True)
    return(result)


def main():
    parser = argparse.ArgumentParser(description="Answers questions based on an input QueryGraph object'.",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input_file', type=str, help="input file name of JSON of a serialized QueryGraph", default=False)
    parser.add_argument('-j', '--json', action='store_true', help='Flag specifying that results should be printed in Translator standard format (to stdout)', default=False)
    parser.add_argument('-d', '--describe', action='store_true', help="Describe what kinds of questions this answers.", default=False)
    parser.add_argument('-t', '--test', action='store_true', help="Run tests", default=False)

    # Parse and check args
    args = parser.parse_args()
    input_file = args.input_file
    use_json = args.json

    # Initialize the question class
    q = QueryGraphReasoner()

    if args.describe:
        result = q.describe()
        print(result)
        return()

    if args.test:
        result = tests()
        print(result)

    else:
        with open(input_file, 'r') as infile:
          query_graph_json_stream = infile.read()
        query_graph_dict = json.loads(query_graph_json_stream)
        query_graph = QueryGraphReasoner().from_dict(query_graph_dict)
        result = q.answer(query_graph, use_json=use_json)
        if use_json:
            result.print()
        else:
            print(result)


if __name__ == "__main__":
    main()
