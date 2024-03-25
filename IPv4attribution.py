import filesIO

def findAdjacency(network):
    adjDic = {}

    for router in network["routers"]:
        adjDic[router["ID"][0]]=[]

        for interface in router["interface"]:
            for i in range(0,len(interface["neighbor"])):
                if interface["neighbor"][i] != []:
                    adjDic[router["ID"][0]].append(interface["neighbor"][i])

    network["adjDic"] = adjDic

def attributeRT(network):

    tempClientASs = []
    for client in network["Clients"]:
        client["RT"] = f"100:{client['ClientID']}"
        for ASiD in client["ASList"]:
            network["AS"][ASiD-1]["ClientID"] = client['ClientID']
            tempClientASs.append(ASiD)

    for AS in network["AS"]:
        if AS["ASname"] not in tempClientASs:
            AS['ClientID'] = 0


def createLinks(network):
    # Crée les dictionnaires contenants les liens, le nb de liens et la liste des routeurs concernés

    ASlinks = []
    for i in range(0,len(network["AS"])):
        ASlinks.append({ "Count":0, "Links":[],"RouterList":[] })
        network["AS"][i]["subNets"] = []

    InterASlinks = { "Count":0, "Links": {}}
    network["InterAS"]["subNets"] = []

    visited = []
    for routerID in network["adjDic"] :
        visited.append(routerID)
        for connectedRouter in network["adjDic"][routerID]:
            if (network["routers"][connectedRouter-1]["AS"] == network["routers"][routerID-1]["AS"]) and (connectedRouter not in visited):
                ASlinks[network["routers"][routerID-1]["AS"]-1]["Count"] += 1
                ASlinks[network["routers"][routerID-1]["AS"]-1]["Links"].append([routerID,connectedRouter])
            elif connectedRouter not in visited :
                InterASlinks["Count"] += 1
                InterASlinks["Links"][(routerID,connectedRouter)] = None

    # Gestion des addresses des routeurs interAS

    for l in range(0,InterASlinks["Count"]):
        Subnet = network["InterAS"]["networkIP"][0]
        network["InterAS"]["subNets"].append([calcSubnet(Subnet,l*4,network["InterAS"]["networkIP"][1]),slashToMask(30)])

    # Gestion des addresses des routeurs des AS

    for j in range(0,len(ASlinks)):
        for k in range(0,ASlinks[j]["Count"]):
            Subnet = network["AS"][j]["networkIP"][0]
            network["AS"][j]["subNets"].append([calcSubnet(Subnet,k*4,network["AS"][j]["networkIP"][1]),slashToMask(30)])
    
    for router in network["routers"]:
        ASlinks[router["AS"]-1]["RouterList"].append(router["ID"][0])
        router["subNets"]=[]

    # Appliquer les adresses de loopback

    for i in range(0,len(ASlinks)):

        loopbackNetIP = network["AS"][i]["loopbackNetworkIP"][0]
        loopbackRouterAdd = 1

        for routerID in ASlinks[i]["RouterList"]:
            loopback = {"name": "Loopback1","neighbor" : [], "metricOSPF" : "", "address" : [calcSubnet(loopbackNetIP,loopbackRouterAdd,"/8"),slashToMask(32)]}
            network["routers"][routerID-1]["interface"].append(loopback)
            loopbackRouterAdd += 1

    return ASlinks,InterASlinks

def calcSubnet(networkIP,count,mask):

    netIP = networkIP.split(".")
    netIP[3] = str(int(netIP[3])+count)
    IP = ".".join(netIP)
    return IP

def calcIP(subnet,nb):
    netIP = subnet.split(".")
    netIP[3] = str(int(netIP[3])+nb)
    IP = ".".join(netIP)
    return IP

def slashToMask(slash):
    zero_bits = 32-slash
    one_bits = 32 - zero_bits
    bits = ""
    for bit in range(one_bits):
        bits+= "1" 
    for bit in range(zero_bits):
        bits += "0"
    mask = ""
    mask += BitsToDecimal(bits[:8])
    mask += "."
    mask += BitsToDecimal(bits[8:16])
    mask += "."
    mask += BitsToDecimal(bits[16:24])
    mask += "."
    mask += BitsToDecimal(bits[24:32])
    return mask


