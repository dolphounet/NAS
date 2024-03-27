import os
import telnetlib
import time


def writeLine(file, tn, line):
    tn.write(line.encode() + b"\r\n")
    file.write(line + "\n\r")
    time.sleep(0.03)


def border_router(network, router):
    for interface in network["routers"][router - 1]["interface"]:
        if border_interface(network, router, interface):
            return True
    return False


def border_interface(network, router, interface):
    if (
        interface["neighbor"] != []
        and network["routers"][interface["neighbor"][0] - 1]["AS"]
        != network["routers"][router - 1]["AS"]
    ):
        return True
    return False


def belongs_to_subNet(network, router, subNet):
    return subNet in network["routers"][router - 1]["subNets"]


def addressing_if(file, tn, interface):
    address = " ".join(interface["address"])
    writeLine(file, tn, f"ip address {address}")


def passive_if(file, tn, network, router):
    for interface in network["routers"][router - 1]["interface"]:
        if (
            interface["neighbor"] != []
            and network["routers"][interface["neighbor"][0] - 1]["AS"]
            != network["routers"][router - 1]["AS"]
        ):
            writeLine(file, tn, f"passive-interface {interface['name']}")


def OSPF_if(file, tn, network, interface):
    writeLine(file, tn, "ip ospf 10 area 0")


def OSPF(file, tn, network, router):
    routerId = 3 * (str(router) + ".") + str(router)
    writeLine(file, tn, "router ospf 10")
    writeLine(file, tn, f"router-id {routerId}")
    writeLine(file, tn, "exit")


def MPLS(file, tn):
    writeLine(file, tn, "mpls ip")
    writeLine(file, tn, "mpls label protocol ldp")


def MPLS_if(file, tn, interface):
    writeLine(file, tn, f"mpls ip")


def VRF(file, tn, network, router):
    for interface in network["routers"][router - 1]["interface"]:
        if border_interface(network, router, interface):
            router_client = interface["neighbor"][0]
            RD = network["routers"][router_client - 1]["RD"]
            clientId = network["AS"][network["routers"][router_client - 1]["AS"] - 1][
                "ClientID"
            ]
            RT = network["Clients"][clientId - 1]["RT"]

            writeLine(file, tn, f"vrf definition Client_{clientId}")
            writeLine(file, tn, f"rd {RD}")
            writeLine(file, tn, f"route-target export {RT}")
            writeLine(file, tn, f"route-target import {RT}")
            
            for id in network["Clients"][clientId-1]["Connections"] :
                writeLine(file, tn, f"route-target import {network["Clients"][id - 1]["RT"]}")
                
            writeLine(file, tn, "address-family ipv4")
            writeLine(file, tn, "exit-address-family")
            writeLine(file, tn, "exit")


def BGP_Coeur(file, tn, network, router):
    """
    Ca s'applique pour le routeur d'ID router
    """

    routerId = f"{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}"
    neighbor_addresses = {"iBGP": [], "eBGP": []}

    writeLine(file, tn, f"router bgp {network['routers'][router-1]['AS']}")
    writeLine(file, tn, f"bgp router-id {routerId}")
    for rtr in network["routers"]:
        neighbor = rtr["ID"][0]
        if (
            rtr["AS"] == network["routers"][router - 1]["AS"]
            and neighbor != router
            and border_router(network, neighbor)
        ):
            # iBGP
            for interface in network["routers"][neighbor - 1]["interface"]:
                if "Loopback" in interface["name"]:
                    for interface in network["routers"][network["RouteReflector"]-1]["interface"]:
                        if "Loopback" in interface["name"]:
                            neighbor_address = interface["address"][0]
                            break
                    break
            writeLine(
                file,
                tn,
                f"neighbor {neighbor_address} remote-as {network['routers'][neighbor-1]['AS']}",
            )
            writeLine(file, tn, f"neighbor {neighbor_address} update-source Loopback1")
            neighbor_addresses["iBGP"].append(neighbor_address)

    writeLine(file, tn, "address-family vpnv4")
    # iBGP
    for neighbor_address in neighbor_addresses["iBGP"]:
        writeLine(file, tn, f"neighbor {neighbor_address} activate")
        writeLine(file, tn, f"neighbor {neighbor_address} send-community extended")

    writeLine(file, tn, "exit-address-family")
    for interface in network["routers"][router - 1]["interface"]:
        if border_interface(network, router, interface):
            router_client = interface["neighbor"][0]
            clientId = network["AS"][network["routers"][router_client - 1]["AS"] - 1][
                "ClientID"
            ]
            for client_interface in network["routers"][router_client - 1]["interface"]:
                if router in client_interface["neighbor"]:
                    neighbor_address = client_interface["address"][0]
                    break
            writeLine(file, tn, "address-family ipv4 vrf Client_" + str(clientId))
            writeLine(
                file,
                tn,
                f"neighbor {neighbor_address} remote-as {network['routers'][router_client-1]['AS']}",
            )
            writeLine(file, tn, f"neighbor {neighbor_address} activate")

    writeLine(file, tn, "exit")


