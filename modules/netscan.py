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

    def scan_host(self, ip, live_hosts, lock, port=80):
        try:
            s = socket.socket()
            s.settimeout(self._connect_timeout())
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
        port = self._scan_port()
        max_threads = self._max_threads()
        sem = threading.Semaphore(max_threads)

        def worker(host):
            with sem:
                self.scan_host(host, live_hosts, lock, port=port)

        for ip in net.hosts():
            t = threading.Thread(target=worker, args=(ip,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        if self.context:
            self.context.add_note(
                text=f"netscan completed for {network} with {len(live_hosts)} live hosts",
                source="netscan",
                severity="info",
            )
            for host in live_hosts:
                self.context.add_relation(
                    "network", str(net), "contains_live_host", "ip", host, "netscan"
                )

        return self.success(
            target=network,
            data={
                "network": str(net),
                "live_hosts": sorted(live_hosts),
                "count": len(live_hosts),
            },
        )
