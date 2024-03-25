import threading

from filesIO import readJson
from IPv4attribution import attributeIP, attributeRD, attributeRT
from networkConfig import config_router


def main():

    # Récupération des informations du réseau
    network = readJson("Network_Intent.json")

    # Attribution des IP
    attributeIP(network)
    attributeRT(network)
    attributeRD(network)

    print()
    """
    for router in network["routers"]:
        config_router(network, router["ID"][0])

    # Ecriture de la configuration avec telnet
    
    threads = [threading.Thread(target=config_router, args=(network, i+1)) for i in range(len(network["routers"]))]
    for thread in threads:
        thread.start()

    for thread in threads :
        thread.join()
    """


if __name__ == "__main__":
    main()
