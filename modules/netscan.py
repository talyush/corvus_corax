import socket
import ipaddress
import threading

name = "netscan"

def scan_host(ip, port=80):
    try:
        s = socket.socket()
        s.settimeout(0.5)
        s.connect((str(ip), port))
        print(f"[+] Host up: {ip}")
        s.close()
    except:
        pass


def run(args):

    if not args:
        print("usage: netscan <network>")
        print("example: netscan 192.168.1.0/24")
        return

    network = args[0]

    try:
        net = ipaddress.ip_network(network, strict=False)
    except:
        print("Invalid network format.")
        return

    print(f"[*] Scanning network: {net}")

    threads = []

    for ip in net.hosts():
        t = threading.Thread(target=scan_host, args=(ip,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("[✓] Scan finished.")