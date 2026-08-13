import socket
import ipaddress
import threading
import json
import urllib.request
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

    def scan_port(self, ip, port, timeout=1.0):
        """Belirli bir IP'de belirli bir portu tarar."""
        try:
            s = socket.socket()
            s.settimeout(timeout)
            s.connect((str(ip), port))
            s.close()
            return True
        except:
            return False

    def scan_ports_on_host(self, ip, ports, timeout=1.0):
        """Bir host üzerinde birden çok portu tarar."""
        open_ports = []
        for port in ports:
            if self.scan_port(ip, port, timeout):
                open_ports.append(port)
        return open_ports

    def fetch_geo(self, ip, timeout=5.0):
        """Bir IP'nin geolocation bilgisini çeker (ip-api.com)."""
        try:
            url = f"http://ip-api.com/json/{ip}"
            req = urllib.request.Request(url, headers={"User-Agent": "CorvusCorax/0.9"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if data.get("status") == "success":
                    return {
                        "country": data.get("country", ""),
                        "region": data.get("regionName", ""),
                        "city": data.get("city", ""),
                        "isp": data.get("isp", ""),
                        "org": data.get("org", ""),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                    }
        except Exception:
            pass
        return None

    def execute(self):
        self.alive_hosts = []
        self.lock = threading.Lock()

        args = self.target

        if not args:
            return self.error("Usage: netscan <network> [--ports] [--geo] [--map]")

        network = args[0]

        # Flag'leri parse et
        do_ports = "--ports" in args
        do_geo = "--geo" in args
        do_map = "--map" in args

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

        # --- v0.9: Port taraması (--ports) ---
        if do_ports:
            self.status_step("Scanning open ports on alive hosts")
            common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 8080, 8443]
            for host in self.alive_hosts:
                ip_str = host.get("ip")
                open_ports = self.scan_ports_on_host(ip_str, common_ports, timeout=0.5)
                host["open_ports"] = open_ports
                for port in open_ports:
                    self.context.add_port(ip_str, port, "tcp")
                    self.add_relation(
                        src_type="ip",
                        src_value=ip_str,
                        relation="has_open_port",
                        dst_type="port",
                        dst_value=str(port),
                        evidence="network port scan"
                    )

        # --- v0.9: Geo-tagging (--geo) ---
        if do_geo:
            self.status_step("Fetching geolocation for alive hosts")
            for host in self.alive_hosts:
                ip_str = host.get("ip")
                geo = self.fetch_geo(ip_str)
                if geo:
                    self.context.add_geo(ip_str, geo)
                    host["geo"] = geo
                    self.add_note(
                        text=f"GeoIP for {ip_str}: {geo.get('city', '')}, {geo.get('country', '')}",
                        severity="info"
                    )

        # --- v0.9: Auto map generation (--map) ---
        if do_map:
            from core.geoint import GeoIntEngine
            engine = GeoIntEngine(self.context)
            ok, msg, path = engine.export_map_html()
            if ok:
                self.add_note(msg, severity="info")

        return self.success(
            target=network,
            data={
                "network": network,
                "alive_hosts": self.alive_hosts,
                "count": len(self.alive_hosts),
                "ports_scanned": do_ports,
                "geo_enabled": do_geo,
                "map_generated": do_map
            }
        )