def adressesLeft(mask):
    #nombre d'adresses dispo par carré
    Nb_adresses = [0,0,0,0]
    Nb_adresses[0] = 255- int(mask[:3])
    Nb_adresses[1] = 255 - int(mask[4:7])
    Nb_adresses[2] = 255 - int(mask[8:11])
    Nb_adresses[3] = 255 - int(mask[12:15])
    return Nb_adresses


def BitsToDecimal(bits):
    decimal=0
    for i in range(len(bits)):
        if bits[i] == "1":
            decimal +=2**(len(bits)-(i+1))
    return (f"{decimal}")


def attributeRD(network):
    RD_Dic = {}

    for AS in network["AS"]:
        RD_Dic[AS["ASname"]]=0
    for router in network["routers"]:
        RD_Dic[router["AS"]]+=1
        router["RD"]=f"{router['AS']}:{router['ID'][0]}"
        
    
def attributeIP(network):

    findAdjacency(network)
    ASlinks,InterASlinks = createLinks(network)

    # Gestion pour un AS
    for i in range(0,len(ASlinks)):
        for j in range(0,len(ASlinks[i]["Links"])):
            currentNet = network["AS"][i]["subNets"][j][0]
            (ID1,ID2) = ASlinks[i]["Links"][j]

            for interface in network["routers"][ID1-1]["interface"]:
                if interface["neighbor"] != [] and interface["neighbor"] == [ID2] :
                    interface["address"] = [calcIP(currentNet,1),network["AS"][i]["subNets"][j][1]]
                    network["routers"][ID1-1]["subNets"].append([currentNet,network["AS"][i]["subNets"][j][1]])
                    
            for interface in network["routers"][ID2-1]["interface"]:
                if interface["neighbor"] != [] and interface["neighbor"] == [ID1] :
                    interface["address"] = [calcIP(currentNet,2),network["AS"][i]["subNets"][j][1]]
                    network["routers"][ID2-1]["subNets"].append([currentNet,network["AS"][i]["subNets"][j][1]])

    # Gestion pour les InterAS
    for k in range(0,len(InterASlinks["Links"])):
        currentNet = network["InterAS"]["subNets"][k][0]
        ID1,ID2 = list(InterASlinks["Links"].keys())[k]
        addressStatic = False
        ipStatic = ([],[])
        
        for interface in network["routers"][ID1-1]["interface"]:
            if interface["neighbor"] != [] and interface["neighbor"] == [ID2] :
                if interface["address"] == "" :
                    interface["address"] = [calcIP(currentNet,1),network["InterAS"]["subNets"][k][1]]
                    network["routers"][ID1-1]["subNets"].append([currentNet,network["InterAS"]["subNets"][k][1]])
                else :
                    addressStatic = True
                    ipStatic = (interface["address"],[])


                
        for interface in network["routers"][ID2-1]["interface"]:
            if interface["neighbor"] != [] and interface["neighbor"] == [ID1] :
                if interface["address"] == "" :
                    interface["address"] = [calcIP(currentNet,2),network["InterAS"]["subNets"][k][1]]
                    network["routers"][ID2-1]["subNets"].append([currentNet,network["InterAS"]["subNets"][k][1]])
                else :
                    a,b = ipStatic
                    ipStatic = (a,interface["address"])

        if not addressStatic :
            InterASlinks["Links"][(ID1,ID2)] = ([calcIP(currentNet,1),network["InterAS"]["subNets"][k][1]],[calcIP(currentNet,2),network["InterAS"]["subNets"][k][1]])
        else:
            InterASlinks["Links"][(ID1,ID2)] = ([calcIP(currentNet,1),network["InterAS"]["subNets"][k][1]],[calcIP(currentNet,2),network["InterAS"]["subNets"][k][1]])


    network["InterAS"]["InterASlinks"] = InterASlinks
    
