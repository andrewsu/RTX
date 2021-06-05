import datetime
import importlib
import json
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ARAX/ARAXQuery")
modules = {
    "ARAX_messenger"      : {"class": "ARAXMessenger"     , "command": "create_message()"},
    "ARAX_expander"       : {"class": "ARAXExpander"      , "command": "expand()"},
    "ARAX_overlay"        : {"class": "ARAXOverlay"       , "command": "overlay()"},
    "ARAX_filter_kg"      : {"class": "ARAXFilterKG"      , "command": "filter_kg()"},
    "ARAX_filter_results" : {"class": "ARAXFilterResults" , "command": "filter_results()"},
    "ARAX_resultify"      : {"class": "ARAXResultify"     , "command": "resultify()"},
    "ARAX_ranker"         : {"class": "ARAXRanker"        , "command": "rank_results()"}
}

araxi_json = {}

for module in modules.keys():
    m = importlib.import_module(module)
    dsl_name = modules[module]["command"]

    ## for dic in getattr(m, modules[module]["class"])().describe_me():
    for dic in sorted(getattr(m, modules[module]["class"])().describe_me(), key=lambda i: i['dsl_command']):
        #print(dic)

        if 'action' in dic:  # for classes that use the `action=` paradigm
            action = dic['action'].pop()
            del dic['action']
            dsl_name = re.sub('\(.*\)',f'(action={action})', dsl_name)
        elif 'dsl_command' in dic:  # for classes like ARAX_messenger that have different DSL commands with different top level names as methods to the main class
            dsl_command = dic['dsl_command']
            del dic['dsl_command']
            dsl_name = dsl_command

        dsl_name = re.sub('\`','', dsl_name)
        print(dsl_name, end='')
        print('.' * (60-len(dsl_name)), end='')
        
        araxi_json[dsl_name] = {}
        araxi_json[dsl_name]['parameters'] = {}

        if 'brief_description' in dic:
            araxi_json[dsl_name]['description'] = dic['brief_description']
            del dic['brief_description']
        elif 'description' in dic:
            araxi_json[dsl_name]['description'] = dic['description']
            del dic['description']

        if 'parameters' in dic:
            araxi_json[dsl_name]['parameters'] = dic['parameters']
            print('OK')
        else:
            print('found NO parameters!')


ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

file_name = 'araxi.js.new'
fid = open(file_name, 'w')
fid.write("// WARNING:\n")
fid.write("// This file was auto-generated by "+__file__+" on: "+ahora+"\n")
fid.write("//\n")
fid.write("var araxi_commands = "+json.dumps(araxi_json,indent=2)+"\n")
fid.close()

print('\nOutput written to: '+file_name)
