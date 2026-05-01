import socket
import ipaddress
import threading
from core.module_base import BaseModule

class NetscanModule(BaseModule):
    name = "netscan"

    def scan_host(self, ip, live_hosts, lock, port=80):
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect((str(ip), port))
            with lock:
                live_hosts.append(str(ip))
            if self.context:
                self.context.add_ip(str(ip))
                self.context.add_port(str(ip), port, "HTTP/Open")
            s.close()
        except Exception:
            pass

    def execute(self):
        args = self.target
        if not args:
            return self.error("usage: netscan <network>")

        network = args[0]
        try:
            net = ipaddress.ip_network(network, strict=False)
        except Exception:
            return self.error("invalid network format", target=network)

        live_hosts = []
        lock = threading.Lock()
        threads = []

        for ip in net.hosts():
            t = threading.Thread(target=self.scan_host, args=(ip, live_hosts, lock))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return self.success(
            target=network,
            data={
                "network": str(net),
                "live_hosts": sorted(live_hosts),
                "count": len(live_hosts),
            },
        )
