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

#print(BitsToDecimal("11110111"))
print(slashToMask(22))
print(adressesLeft(slashToMask(22)))