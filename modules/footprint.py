import socket

name = "footprint"

def run(args):

    if not args:
        print("usage: footprint <domain>")
        return

    target = args[0]

    try:
        ip = socket.gethostbyname(target)
        print(f"[+] IP Address : {ip}")

        host = socket.gethostbyaddr(ip)
        print(f"[+] Hostname   : {host[0]}")

    except Exception as e:
        print("Error:", e)