def BGP_Client(file, tn, network, router):
    routerId = f"{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}.{network['routers'][router-1]['ID'][0]}"

    writeLine(file, tn, f"router bgp {network['routers'][router-1]['AS']}")
    writeLine(file, tn, f"bgp router-id {routerId}")

    for interface in network["routers"][router - 1]["interface"]:
        if border_interface(network, router, interface):
            router_PE = interface["neighbor"][0]
            clientId = network["AS"][network["routers"][router_PE - 1]["AS"] - 1][
                "ClientID"
            ]
            for interface in network["routers"][router_PE - 1]["interface"]:
                if router in interface["neighbor"]:
                    neighbor_address = interface["address"][0]
                    break
            neighbor_address = interface["address"][0]
            writeLine(
                file,
                tn,
                f"neighbor {neighbor_address} remote-as {network['routers'][router_PE-1]['AS']}",
            )
            writeLine(file, tn, "address-family ipv4")
            writeLine(file, tn, "redistribute connected")
            writeLine(file, tn, f"neighbor {neighbor_address} activate")
            writeLine(file, tn, "exit-address-family")

    writeLine(file, tn, "exit")

def config_router(network, routerID):
    fileName = f"log{routerID}"  # We create a logging file
    if os.path.exists(fileName):
        os.remove(fileName)
    file = open(fileName, "x")
    file.close()
    with open(
        fileName, "a"
    ) as file:  # We open the logging file to write what we are sending to the router
        port = network["routers"][routerID - 1]["Port"]
        host = "localhost"
        tn = telnetlib.Telnet(host, port)
        writeLine(file, tn, "")
        writeLine(file, tn, "enable")
        writeLine(file, tn, "write erase")  # To erase current configuration
        writeLine(file, tn, "")  # To confirm the configuration deletion
        tn.read_until(b"Erase of nvram: complete")  # Waiting for the deletion to finish
        writeLine(file, tn, "conf t")
        if (
            border_router(network, routerID)
            and network["routers"][routerID - 1]["AS"] == 1
        ):
            VRF(file, tn, network, routerID)
        if "MPLS" in network["AS"][network["routers"][routerID - 1]["AS"] - 1]["IGP"]:
            MPLS(file, tn)
        for interface in network["routers"][routerID - 1]["interface"]:
            if interface["neighbor"] != [] or "Loopback" in interface["name"]:
                writeLine(file, tn, f"interface {interface['name']}")
                if (
                    border_interface(network, routerID, interface) 
                    and network["routers"][routerID - 1]["AS"] == 1 
                ):
                    router_client = interface["neighbor"][0]
                    writeLine(file, tn, f"vrf forwarding Client_{network['AS'][network['routers'][router_client - 1]['AS'] - 1]['ClientID']}")
                
                addressing_if(file, tn, interface)

                if "OSPF" in network["AS"][network["routers"][routerID - 1]["AS"] - 1][
                    "IGP"
                ] and not border_interface(network, routerID, interface):
                    OSPF_if(file, tn, network, interface)

                if "MPLS" in network["AS"][network["routers"][routerID - 1]["AS"] - 1][
                    "IGP"
                ] and not border_interface(network, routerID, interface):
                    MPLS_if(file, tn, interface)

                writeLine(file, tn, "no shutdown")
                writeLine(file, tn, "exit")

        if (
            border_router(network, routerID)
            and network["routers"][routerID - 1]["AS"] == 1
        ):
            BGP_Coeur(file, tn, network, routerID)

        elif (
            border_router(network, routerID)
            and network["routers"][routerID - 1]["AS"] != 1
        ):
            BGP_Client(file, tn, network, routerID)

        if "OSPF" in network["AS"][network["routers"][routerID - 1]["AS"] - 1]["IGP"]:
            OSPF(file, tn, network, routerID)

        writeLine(file, tn, "end")
        # To write the configuration in order not to lose it the next time
        tn.close()
