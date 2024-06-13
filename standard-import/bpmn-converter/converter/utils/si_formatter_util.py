from typing import Dict, Any
#from hashlib import sha256

#TODO: actually hash instead of truncate? 
#Note: hashing is not meant for safety/security here, only uniformity of id length
def hashId(id: str):
    return id[0:35]

def fixLineEndpoint(endpoint: dict):
    if endpoint["type"] == "shapeEndpoint":
        if len(endpoint["shapeId"]) > 36:
            endpoint["shapeId"] = hashId(endpoint["shapeId"])
        if endpoint["position"]["x"] < 0:
           endpoint["position"]["x"] = 0
        if endpoint["position"]["y"] < 0:
           endpoint["position"]["y"] = 0 
    elif endpoint["type"] == "lineEndpoint": 
        if len(endpoint["lineId"]) > 36:
            endpoint["lineId"] = hashId(endpoint["lineId"])
        if endpoint["position"] < 0:
            endpoint["position"] = 0

def forceSIFormatting(data: dict):
    for page in data["pages"]:
        if len(page["id"]) > 36:
            page["id"] = hashId(page["id"])
        for shape in page["shapes"]:
            if len(shape["id"]) > 36:
                shape["id"] = hashId(shape["id"])
        for line in page["lines"]:
            if len(line["id"]) > 36:
                line["id"] = hashId(line["id"])
            fixLineEndpoint(line["endpoint1"])
            fixLineEndpoint(line["endpoint2"])
        #TODO: groups and layers?
    return data