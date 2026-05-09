import socket
import ipaddress
import threading
from core.module_base import BaseModule

class NetscanModule(BaseModule):
    name = "netscan"

    def _scan_defaults(self):
        cfg = self.config or {}
        return cfg.get("scan_defaults", {}) if isinstance(cfg.get("scan_defaults", {}), dict) else {}

    def _scan_port(self):
        ports = self._scan_defaults().get("host_probe_ports", [80])
        if isinstance(ports, list) and ports:
            try:
                return int(ports[0])
            except Exception:
                pass
        return 80

    def _connect_timeout(self):
        defaults = self._scan_defaults()
        return float(defaults.get("host_probe_timeout", (self.config or {}).get("timeout", 0.5)))

    def _max_threads(self):
        configured_threads = int((self.config or {}).get("threads", 20))
        ceiling = int(self._scan_defaults().get("max_threads", 200))
        return max(1, min(configured_threads, max(1, ceiling)))

    def scan_host(self, ip, port=80):
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect((str(ip), port))
            s.close()

            with self.lock:
                self.alive_hosts.append({
                    "ip": str(ip),
                    "port": port
                })

        except:
            pass

    def run(self):
        args = self.target

        if not args:
            raise ValueError("Usage: netscan <network>")

        network = args[0]

        net = ipaddress.ip_network(network, strict=False)

        threads = []

        for ip in net.hosts():
            t = threading.Thread(target=self.scan_host, args=(ip,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return {
            "network": network,
            "alive_hosts": self.alive_hosts,
            "count": len(self.alive_hosts)
        }
