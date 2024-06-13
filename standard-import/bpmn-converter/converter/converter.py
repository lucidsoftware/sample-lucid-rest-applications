import argparse
import json
from utils.bpmn_object_to_lucid_json import transform_object_into_lucid_json
from utils.bpmn_to_object import object_from_bpmn
from utils.lucid_utils import oauth, uploadDoc
if __name__ == '__main__':
    #TODO: Add description
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--Input", help = "File or  directory to read from, uses ./ if not specified")
    parser.add_argument("-r", "--Recursive", help = "If input is dir it will also parse all the directories inside it", action='store_true')
    parser.add_argument("-f", "--ForceFormat", help = "Formats to fix invalid Standard Import fields (i.e. shortens ID's, fixes relative endpoint issues, etc)", action='store_true')

    args = parser.parse_args() 

    input = args.Input if isinstance(args.Input, str) else './'
    recursive = args.Recursive
    format = args.ForceFormat

    bpmn_object = object_from_bpmn(input, recursive)

    if bpmn_object == None:
        print('No data was parsed, something went wrong')
    else:
        lucid_jsons = transform_object_into_lucid_json(bpmn_object, format)

        access_token = oauth()

        for lucid_doc in lucid_jsons:
            uploadDoc(lucid_doc, access_token)
    
