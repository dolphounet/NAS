import json

def readJson(file):
    Network_Intent = open(file)
    network = json.load(Network_Intent)
    Network_Intent.close
    return network

