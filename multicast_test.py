# Based on https://stackoverflow.com/a/1794373/869402


import socket
import struct
from multiprocessing import Process
import time

MCAST_GRP = '224.0.0.251'
MCAST_PORT = 5353
IS_ALL_GROUPS = True

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
if IS_ALL_GROUPS:
    # on this port, receives ALL multicast groups
    sock.bind(('', MCAST_PORT))
else:
    # on this port, listen ONLY to MCAST_GRP
    sock.bind((MCAST_GRP, MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def receiver():
	print("Running receiver ...")
	rec = ""
	while not rec == "robot 9":
		rec = sock.recv(10240)
		print(rec)
	print("Shutting down receiver ...")

p = Process(target=receiver)
p.start()



# Now send the multicast messages to the receiver

MULTICAST_TTL = 2

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)


for i in range(10):
	sock.sendto("robot " + str(i), (MCAST_GRP, MCAST_PORT))

TIMEOUT = 5
start = time.time()
while time.time() - start <= TIMEOUT:
    if any(p.is_alive()):
        time.sleep(.1)
    else:
        # All the processes are done, break now.
        exit(0)
else:
    # We only enter this if we didn't 'break' above.
    print("timed out, killing all processes")
    p.terminate()
    p.join()
    exit(1)


