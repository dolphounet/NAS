import telnetlib
import time
import os

def writeLine(file, tn, line):
    tn.write(line.encode()+b"\r\n")
    file.write(line+"\n\r")
    time.sleep(0.01)

def border_router(network, router):
    for interface in network["routers"][router-1]["interface"]:
        if interface["neighbor"] != [] and network["routers"][interface["neighbor"][0]-1]["AS"] != network["routers"][router-1]["AS"]:
            return True
    return False

def belongs_to_subNet(network, router, subNet):
    return subNet in network["routers"][router-1]["subNets"]

def addressing_if(file, tn, interface):
    address = "".join(interface["address"])
    writeLine(file, tn, f"interface {interface['name']}")
    writeLine(file, tn, "ipv6 enable")
    writeLine(file, tn, f"ipv6 address {address}")


def passive_if(file, tn, network, router):
    for interface in network["routers"][router-1]["interface"]:
        if interface["neighbor"] != [] and network["routers"][interface["neighbor"][0]-1]["AS"] != network["routers"][router-1]["AS"]:
            writeLine(file, tn, f"passive-interface {interface['name']}")

def OSPF_if(file, tn, network,interface):
    writeLine(file, tn, "ipv6 ospf 10 area 0")
    for interfaceType in network["Constants"]["Bandwith"]:
        if interfaceType in interface["name"] and interfaceType != "Reference":
            writeLine(file, tn, f"bandwidth {network['Constants']['Bandwith'][interfaceType]}")
            if interface['metricOSPF'] != "":
                writeLine(file, tn, f"ipv6 ospf cost {interface['metricOSPF']}")

def OSPF(file, tn, network, router):
    routerId = f"{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}"
    writeLine(file, tn, "ipv6 router ospf 10")
    writeLine(file, tn, f"router-id {routerId}")
    passive_if(file, tn, network, router)
    writeLine(file, tn, f"auto-cost reference-bandwidth {network['Constants']['Bandwith']['Reference']}")
    writeLine(file, tn, "exit")

def RIP_if(file, tn, network, router, interface):
    if interface["name"] == "Loopback1" or network["routers"][interface["neighbor"][0]-1]["AS"] == network["routers"][router-1]["AS"]:
        writeLine(file, tn, "ipv6 rip BeginRIP enable")

def RIP(file, tn):
    writeLine(file, tn, "ipv6 router rip BeginRIP")
    writeLine(file, tn, "redistribute connected")
    writeLine(file, tn, "exit")

def BGP(file, tn, network, router):
    """
    Ca s'applique pour le routeur d'ID router
    """

    routerId = f"{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}"
    neighbor_addresses = {"iBGP" : [], "eBGP" : []}

    writeLine(file, tn, f"router bgp {network['routers'][router-1]['AS']}")
    writeLine(file, tn, "no bgp default ipv4-unicast")
    writeLine(file, tn, f"bgp router-id {routerId}")
    for rtr in network["routers"]:
        neighbor = rtr["ID"][0]
        if neighbor != router:

            # iBGP
            if network["routers"][neighbor-1]["AS"] == network["routers"][router-1]["AS"]:
                for interface in network["routers"][neighbor-1]["interface"]:
                    if "Loopback" in interface["name"]:
                        neighbor_address = interface["address"][0]
                        break
                writeLine(file, tn, f"neighbor {neighbor_address} remote-as {network['routers'][neighbor-1]['AS']}")
                writeLine(file, tn, f"neighbor {neighbor_address} update-source Loopback1")
                neighbor_addresses["iBGP"].append((neighbor_address,neighbor))

            # eBGP
            elif neighbor in network["adjDic"][router]:
                for interface in network["routers"][neighbor-1]["interface"]:
                    if router in interface["neighbor"]:
                        neighbor_address = interface["address"][0]
                        break
                writeLine(file, tn, f"neighbor {neighbor_address} remote-as {network['routers'][neighbor-1]['AS']}")
                neighbor_addresses["eBGP"].append((neighbor_address,neighbor))
    writeLine(file, tn, "exit")

    BGP_CommunityLists(file, tn, network,router)
    BGP_Routemap(file, tn, network,router) 

    # Config de l'address-family en ipv6
    writeLine(file, tn, f"router bgp {network['routers'][router-1]['AS']}")
    writeLine(file, tn, "address-family ipv6 unicast")
    once = False
    # iBGP
    for (neighbor_address,neighborID) in neighbor_addresses["iBGP"]:
        writeLine(file, tn, f"neighbor {neighbor_address} activate")
        writeLine(file, tn, f"neighbor {neighbor_address} send-community")
        if not once :
            # Rejoindre son sous réseau
            for subNet in network["AS"][network["routers"][router-1]["AS"]-1]["subNets"]:
                if belongs_to_subNet(network, router, subNet):
                    writeLine(file, tn, f"network {''.join(subNet)} route-map {network['routers'][router-1]['AS']}_Client_in")
            once = True

    # eBGP
    for (neighbor_address,neighborID) in neighbor_addresses["eBGP"]:
        writeLine(file, tn, f"neighbor {neighbor_address} activate")
        BGP_Border(file, tn, network, router,neighbor_address,neighborID)
        if not once :
            # Rejoindre son sous réseau
            for subNet in network["InterAS"]["subNets"]:
                if belongs_to_subNet(network, router, subNet):
                    writeLine(file, tn, f"network {''.join(subNet)} route-map {network['routers'][router-1]['AS']}_Client_in")
            writeLine(file, tn, f"network {network['AS'][network['routers'][router-1]['AS']-1]['networkIP'][0]}{network['AS'][network['routers'][router-1]['AS']-1]['networkIP'][1]}")
            once = True 
    writeLine(file, tn, "exit-address-family")
    writeLine(file, tn, "exit")

