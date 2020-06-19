#!/usr/bin/env python3
'''ncbigene_tsv_to_kg_json.py: Extracts a KG2 JSON file from the NCBI human gene distribution in TSV format

   Usage: ncbigene_tsv_to_kg_json.py [--test] <inputFile.tsv> <outputFile.json>
'''

__author__ = 'Stephen Ramsey'
__copyright__ = 'Oregon State University'
__credits__ = ['Stephen Ramsey']
__license__ = 'MIT'
__version__ = '0.1.0'
__maintainer__ = ''
__email__ = ''
__status__ = 'Prototype'

import argparse
import kg2_util
import os


NCBI_BASE_IRI = 'https://identifiers.org/ncbigene:'
NCBI_KB_IRI = 'https://registry.identifiers.org/registry/ncbigene'
NCBI_KB_CURIE_ID = kg2_util.CURIE_PREFIX_IDENTIFIERS_ORG_REGISTRY + ':' + 'ncbigene'
NCBI_KB_URL = kg2_util.BASE_URL_IDENTIFIERS_ORG_REGISTRY + 'ncbigene'


def get_args():
    arg_parser = argparse.ArgumentParser(description='ncbigene_tsv_to_kg_json.py: builds a KG2 JSON representation for NCBI human genes')
    arg_parser.add_argument('--test', dest='test', action="store_true", default=False)
    arg_parser.add_argument('inputFile', type=str)
    arg_parser.add_argument('outputFile', type=str)
    return arg_parser.parse_args()


def make_node(ncbi_gene_id: str,
              full_name: str,
              gene_symbol: str,
              update_date: str,
              other_synonyms: list = None):
    category_label = kg2_util.BIOLINK_CATEGORY_GENE
    if other_synonyms is None:
        other_synonyms = []
    node_curie = kg2_util.CURIE_PREFIX_NCBI_GENE + ':' + ncbi_gene_id
    iri = NCBI_BASE_IRI + ncbi_gene_id
    node_dict = kg2_util.make_node(node_curie,
                                   iri,
                                   full_name,
                                   category_label,
                                   update_date,
                                   NCBI_KB_CURIE_ID)
    node_dict['synonym'] = list(set([gene_symbol] + other_synonyms))
    return node_dict


def make_kg2_graph(input_file_name: str, test_mode: bool = False):
    nodes = []
    edges = []
    gene_ctr = 0

    update_date = os.path.getmtime(input_file_name)
    ontology_curie_id = NCBI_KB_CURIE_ID
    ens_kp_node = kg2_util.make_node(ontology_curie_id,
                                     NCBI_KB_URL,
                                     'NCBI Genes',
                                     kg2_util.BIOLINK_CATEGORY_DATA_FILE,
                                     update_date,
                                     ontology_curie_id)
    nodes.append(ens_kp_node)

    with open(input_file_name, 'r') as input_file:
        for line in input_file:
            if line.startswith('#'):
                continue
            gene_ctr += 1
            if test_mode and gene_ctr > 10000:
                break
            fields = line.rstrip("\n").split("\t")
            fields = [(field if field.strip() != '-' else None) for field in fields]
            [taxon_id_str,
             ncbi_gene_id,
             gene_symbol,
             locus_tag,
             synonyms_str,
             db_xrefs,
             chromosome,
             map_location,
             description,
             type_of_gene,
             symbol_auth,
             full_name_auth,
             nomenc_status,
             other_desig,
             modify_date,
             feature_type] = fields
            taxon_id_int = int(taxon_id_str)
            if taxon_id_int != kg2_util.NCBI_TAXON_ID_HUMAN:
                # skip neanderthal- and denisovan-specific genes
                continue
            node_synonyms = list()
            if synonyms_str is not None:
                node_synonyms += synonyms_str.split('|')
            if other_desig is not None:
                node_synonyms += other_desig.split('|')
            if symbol_auth is not None and symbol_auth != gene_symbol:
                node_synonyms = [symbol_auth] + node_synonyms
            node_synonyms = list(set(node_synonyms))
            full_name = full_name_auth
            if full_name is None:
                full_name = description
            node_dict = make_node(ncbi_gene_id,
                                  full_name,
                                  gene_symbol,
                                  modify_date,
                                  node_synonyms)
            node_curie_id = node_dict['id']
            type_str = 'Type:'+type_of_gene
            node_description = ''
            if description is not None and description != full_name_auth:
                node_description = description + '; '
            node_description += type_str
            if map_location is not None:
                node_description += '; Locus:' + map_location
            if nomenc_status is not None:
                nomenc_tag = 'official'
            else:
                nomenc_tag = 'unofficial'
            node_description += '; NameStatus:' + nomenc_tag
            node_dict['description'] = node_description
            nodes.append(node_dict)
            org_curie = kg2_util.CURIE_PREFIX_NCBI_TAXON + ':' + taxon_id_str
            predicate_label = 'in_taxon'

            edge_dict = kg2_util.make_edge_biolink(node_curie_id,
                                                   org_curie,
                                                   predicate_label,
                                                   NCBI_KB_CURIE_ID,
                                                   modify_date)
            edges.append(edge_dict)
            if db_xrefs is not None:
                xrefs_list = db_xrefs.split('|')
                for xref_curie in xrefs_list:
                    if xref_curie.startswith('HGNC:HGNC:'):
                        xref_curie = 'HGNC:' + xref_curie.replace('HGNC:', '')
                    elif xref_curie.startswith('Ensembl:'):
                        xref_curie = xref_curie.upper()
                    elif xref_curie.startswith('MIM:'):
                        xref_curie = 'OMIM:' + xref_curie.replace('MIM:', '')
                    edges.append(kg2_util.make_edge(node_curie_id,
                                                    xref_curie,
                                                    kg2_util.IRI_OWL_SAME_AS,
                                                    kg2_util.CURIE_OWL_SAME_AS,
                                                    'same_as',
                                                    NCBI_KB_CURIE_ID,
                                                    modify_date))
    return {'nodes': nodes,
            'edges': edges}


if __name__ == '__main__':
    args = get_args()
    input_file_name = args.inputFile
    output_file_name = args.outputFile
    test_mode = args.test
    graph = make_kg2_graph(input_file_name, test_mode)
    kg2_util.save_json(graph, output_file_name, test_mode)
