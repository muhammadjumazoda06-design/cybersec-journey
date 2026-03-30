import socket, sys, time

if len(sys.argv) < 2:
    print("Использование: python3 dns_resolver.py domains.txt")
    sys.exit(1)

domains = open(sys.argv[1]).read().splitlines()
start = time.time()

print(f"Проверяю {len(domains)} доменов...\n")

for domain in domains:
    if not domain.strip():
        continue
    try:
        ip = socket.gethostbyname(domain.strip())
        print(f"[+] {domain:<30} → {ip}")
    except socket.gaierror:
        print(f"[-] {domain:<30} → не резолвится")

print(f"\nГотово за {time.time()-start:.2f} секунд")
