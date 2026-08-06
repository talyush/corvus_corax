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

    def execute(self):
        self.alive_hosts = []
        self.lock = threading.Lock()

        args = self.target

        if not args:
            return self.error("Usage: netscan <network>")

        network = args[0]

        inv = self.begin_investigation(
            f"Execute subnet host discovery & liveness sweep for network {network}",
            ["SUBNET RANGE PARSING", "HOST DISCOVERY SWEEP"]
        )

        net = ipaddress.ip_network(network, strict=False)

        threads = []
        with inv.phase(1):
            def run_sweep():
                for ip in net.hosts():
                    t = threading.Thread(target=self.scan_host, args=(ip,))
                    t.start()
                    threads.append(t)

                for t in threads:
                    t.join()

            self.status_step(f"Probing active hosts on subnet {network}", work=run_sweep)

        # Context manager sync and relation mapping
        if self.context:
            for host in self.alive_hosts:
                ip_str = host.get("ip")
                self.context.add_ip(ip_str)
                self.add_note(
                    text=f"Active host discovered: {ip_str} on network {network}",
                    severity="info"
                )
                self.add_relation(
                    src_type="network",
                    src_value=network,
                    relation="has_active_host",
                    dst_type="ip",
                    dst_value=ip_str,
                    evidence="probe network scan"
                )

        return self.success(
            target=network,
            data={
                "network": network,
                "alive_hosts": self.alive_hosts,
                "count": len(self.alive_hosts)
            }
        )
