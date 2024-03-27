import threading

from filesIO import readJson, writeJson,mkdir
from IPv4attribution import attributeIP, attributeRD, attributeRT
from networkConfig import config_router



def main():

    # Récupération des informations du réseau
    network = readJson("Network_Intent.json")

    # Attribution des IP
    attributeIP(network)
    attributeRT(network)
    attributeRD(network)
    # Ecriture du fichier json pour voir la config
    writeJson(network,"network.json")
    logsPath = mkdir("logs")

    # Ecriture de la configuration avec telnet
    threads = [threading.Thread(target=config_router, args=(network, i+1,logsPath)) for i in range(len(network["routers"]))]
    for thread in threads:
        thread.start()

    for thread in threads :
        thread.join()

if __name__ == "__main__":
    main()
