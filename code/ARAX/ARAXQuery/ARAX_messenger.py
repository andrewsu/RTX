#!/bin/env python3
import sys
def eprint(*args, **kwargs): print(*args, file=sys.stderr, **kwargs)

import os
import json
import ast
import re
from datetime import datetime
import numpy as np
import requests

from ARAX_response import ARAXResponse
from query_graph_info import QueryGraphInfo
from knowledge_graph_info import KnowledgeGraphInfo

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../")
from RTXConfiguration import RTXConfiguration

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../UI/OpenAPI/python-flask-server/")
from openapi_server.models.response import Response
from openapi_server.models.message import Message
from openapi_server.models.knowledge_graph import KnowledgeGraph
from openapi_server.models.query_graph import QueryGraph
from openapi_server.models.q_node import QNode
from openapi_server.models.q_edge import QEdge

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../NodeSynonymizer")
from node_synonymizer import NodeSynonymizer


class ARAXMessenger:

    #### Constructor
    def __init__(self):
        self.response = None
        self.envelope = None
        self.message = None
        self.parameters = None

    def describe_me(self):
        """
        Self-documentation method for internal use that returns the available actions and what they can do
        :return: A list of allowable actions supported by this class
        :rtype: list
        """
        description_list = []
        description_list.append(self.create_envelope(describe=True))
        description_list.append(self.add_qnode(0,0,describe=True))
        description_list.append(self.add_qedge(0,0,describe=True))
        return description_list


    # #### Create a fresh ARAXResponse object as an envelple and fill with defaults
    def create_envelope(self, response, describe=False):
        """
        Creates a basic empty ARAXResponse object with basic boilerplate metadata
        :return: ARAXResponse object with execution information and the new message object inside the data envelope
        :rtype: ARAXResponse
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'create_envelope()',
            'description': """The `create_envelope` command creates a basic empty Response object with basic boilerplate metadata
                such as reasoner_id, schema_version, etc. filled in. This DSL command takes no arguments. This command is not explicitly
                necessary, as it is called implicitly when needed. e.g. If a DSL program begins with add_qnode(), the
                create_envelope() will be executed automatically if there is not yet a ARAXResponse. If there is already ARAXResponse in memory,
                then this command will destroy the previous one (in memory) and begin a new envelope.""",
            'parameters': {
            }
        }

        if describe:
            return command_definition


        #### Store the passed response object
        self.response = response
    
        #### Create the top-level Response object called an envelope
        response.info("Creating an empty template ARAX Envelope")
        envelope = Response()
        response.envelope = envelope
        self.envelope = envelope

        # Create a Message object and place it in the envelope
        message = Message()
        response.envelope.message = message
        self.message = message

        #### Fill it with default information
        envelope.id = None
        envelope.type = "translator_reasoner_response"
        envelope.reasoner_id = "ARAX"
        envelope.tool_version = RTXConfiguration().version
        envelope.schema_version = "1.0.0"
        envelope.status = "OK"
        envelope.description = "Created empty template response"
        envelope.context = "https://raw.githubusercontent.com/biolink/biolink-model/master/context.jsonld"
        envelope.logs = response.messages
        envelope.datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		#### Create an empty master knowledge graph
        message.knowledge_graph = KnowledgeGraph()
        message.knowledge_graph.nodes = {}
        message.knowledge_graph.edges = {}

		#### Create an empty query graph
        message.query_graph = QueryGraph()
        message.query_graph.nodes = {}
        message.query_graph.edges = {}

        #### Create empty results
        message.results = []

        #### Return the response
        response.data['envelope'] = envelope
        return response


    ###############################################################################################
    # #### Add a new QNode
    def add_qnode(self, response, input_parameters, describe=False):
        """
        Adds a new QNode object to the QueryGraph inside the Message object
        :return: ARAXResponse object with execution information
        :rtype: ARAXResponse
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'add_qnode()',
            'description': """The `add_qnode` method adds an additional QNode to the QueryGraph in the Message object. Currently
                when a id or name is specified, this method will only return success if a matching node is found in the KG1/KG2 KGNodeIndex.""",
            'parameters': {
                'key': { 
                    'is_required': False,
                    'examples': [ 'n00', 'n01' ],
                    'default': '',
                    'type': 'string',
                    'description': """Any string that is unique among all QNode id fields, with recommended format n00, n01, n02, etc.
                        If no value is provided, autoincrementing values beginning for n00 are used.""",
                    },
                'id': {
                    'is_required': False,
                    'examples': [ 'DOID:9281', '[UniProtKB:P12345,UniProtKB:Q54321]' ],
                    'type': 'string',
                    'description': 'Any compact URI (CURIE) (e.g. DOID:9281) (May also be a list like [UniProtKB:P12345,UniProtKB:Q54321])',
                    },
                'name': {
                    'is_required': False,
                    'examples': [ 'hypertension', 'insulin' ],
                    'type': 'string',
                    'description': 'Any name of a bioentity that will be resolved into a CURIE if possible or result in an error if not (e.g. hypertension, insulin)',
                    },
                'category': {
                    'is_required': False,
                    'examples': [ 'protein', 'chemical_substance', 'disease' ],
                    'type': 'ARAXnode',
                    'description': 'Any valid Translator bioentity category (e.g. protein, chemical_substance, disease)',
                    },
                'is_set': {
                    'is_required': False,
                    'enum': [ "true", "false", "True", "False", "t", "f", "T", "F" ],
                    'examples': [ 'true', 'false' ],
                    'type': 'boolean',
                    'description': 'If set to true, this QNode represents a set of nodes that are all in common between the two other linked QNodes (assumed to be false if not specified or value is not recognized as true/t case insensitive)'
                    },
                'option_group_id': {
                    'is_required': False,
                    'examples': [ '1', 'a', 'b2', 'option'],
                    'type': 'string',
                    'description': 'A group identifier indicating a group of nodes and edges should either all be included or all excluded. An optional match for all elements in this group. If not included Node will be treated as required.'
                    },
            }
        }

        if describe:
            return command_definition

        #### Extract the message to work on
        message = response.envelope.message

        #### Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        #### Define a complete set of allowed parameters and their defaults
        parameters = {
            'key': None,
            'id': None,
            'name': None,
            'category': None,
            'is_set': None,
            'option_group_id': None,
        }

        #### Loop through the input_parameters and override the defaults and make sure they are allowed
        for key,value in input_parameters.items():
            if key not in parameters:
                response.error(f"Supplied parameter {key} is not permitted", error_code="UnknownParameter")
            else:
                parameters[key] = value

        #### Check for option_group_id and is_set:
        if parameters['option_group_id'] is not None and parameters['curie'] is None and parameters['name'] is None:
            if parameters['is_set'] is None:
                parameters['is_set'] = 'true'
                response.warning(f"An 'option_group_id' was set to {parameters['option_group_id']}, but 'is_set' was not an included parameter. It must be true when an 'option_group_id' is given, so automatically setting to true. Avoid this warning by explictly setting to true.")
            elif not ( parameters['is_set'].lower() == 'true' or parameters['is_set'].lower() == 't' ):
                response.error(f"When an 'option_group_id' is given 'is_set' must be set to true. However, supplied input for parameter 'is_set' was {parameters['is_set']}.", error_code="InputMismatch")


        #### Return if any of the parameters generated an error (showing not just the first one)
        if response.status != 'OK':
            return response


        #### Now apply the filters. Order of operations is probably quite important
        #### Scalar value filters probably come first like minimum_confidence, then complex logic filters
        #### based on edge or node properties, and then finally maximum_results
        response.info(f"Adding a QueryNode to Message with input parameters {parameters}")

        #### Make sure there's a query_graph already here
        if message.query_graph is None:
            message.query_graph = QueryGraph()
            message.query_graph.nodes = {}
            message.query_graph.edges = {}
        if message.query_graph.nodes is None:
            message.query_graph.nodes = {}

        #### Set up the NodeSynonymizer to find curies and names
        synonymizer = NodeSynonymizer()

        # Create the QNode and set the id
        qnode = QNode()
        if parameters['key'] is not None:
            key = parameters['key']
        else:
            key = self.__get_next_free_node_id()

        if parameters['option_group_id'] is not None:
            qnode.option_group_id = parameters['option_group_id']
        
        # Set the is_set parameter to what the user selected
        if parameters['is_set'] is not None:
            qnode.is_set = ( parameters['is_set'].lower() == 'true' or parameters['is_set'].lower() == 't' )

        #### If the id is specified, try to find that
        if parameters['id'] is not None:

            # If the id is a scalar then treat it here as a list of one
            if isinstance(parameters['id'], str):
                id_list = [ parameters['id'] ]
                is_id_a_list = False
                if parameters['is_set'] is not None and qnode.is_set is True:
                    response.error(f"Specified id '{parameters['id']}' is a scalar, but is_set=true, which doesn't make sense", error_code="IdScalarButIsSetTrue")
                    return response

            # Or else set it up as a list
            elif isinstance(parameters['id'], list):
                id_list = parameters['id']
                is_id_a_list = True
                qnode.id = []
                if parameters['is_set'] is None:
                    response.warning(f"Specified id '{parameters['id']}' is a list, but is_set was not set to true. It must be true in this context, so automatically setting to true. Avoid this warning by explictly setting to true.")
                    qnode.is_set = True
                else:
                    if qnode.is_set == False:
                        response.warning(f"Specified id '{parameters['id']}' is a list, but is_set=false, which doesn't make sense, so automatically setting to true. Avoid this warning by explictly setting to true.")
                        qnode.is_set = True

            # Or if it's neither a list or a string, then error out. This cannot be handled at present
            else:
                response.error(f"Specified id '{parameters['id']}' is neither a string nor a list. This cannot to handled", error_code="IdNotListOrScalar")
                return response

            # Loop over the available ids and create the list
            for id in id_list:
                response.debug(f"Looking up id {id} in NodeSynonymizer")
                synonymizer_results = synonymizer.get_canonical_curies(curies=[id])

                # If nothing was found, we won't bail out, but rather just issue a warning that this id is suspect
                if synonymizer_results[id] is None:
                    response.warning(f"A node with id {id} is not in our knowledge graph KG2, but will continue with it")
                    if is_id_a_list:
                        qnode.id.append(id)
                    else:
                        qnode.id = id

                # And if it is found, keep the same id but report the preferred id
                else:

                    response.info(f"id {id} is found. Adding it to the qnode")
                    if is_id_a_list:
                        qnode.id.append(id)
                    else:
                        qnode.id = id

                if 'category' in parameters and parameters['category'] is not None:
                    if isinstance(parameters['category'], str):
                        qnode.category = parameters['category']
                    else:
                        qnode.category = parameters['category'][0]

            message.query_graph.nodes[key] = qnode
            return response

        #### If the name is specified, try to find that
        if parameters['name'] is not None:
            name = parameters['name']
            response.debug(f"Looking up id for name '{name}' in NodeSynonymizer")
            synonymizer_results = synonymizer.get_canonical_curies(curies=[name], names=[name])

            if synonymizer_results[name] is None:
                response.error(f"A node with name '{name}' is not in our knowledge graph", error_code="UnresolvableNodeName")
                return response
 
            qnode.id = synonymizer_results[name]['preferred_curie']
            response.info(f"Creating QueryNode with id '{qnode.id}' for name '{name}'")
            if parameters['category'] is not None:
                qnode.category = parameters['category']
            message.query_graph.nodes[key] = qnode
            return response

        #### If the category is specified, just add that category. There should be checking that it is legal. FIXME
        if parameters['category'] is not None:
            qnode.category = parameters['category']
            if parameters['is_set'] is not None:
                qnode.is_set = (parameters['is_set'].lower() == 'true')
            message.query_graph.nodes[key] = qnode
            return response

        #### If we get here, it means that all three main parameters are null. Just a generic node with no category or anything. This is okay.
        message.query_graph.nodes[key] = qnode
        return response


    ###############################################################################################
    #### Get the next free node id like nXX where XX is a zero-padded integer starting with 00
    def __get_next_free_node_id(self):

        #### Set up local references to the message and verify the query_graph nodes
        message = self.envelope.message
        if message.query_graph is None:
            message.query_graph = QueryGraph()
            message.query_graph.nodes = []
            message.query_graph.edges = []
        if message.query_graph.nodes is None:
            message.query_graph.nodes = []
        qnodes = message.query_graph.nodes

        #### Find the first unused id
        index = 0
        while 1:
            pad = '0'
            if index > 9:
                pad = ''
            potential_node_id = f"n{pad}{str(index)}"
            if potential_node_id not in qnodes:
                return potential_node_id
            index += 1


    ###############################################################################################
    #### Add a new QEdge
    def add_qedge(self, response, input_parameters, describe=False):
        """
        Adds a new QEdge object to the QueryGraph inside the Message object
        :return: ARAXResponse object with execution information
        :rtype: ARAXResponse
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'add_qedge()',
            'description': """The `add_qedge` command adds an additional QEdge to the QueryGraph in the Message object. Currently
                subject and object QNodes must already be present in the QueryGraph. The specified type is not currently checked that it is a
                valid Translator/BioLink relationship type, but it should be.""",
            'parameters': {
                'id': { 
                    'is_required': False,
                    'examples': [ 'e00', 'e01' ],
                    'default': '',
                    'type': 'string',
                    'description': """Any string that is unique among all QEdge id fields, with recommended format e00, e01, e02, etc.
                        If no value is provided, autoincrementing values beginning for e00 are used.""",
                    },
                'subject': {
                    'is_required': True,
                    'examples': [ 'n00', 'n01' ],
                    'type': 'string',
                    'description': 'id of the source QNode already present in the QueryGraph (e.g. n00, n01)',
                    },
                'object': {
                    'is_required': True,
                    'examples': [ 'n01', 'n02' ],
                    'type': 'string',
                    'description': 'id of the target QNode already present in the QueryGraph (e.g. n01, n02)',
                    },
                'predicate': {
                    'is_required': False,
                    'examples': [ 'protein', 'physically_interacts_with', 'participates_in' ],
                    'type': 'ARAXedge',
                    'description': 'Any valid Translator/BioLink relationship predicate (e.g. physically_interacts_with, participates_in)',
                    },
                'option_group_id': {
                    'is_required': False,
                    'examples': [ '1', 'a', 'b2', 'option'],
                    'type': 'string',
                    'description': 'A group identifier indicating a group of nodes and edges should either all be included or all excluded. An optional match for all elements in this group. If not included Node will be treated as required.'
                    },
                'exclude': {
                    'is_required': False,
                    'enum': [ 'true', 'false' ],
                    'examples': [ 'true', 'false' ],
                    'type': 'boolean',
                    'description': 'If set to true, results with this node will be excluded. If set to false or not included nodes will be treated as part of a normal query.'
                    },
            }
        }

        if describe:
            return command_definition


        #### Extract the message to work on
        message = response.envelope.message

        #### Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        #### Define a complete set of allowed parameters and their defaults
        parameters = {
            'id': None,
            'subject': None,
            'object': None,
            'predicate': None,
            'option_group_id': None,
            'exclude': None,
        }

        #### Loop through the input_parameters and override the defaults and make sure they are allowed
        for key,value in input_parameters.items():
            if key not in parameters:
                response.error(f"Supplied parameter {key} is not permitted", error_code="UnknownParameter")
            else:
                parameters[key] = value
        #### Return if any of the parameters generated an error (showing not just the first one)
        if response.status != 'OK':
            return response

        #### Store these final parameters for convenience
        response.data['parameters'] = parameters
        self.parameters = parameters


        #### Now apply the filters. Order of operations is probably quite important
        #### Scalar value filters probably come first like minimum_confidence, then complex logic filters
        #### based on edge or node properties, and then finally maximum_results
        response.info(f"Adding a QueryEdge to Message with parameters {parameters}")

        #### Make sure there's a query_graph already here
        if message.query_graph is None:
            message.query_graph = QueryGraph()
            message.query_graph.nodes = {}
            message.query_graph.edges = {}
        if message.query_graph.edges is None:
            message.query_graph.edges = {}

        #### Create a QEdge
        qedge = QEdge()
        if parameters['id'] is not None:
            key = parameters['id']
        else:
            key = self.__get_next_free_edge_id()

        #### Get the list of available node_ids
        qnodes = message.query_graph.nodes

        #### Add the subject
        if parameters['subject'] is not None:
            if parameters['subject'] not in qnodes:
                response.error(f"While trying to add QEdge, there is no QNode with id {parameters['subject']}", error_code="UnknownSourceId")
                return response
            qedge.subject = parameters['subject']
        else:
            response.error(f"While trying to add QEdge, subject is a required parameter", error_code="MissingSourceId")
            return response

        #### Add the object
        if parameters['object'] is not None:
            if parameters['object'] not in qnodes:
                response.error(f"While trying to add QEdge, there is no QNode with id {parameters['object']}", error_code="UnknownTargetId")
                return response
            qedge.object = parameters['object']
        else:
            response.error(f"While trying to add QEdge, object is a required parameter", error_code="MissingTargetId")
            return response

        #### Add the predicate if any. Need to verify it's an allowed predicate. FIXME
        if parameters['predicate'] is not None:
            qedge.predicate = parameters['predicate']

        if parameters['exclude'] is not None:
            if parameters['exclude'] in {'t', 'T', 'true', 'True'}:
                qedge.exclude = True
            elif parameters['exclude'] in {'f', 'F', 'false', 'False'}:
                qedge.exclude = False
            elif parameters['exclude'] not in {True, False}:
                response.error(f"Supplied input, {parameters['exclude']}, for the 'exclude' parameter is not valid. Acceptable inputs are t, T, f, F, true, True, false, and False.", error_code="UnknownInput")
        else:
            qedge.exclude = False

        if parameters['option_group_id'] is not None:
            qedge.option_group_id = parameters['option_group_id']

        #### Add it to the query_graph edge list
        message.query_graph.edges[key] = qedge

        #### Return the response
        return response


    ###############################################################################################
    #### Get the next free edge id like eXX where XX is a zero-padded integer starting with 00
    def __get_next_free_edge_id(self):

        #### Set up local references to the message and verify the query_graph nodes
        message = self.envelope.message
        if message.query_graph is None:
            message.query_graph = QueryGraph()
            message.query_graph.nodes = {}
            message.query_graph.edges = {}
        if message.query_graph.edges is None:
            message.query_graph.edges = {}
        qedges = message.query_graph.edges

        #### Find the first unused id
        index = 0
        while 1:
            pad = '0'
            if index > 9:
                pad = ''
            potential_edge_id = f"e{pad}{str(index)}"
            if potential_edge_id not in qedges:
                return potential_edge_id
            index += 1


    ###############################################################################################
    #### Remove a QEdge
    def remove_qedge(self, response, input_parameters, describe=False):
        """
        Removes a QEdge object in the QueryGraph inside the Message object
        :return: ARAXResponse object with execution information
        :rtype: ARAXResponse
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'remove_qedge()',
            'description': """The `remove_qedge` command removes a QEdge from the QueryGraph in the Message object. Currently
                the only way to specify the desired edge to remove it by its id.""",
            'parameters': {
                'id': { 
                    'is_required': True,
                    'examples': [ 'e00', 'e01' ],
                    'default': '',
                    'type': 'string',
                    'description': """The id of the QEdge to remove, such as e00, e01, e02, etc.""",
                    },
           }
        }

        if describe:
            return command_definition


        #### Extract the message to work on
        message = response.envelope.message

        #### Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        #### Define a complete set of allowed parameters and their defaults
        parameters = {
            'id': None,
        }

        #### Loop through the input_parameters and override the defaults and make sure they are allowed
        for key,value in input_parameters.items():
            if key not in parameters:
                response.error(f"Supplied parameter {key} is not permitted", error_code="UnknownParameter")
            else:
                parameters[key] = value
        #### Return if any of the parameters generated an error (showing not just the first one)
        if response.status != 'OK':
            return response

        #### Store these final parameters for convenience
        response.data['parameters'] = parameters
        self.parameters = parameters


        #### Now apply the filters. Order of operations is probably quite important
        #### Scalar value filters probably come first like minimum_confidence, then complex logic filters
        #### based on edge or node properties, and then finally maximum_results
        response.info(f"Removing QueryEdge with parameters {parameters}")

        #### Make sure there's a query_graph already here
        if message.query_graph is None:
            response.error(f"While trying to remove a QEdge, there is no QueryGraph", error_code="QueryGraphNotFound")
            return response
        if message.query_graph.edges is None:
            response.error(f"While trying to remove a QEdge, there are no edges in the QueryGraph", error_code="NoEdgesFound")
            return response

        key = parameters['id']
        if key in message.query_graph.edges:
            del message.query_graph.edges[key]
        else:
            response.error(f"While trying to remove a QEdge, no QEdge with id {key} was found", error_code="QEdgeIdNotfound")
            return response

        #### Return the response
        return response


    ###############################################################################################
    #### Fetch a message by its URI, return the message
    def fetch_message(self, message_uri):

        result = self.apply_fetch_message(self.message, { 'uri': message_uri })
        return self.message


    #### Fetch a message by its URI, return a full response
    def apply_fetch_message(self, message, input_parameters, describe=False):
        """
        Adds a new QEdge object to the QueryGraph inside the Message object
        :return: ARAXResponse object with execution information
        :rtype: ARAXResponse
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'fetch_message()',
            'description': """The `fetch_message` command fetches a remote Message by its id and can then allow further processing on it.""",
            'parameters': {
                'id': { 
                    'is_required': True,
                    'examples': [ 'https://arax.ncats.io/api/rtx/v1/message/3164' ],
                    'default': '',
                    'type': 'string',
                    'description': """A URL/URI that identifies the Message to be fetched""",
                    },
            }
        }

        if describe:
            return command_definition


        #### Define a default response
        response = ARAXResponse()
        self.response = response
        self.message = message

        #### Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        #### Define a complete set of allowed parameters and their defaults
        parameters = {
            'uri': None,
        }

        #### Loop through the input_parameters and override the defaults and make sure they are allowed
        for key,value in input_parameters.items():
            if key not in parameters:
                response.error(f"Supplied parameter {key} is not permitted", error_code="UnknownParameter")
            else:
                parameters[key] = value
        #### Return if any of the parameters generated an error (showing not just the first one)
        if response.status != 'OK':
            return response

        #### Store these final parameters for convenience
        response.data['parameters'] = parameters
        self.parameters = parameters


        #### Basic checks on arguments
        message_uri = input_parameters['uri']
        if not isinstance(message_uri, str):
            response.error("Provided parameter is not a string", error_code="ParameterNotString")
            return response

        response.info(f"Fetching Message via GET to '{message_uri}'")
        response_content = requests.get(message_uri, headers={'accept': 'application/json'})
        status_code = response_content.status_code

        if status_code != 200:
            response.error(f"GET to '{message_uri}' returned HTTP code {status_code} and content '{response_content.content}'", error_code="GETFailed")
            response.error(f"GET to '{message_uri}' returned HTTP code {status_code}", error_code="GETFailed")
            return response

        #### Unpack the response content into a dict and dump
        try:
            response_dict = response_content.json()
            message = self.from_dict(response_dict)
        except:
            response.error(f"Error converting response from '{message_uri}' to objects from content", error_code="UnableToParseContent")
            return response

        #### Store the decoded message and return response
        self.message = message
        n_results = 0
        n_qg_nodes = 0
        n_kg_nodes = 0
        if message.results is not None and isinstance(message.results,list):
            n_results = len(message.results)
        if message.query_graph is not None and isinstance(message.query_graph,QueryGraph) and isinstance(message.query_graph.nodes,list):
            n_qg_nodes = len(message.query_graph.nodes)
        if message.knowledge_graph is not None and isinstance(message.knowledge_graph,KnowledgeGraph) and isinstance(message.knowledge_graph.nodes,list):
            n_kg_nodes = len(message.knowledge_graph.nodes)
        response.info(f"Retreived Message with {n_qg_nodes} QueryGraph nodes, {n_kg_nodes} KnowledgeGraph nodes, and {n_results} results")
        return response


    #### Convert a Message as a dict to a Message as objects
    def from_dict(self, message):

        if str(message.__class__) != "<class 'openapi_server.models.message.Message'>":
            message = Message().from_dict(message)

        # When tested from ARAX_query_graph_interpreter, none of this subsequent stuff is needed

        #print(message.query_graph.__class__)
        #message.query_graph = QueryGraph().from_dict(message.query_graph)
        #message.knowledge_graph = KnowledgeGraph().from_dict(message.knowledge_graph)

        #### This is an unfortunate hack that fixes qnode.curie entries
        #### Officially a curie can be a str or a list. But Swagger 2.0 only permits one type and we set it to str
        #### so when it gets converted from_dict, the list gets converted to a str because that's its type
        #### Here we force it back. This should no longer be needed when we are properly on OpenAPI 3.0
        #if message.query_graph is not None and message.query_graph.nodes is not None:
        #    for qnode_key,qnode in message.query_graph.nodes.items():
        #        print(qnode.__class__)
                #if qnode.id is not None and isinstance(qnode.id,str):
                #    if qnode.id[0:2] == "['":
                #        try:
                #            qnode.id = ast.literal_eval(qnode.id)
                #        except:
                #            pass

        #new_nodes = []
        #for qnode in message.query_graph.nodes:
        #    print(type(qnode))
        #    new_nodes.append(QNode().from_dict(qnode))
        #message.query_graph.nodes = new_nodes
        #for qedge in message.query_graph.edges:
        #    new_edges.append(QEdge().from_dict(qedge))
        #message.query_graph.edges = new_edges

        #if message.results is not None:
        #    for result in message.results:
        #        if result.result_graph is not None:
        #            #eprint(str(result.result_graph.__class__))
        #            if str(result.result_graph.__class__) != "<class 'openapi_server.models.knowledge_graph.KnowledgeGraph'>":
        #                result.result_graph = KnowledgeGraph().from_dict(result.result_graph)

        return message



##########################################################################################
def main():

    #### Create a response object that contains the final results of our efforts
    response = ARAXResponse()
    #### Setting the output to STDERR will write out information as we go along in addition to supplying it with the response
    #ARAXResponse.output = 'STDERR'

    #### Create the ARAXMessenger
    messenger = ARAXMessenger()

    #### Test fetch_message()
    if False:
        messenger = ARAXMessenger()
        result = messenger.apply_fetch_message(messenger.message, { 'uri': 'https://arax.ncats.io/api/rtx/v1/message/3000'} )
        response.merge(result)
        if result.status != 'OK':
            print(response.show(level=ARAXResponse.DEBUG))
            return response
        message = messenger.message
        print(response.show(level=ARAXResponse.DEBUG))
        #print(json.dumps(message.to_dict(),sort_keys=True,indent=2))
        return

    #### Create an envelope in which to work
    messenger.create_envelope(response)
    if response.status != 'OK':
        print(response.show(level=ARAXResponse.DEBUG))
        return response
    message = response.envelope.message

    #### Some qnode examples
    parameters_sets = [
        { 'id': 'DOID:9281'},
        { 'id': 'Orphanet:673'},
        { 'name': 'acetaminophen', 'category': 'biolink:ChemicalSubstance' },
        { 'id': 'NCIT:C198'},
        { 'id': 'UMLS:C4710278'},
        { 'category': 'biolink:Protein', 'key': 'n10'},
        { 'id': ['UniProtKB:P14136','UniProtKB:P35579'] },
        { 'id': ['UniProtKB:P14136','UniProtKB:P35579'], 'is_set': 'false' },
    ]

    for parameter in parameters_sets:
        #### Add a QNode
        messenger.add_qnode(response, parameter)
        if response.status != 'OK':
            print(response.show(level=ARAXResponse.DEBUG))
            return response

    #### Some qedge examples
    parameters_sets = [
        { 'subject': 'n00', 'object': 'n01' },
        { 'subject': 'n01', 'object': 'n10', 'predicate': 'treats' },
   ]

    for parameter in parameters_sets:
        #### Add a QEdge
        messenger.add_qedge(response, parameter)
        if response.status != 'OK':
            print(response.show(level=ARAXResponse.DEBUG))
            return response

    #### Delete one of the edges
    messenger.remove_qedge(response, { 'id': 'e00' } )
    if response.status != 'OK':
        print(response.show(level=ARAXResponse.DEBUG))
        return response


    #### Show the final result
    print(response.show(level=ARAXResponse.DEBUG))
    print(json.dumps(response.envelope.to_dict(),sort_keys=True,indent=2))


if __name__ == "__main__": main()
