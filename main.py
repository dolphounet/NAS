from filesIO import readJson
from IPattribution import attributeIP
from networkConfig import config_router
import threading



def main():

    # Récupération des informations du réseau
    network = readJson('Network_Intent.json')

    # Attribution des IP
    attributeIP(network)

    # Ecriture de la configuration avec telnet
    
    threads = [threading.Thread(target=config_router, args=(network, i+1)) for i in range(len(network["routers"]))]
    for thread in threads:
        thread.start()

    for thread in threads :
        thread.join()
if __name__ == "__main__":
    main()

