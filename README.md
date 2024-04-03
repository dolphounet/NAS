# NAS

Les fonctionnalités implémentées sont : 
- MPLS BGP VPN avec 3 clients
- Bonus Route Reflector
- Bonus Manipulation des Route Targets pour que certains clients communiquent entre eux et pas d'autres (Client A et Client B communiquent avec Client C mais pas entre eux)
- Bonus RSVP (light)
  
Le programme s'exécute avec TELNET. Pour que cela fonctionne :

- Avoir la config GNS3 correspondant à l'intent file utilisé (Network_Intent.json)

  ![image](https://github.com/dolphounet/NAS/assets/154347169/d9a20995-e525-4578-989c-58a5beff3713)

- Vérifier les connections entre routeurs et les interfaces, les numéros de ports TELNET et le numéro du route reflector dans l'intent file
- Exécuter le programme main.py 
- les commandes écrites dans chaque routeur sont trouvables dans les fichiers log{num_routeur} générés au lancement du programme
