import socket
import ipaddress
import threading
from core.module_base import BaseModule

class NetscanModule(BaseModule):
    name = "netscan"

    def scan_host(self, ip, port=80):
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect((str(ip), port))
            print(f"[+] Host up: {ip}")
            if self.context:
                self.context.add_ip(str(ip))
                self.context.add_port(str(ip), port, "HTTP/Open")
            s.close()
        except:
            pass

    def execute(self):
        args = self.target
        if not args:
            print("usage: netscan <network>")
            print("example: netscan 192.168.1.0/24")
            return {"module": self.name, "status": "error", "error": "eksik argüman"}

        network = args[0]
        try:
            net = ipaddress.ip_network(network, strict=False)
        except:
            print("Invalid network format.")
            return {"module": self.name, "status": "error", "error": "geçersiz format"}

        print(f"[*] Scanning network: {net}")
        threads = []

        for ip in net.hosts():
            t = threading.Thread(target=self.scan_host, args=(ip,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        print("[✓] Scan finished.")
        return {"module": self.name, "status": "completed"}
