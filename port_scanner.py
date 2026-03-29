
import socket
import time

host = "scanme.nmap.org"
start = time.time()
print(f"Scanning {host}....")
for port in range(1,101):
    s = socket.socket()
    s.settimeout(0.5)
    if s.connect_ex((host, port)) == 0:
        print(f"[+] PORT {port} open")
    s.close()

print(f"Ready For {time.time()-start:.1f}seconds")