def BGP_Border(file, tn, network,router,neighbor_address,neighborID):

    # Application des route-map
    neighborType = network["AS"][network["routers"][router-1]["AS"]-1]["relations"][str(network["routers"][neighborID-1]["AS"])]
    writeLine(file, tn, f"neighbor {neighbor_address} route-map {network['routers'][router-1]['AS']}_{neighborType}_in in")
    # Route-map out
    writeLine(file, tn, f"neighbor {neighbor_address} route-map {network['routers'][router-1]['AS']}_{neighborType}_out out")


def BGP_CommunityLists(file, tn, network,router):
    writeLine(file, tn, f"ipv6 route {network['AS'][network['routers'][router-1]['AS']-1]['networkIP'][0]}{network['AS'][network['routers'][router-1]['AS']-1]['networkIP'][1]} Null0")
    writeLine(file, tn, "ip bgp-community new-format")

    for relation in network["Constants"]["LocPref"]:
        if relation != "Client" :
            writeLine(file, tn, f"ip community-list {network['Constants']['LocPref'][relation]} permit {network['routers'][router-1]['AS']}:{network['Constants']['LocPref']['Client']}")
            writeLine(file, tn, f"ip community-list {network['Constants']['LocPref'][relation]} deny {network['routers'][router-1]['AS']}:{network['Constants']['LocPref']['Peer']}")
            writeLine(file, tn, f"ip community-list {network['Constants']['LocPref'][relation]} deny {network['routers'][router-1]['AS']}:{network['Constants']['LocPref']['Provider']}")

        elif relation == "Client" :
            writeLine(file, tn, f"ip community-list {network['Constants']['LocPref'][relation]} permit {network['routers'][router-1]['AS']}:{network['Constants']['LocPref']['Client']}")
            writeLine(file, tn, f"ip community-list {network['Constants']['LocPref'][relation]} permit {network['routers'][router-1]['AS']}:{network['Constants']['LocPref']['Peer']}")
            writeLine(file, tn, f"ip community-list {network['Constants']['LocPref'][relation]} permit {network['routers'][router-1]['AS']}:{network['Constants']['LocPref']['Provider']}")

def BGP_Routemap(file, tn, network,router):
    
    # In route-map
    for relation in network["Constants"]["LocPref"]:
        writeLine(file, tn, f"route-map {network['routers'][router-1]['AS']}_{relation}_in permit {int(network['Constants']['LocPref'][relation]/10)}")
        writeLine(file, tn, f"set local-preference {network['Constants']['LocPref'][relation]}")
        writeLine(file, tn, f"set community {network['routers'][router-1]['AS']}:{network['Constants']['LocPref'][relation]}")
        writeLine(file, tn, "exit")
    
    # Out route-map
    for relation in network["Constants"]["LocPref"] :
        writeLine(file, tn, f"route-map {network['routers'][router-1]['AS']}_{relation}_out permit {int(network['Constants']['LocPref'][relation]/10)}")
        writeLine(file, tn, f"match community {network['Constants']['LocPref'][relation]}")
        writeLine(file, tn, "exit")

def config_router(network, routerID):
    fileName = f"log{routerID}" #We create a logging file
    if os.path.exists(fileName):
        os.remove(fileName)
    file = open(fileName, "x")
    file.close()
    with open(fileName, "a") as file: #We open the logging file to write what we are sending to the router
        port = network["routers"][routerID-1]["Port"]
        host = "localhost"
        tn = telnetlib.Telnet(host, port)
        writeLine(file, tn, "enable")
        writeLine(file, tn, "write erase") #To erase current configuration
        writeLine(file, tn, "") #To confirm the configuration deletion
        tn.read_until(b"Erase of nvram: complete") #Waiting for the deletion to finish
        writeLine(file, tn, "conf t")
        writeLine(file, tn, "ipv6 unicast-routing")
        for interface in network["routers"][routerID-1]["interface"]:
            if interface["neighbor"] != [] or "Loopback" in interface["name"]:
                addressing_if(file, tn, interface)
                if "RIP" in network["AS"][network["routers"][routerID-1]["AS"]-1]["IGP"]:
                    RIP_if(file, tn, network, routerID, interface)

                if "OSPF" in network["AS"][network["routers"][routerID-1]["AS"]-1]["IGP"]:
                    OSPF_if(file, tn, network,interface)
                writeLine(file, tn, "no shutdown")
                writeLine(file, tn, "exit")
        
        BGP(file, tn, network, routerID)

        if "RIP" in network["AS"][network["routers"][routerID-1]["AS"]-1]["IGP"]:
            RIP(file, tn)

        if "OSPF" in network["AS"][network["routers"][routerID-1]["AS"]-1]["IGP"]:
            OSPF(file, tn, network, routerID)
        writeLine(file, tn, "end")
        writeLine(file, tn, "write") #To write the configuration in order not to lose it the next time
        tn.read_until(b"[OK]") #Waiting for the writing to complete
        tn.close()
