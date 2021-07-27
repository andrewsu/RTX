## download 'kg2_node_info.tsv' file from /translator/data/orangeboard/databases/KG2.6.7.1 from arax.ncats.io or run python dump_kg2_node_data.py under RTX/code/ARAX/NodeSynonymizer
python generate_synoym_pkl.py --NodeDescriptionFile ~/work/RTX/data/KGmetadata/kg2_node_info_v2.6.7.1.tsv --CurieType "['biolink:Disease', 'biolink:PhenotypicFeature', 'biolink:ChemicalSubstance', 'biolink:Drug', 'biolink:DiseaseOrPhenotypicFeature', 'biolink:Metabolite']" --OutFile ~/work/RTX/code/ARAX/KnowledgeSources/COHD_local/data/backup/preferred_synonyms_kg2_6_7_1.pkl
python OMOP_mapping_parallel.py --PKLfile ~/work/RTX/code/ARAX/KnowledgeSources/COHD_local/data/backup/preferred_synonyms_kg2_6_7_1.pkl --OutFile ~/work/RTX/code/ARAX/KnowledgeSources/COHD_local/data/backup/preferred_synonyms_kg2_6_7_1_with_concepts.pkl
