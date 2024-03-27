import json

def readJson(file):
    Network_Intent = open(file)
    network = json.load(Network_Intent)
    Network_Intent.close
    return network

def writeJson(data,name):
    if name == "network.json":
        data = formatNetwork(data)

    with open(name,'w') as f :
        jsonData = json.dumps(data,indent=3)
        print(jsonData,file=f)

def formatNetwork(network):
    Links = {}
    for tuple in network["InterAS"]["InterASlinks"]["Links"]:
        new_key = str(tuple)
        Links[new_key] = network["InterAS"]["InterASlinks"]["Links"][tuple]
    network["InterAS"]["InterASlinks"]["Links"] = Links
    return network
