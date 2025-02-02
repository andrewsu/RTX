import datetime
import json
import os
import sys
import urllib.request

jsdefs = {}

# schema at:   https://github.com/NCATSTranslator/OperationsAndWorkflows/blob/main/schema/operation.json
raw_schema = ' https://raw.githubusercontent.com/NCATSTranslator/OperationsAndWorkflows/main/schema/operation.json'

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ARAX/ARAXQuery")
from operation_to_ARAXi import WorkflowToARAXi
wf = WorkflowToARAXi()
in_arax = wf.implemented

# for local testing:
#with open('wfschema.json') as file:
#    schema = json.load(file)

with urllib.request.urlopen(raw_schema) as file:
    schema = json.loads(file.read().decode())

    for operation in schema["$defs"]:
        id = schema["$defs"][operation]['properties']['id']['enum'][0]
        print("In: "+operation+" ("+id+")")

        jsdefs[id] = {}
        jsdefs[id]['in_arax'] = id in in_arax

        params = {}
        if 'properties' in schema["$defs"][operation]['properties']['parameters']:
            for par in schema["$defs"][operation]['properties']['parameters']['properties']:
                params[par] = {}
                ref = schema["$defs"][operation]['properties']['parameters']['properties'][par]
                if 'required' in schema["$defs"][operation]['properties']['parameters']:
                    params[par]['is_required'] = par in schema["$defs"][operation]['properties']['parameters']['required']
                else:
                    params[par]['is_required'] = False;

                if 'type' in ref:
                    params[par]['type'] = ref['type']
                if 'minLength' in ref:
                    params[par]['minLength'] = ref['minLength']
                if 'enum' in ref:
                    params[par]['enum'] = ref['enum']
                if 'default' in ref:
                    params[par]['default'] = ref['default']
                if 'minimum' in ref:
                    params[par]['min'] = ref['minimum']
                if 'maximum' in ref:
                    params[par]['max'] = ref['maximum']
                if 'example' in ref:
                    params[par]['examples'] = ref['example']
                if 'description' in ref:
                    params[par]['description'] = ref['description']


                for v in ['type', 'minLength', 'enum', 'default','minimum', 'maximum', 'example', 'description']:
                    if v in ref:
                        del ref[v]
                for a in ref:
                    print("--------------- missed: ["+par+"]: "+a)

        jsdefs[id]['parameters'] = params


ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

file_name = 'wfoperations.js.new'
fid = open(file_name, 'w')
fid.write("// WARNING:\n")
fid.write("// This file was auto-generated by "+__file__+" on: "+ahora+"\n")
fid.write("//\n")
fid.write("var wf_operations = "+json.dumps(jsdefs,indent=2)+"\n")
fid.close()

print('\nOutput written to: '+file_name)
