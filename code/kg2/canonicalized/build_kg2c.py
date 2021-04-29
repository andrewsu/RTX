#!/bin/env python3
"""
This script creates a canonicalized version of KG2 stored in various file formats, including TSVs ready for import
into Neo4j. Files are created in the directory this script is in. It relies on the options you specify in
kg2c_config.json; in particular, the KG2c will be built off of the KG2 endpoint you specify in that config file.
WARNING: If you happen to already have a custom version of config_local.json on your machine, this script will override
it; make a copy if you don't want to lose it.
Usage: python3 build_kg2c.py [--test]
"""
import argparse
from datetime import datetime
import json
import os
import subprocess
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_kg2c_files import create_kg2c_files
from record_kg2c_meta_info import record_meta_kg_info
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../")  # code directory
from RTXConfiguration import RTXConfiguration

KG2C_DIR = f"{os.path.dirname(os.path.abspath(__file__))}"
CODE_DIR = f"{KG2C_DIR}/../.."


def _setup_rtx_config_local(kg2_neo4j_endpoint: str):
    # Create a config_local.json file based off of configv2.json, but modified for our needs
    _print_log_message("Creating a config_local.json file pointed to the right KG2 Neo4j and synonymizer..")
    RTXConfiguration()  # Ensures we have a reasonably up-to-date configv2.json
    with open(f"{CODE_DIR}/configv2.json") as configv2_file:
        rtx_config_dict = json.load(configv2_file)
    # Point to the 'right' KG2 (the one specified in the KG2c config)
    rtx_config_dict["Contextual"]["KG2"]["neo4j"]["bolt"] = f"bolt://{kg2_neo4j_endpoint}:7687"
    # Point to the 'right' synonymizer (we'll always use the basic name, and don't need full arax.ncats.io path)
    for mode, path_info in rtx_config_dict["Contextual"].items():
        path_info["node_synonymizer"]["path"] = "/something/node_synonymizer.sqlite"
    with open(f"{CODE_DIR}/config_local.json", "w+") as config_local_file:
        json.dump(rtx_config_dict, config_local_file)
    _print_log_message(f"KG2 neo4j bolt entry in config_local is now: "
                       f"{rtx_config_dict['Contextual']['KG2']['neo4j']['bolt']}")


def _upload_output_files_to_s3():
    _print_log_message("Uploading KG2c json and TSV files to S3..")
    tarball_path=f"{KG2C_DIR}/kg2c-tsv.tar.gz"
    json_file_path=f"{KG2C_DIR}/kg2c.json"
    json_lite_file_path=f"{KG2C_DIR}/kg2c_lite.json"
    subprocess.call(f"tar -czvf {tarball_path} nodes_c.tsv nodes_c_header.tsv edges_c.tsv edges_c_header.tsv", shell=True)
    subprocess.call(f"aws s3 cp --no-progress --region us-west-2 {tarball_path} s3://rtx-kg2/", shell=True)
    subprocess.call(f"gzip -f {json_file_path}", shell=True)
    subprocess.call(f"gzip -f {json_lite_file_path}", shell=True)
    subprocess.call(f"aws s3 cp --no-progress --region us-west-2 {json_file_path}.gz s3://rtx-kg2/", shell=True)
    subprocess.call(f"aws s3 cp --no-progress --region us-west-2 {json_lite_file_path}.gz s3://rtx-kg2/", shell=True)


def _print_log_message(message: str):
    current_time = datetime.utcfromtimestamp(time.time()).strftime('%H:%M:%S')
    print(f"{current_time}: {message}")


def main():
    _print_log_message("STARTING KG2c BUILD")
    start = time.time()
    # Grab any parameters passed to this script
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--test", dest="test", action='store_true', default=False)
    args = arg_parser.parse_args()

    # Load the KG2c config file
    with open(f"{KG2C_DIR}/kg2c_config.json") as config_file:
        kg2c_config_info = json.load(config_file)
    kg2_neo4j_endpoint = kg2c_config_info["kg2_neo4j"]
    biolink_model_version = kg2c_config_info["biolink_model_version"]
    include_neighbor_counts = kg2c_config_info["include_neighbor_counts"]
    upload_to_s3 = kg2c_config_info["upload_to_s3"]
    build_synonymizer = kg2c_config_info["build_synonymizer"]
    _print_log_message(f"Biolink model version to use is {biolink_model_version}")
    _print_log_message(f"KG2 Neo4j to use is {kg2_neo4j_endpoint}")

    # Set up an RTX config_local.json file that points to the right KG2 and synonymizer
    _setup_rtx_config_local(kg2_neo4j_endpoint)

    # Build a new node synonymizer, if we're supposed to
    if build_synonymizer and not args.test:
        _print_log_message("Building node synonymizer off of specified KG2..")
        subprocess.call(f"bash -x {KG2C_DIR}/build-synonymizer.sh", shell=True)

    # Actually build KG2c
    _print_log_message("Creating KG2c files..")
    create_kg2c_files(args.test)
    _print_log_message("Recording meta KG info..")
    record_meta_kg_info(biolink_model_version, args.test, include_neighbor_counts)
    if upload_to_s3 and not args.test:
        _print_log_message("Uploading KG2c files to S3..")
        _upload_output_files_to_s3()

    # Remove the config_local file we created (otherwise will always be used instead of configv2.json)
    subprocess.call(f"rm {CODE_DIR}/config_local.json", shell=True)

    _print_log_message(f"DONE WITH KG2c BUILD! Took {round(((time.time() - start) / 60) / 60, 1)} hours")


if __name__ == "__main__":
    main()
