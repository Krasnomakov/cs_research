302350
302700

here I get visible change in level 

use telnet to access gqrx via tcp ip 

use l to get level 

idle values
l
-56.7
l
-56.7
l
-56.8

load_cpu_2.py

l   
-44.9
l
-46.0
l
-48.5


----

have cpu_transmitter in C

And python script that uses gqrx and tcp_ip to get level 

this clearly works in slected frequencies 

----

To compile C code 
gcc -O2 -pthread cpu_transmitter.c -o cpu_transmitter

