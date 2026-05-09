import socket
import time
from core.module_base import BaseModule

COMMON_PORTS = {
    21:"FTP",
    22:"SSH",
    23:"TELNET",
    25:"SMTP",
    53:"DNS",
    80:"HTTP",
    110:"POP3",
    143:"IMAP",
    443:"HTTPS",
    3306:"MySQL",
    3389:"RDP"
}

class ScanModule(BaseModule):
    name = "scan"

    def _scan_defaults(self):
        cfg = self.config or {}
        return cfg.get("scan_defaults", {}) if isinstance(cfg.get("scan_defaults", {}), dict) else {}

    def _connect_timeout(self):
        defaults = self._scan_defaults()
        global_timeout = (self.config or {}).get("timeout", 1.0)
        return float(defaults.get("connect_timeout", global_timeout))

    def _banner_timeout(self):
        defaults = self._scan_defaults()
        global_timeout = (self.config or {}).get("timeout", 2.0)
        return float(defaults.get("banner_timeout", global_timeout))

    def _host_probe_timeout(self):
        defaults = self._scan_defaults()
        return float(defaults.get("host_probe_timeout", 0.3))

    def _host_probe_ports(self):
        defaults = self._scan_defaults()
        ports = defaults.get("host_probe_ports", [80, 22])
        if isinstance(ports, list) and ports:
            cleaned = []
            for p in ports:
                try:
                    val = int(p)
                    if 1 <= val <= 65535:
                        cleaned.append(val)
                except Exception:
                    continue
            if cleaned:
                return cleaned
        return [80, 22]

    def _slow_delay(self):
        defaults = self._scan_defaults()
        return float(defaults.get("slow_scan_delay", 0.3))

    def _normal_range(self):
        defaults = self._scan_defaults()
        port_range = defaults.get("normal_port_range", [1, 1024])
        if isinstance(port_range, list) and len(port_range) == 2:
            try:
                start = int(port_range[0])
                end = int(port_range[1])
                if 1 <= start <= 65535 and 1 <= end <= 65535 and start <= end:
                    return [start, end]
            except Exception:
                pass
        return [1, 1024]

    def scan_port(self, ip, port, timeout=None):
        timeout = self._connect_timeout() if timeout is None else timeout
        s = socket.socket()
        s.settimeout(timeout)
        try:
            s.connect((ip, port))
            return True
        except:
            return False
        finally:
            s.close()

    def detect_service(self, port):
        return COMMON_PORTS.get(port, "Unknown")

    def banner_grab(self, ip, port):
        try:
            s = socket.socket()
            s.settimeout(self._banner_timeout())
            s.connect((ip, port))

            s.send(b"HEAD / HTTP/1.0\r\n\r\n")
            banner = s.recv(1024).decode(errors="ignore")
            s.close()
            return banner.strip()
        except:
            return None

    def normal_scan(self, ip, start, end):
        if self.context:
            self.context.add_ip(ip)
            self.context.add_note(
                text=f"scan normal started for {ip} ports {start}-{end}",
                source="scan",
                severity="info",
            )
        open_ports = []

        for port in range(start, end+1):
            if self.scan_port(ip, port):
                service = self.detect_service(port)
                open_ports.append({"port": port, "service": service})
                if self.context:
                    self.context.add_port(ip, port, service)
                    self.context.add_relation(
                        "ip", ip, "has_open_port", "port", f"{port}/{service}", "scan normal"
                    )
        return open_ports

    def slow_scan(self, ip, start, end):
        if self.context:
            self.context.add_ip(ip)
            self.context.add_note(
                text=f"scan slow started for {ip} ports {start}-{end}",
                source="scan",
                severity="info",
            )
        open_ports = []

        for port in range(start, end+1):
            if self.scan_port(ip, port):
                service = self.detect_service(port)
                open_ports.append({"port": port, "service": service})
                if self.context:
                    self.context.add_port(ip, port, service)
                    self.context.add_relation(
                        "ip", ip, "has_open_port", "port", f"{port}/{service}", "scan slow"
                    )
            time.sleep(self._slow_delay())
        return open_ports

    def banner_mode(self, ip, port):
        if self.context:
            self.context.add_ip(ip)
        
        if self.scan_port(ip, port):
            banner = self.banner_grab(ip, port)
            service = self.detect_service(port)
            if self.context:
                self.context.add_port(ip, port, service)
                self.context.add_relation(
                    "ip", ip, "has_open_port", "port", f"{port}/{service}", "scan banner"
                )
                self.context.add_note(
                    text=f"scan banner checked {ip}:{port}",
                    source="scan",
                    severity="info",
                )
            return {"port": port, "service": service, "banner": banner}
        else:
            return {"port": port, "state": "closed"}

    def subnet_scan(self, base_ip):
        base = ".".join(base_ip.split(".")[:-1])
        active_hosts = []

        for i in range(1, 255):
            ip = f"{base}.{i}"
            probe_timeout = self._host_probe_timeout()
            if any(self.scan_port(ip, port, probe_timeout) for port in self._host_probe_ports()):
                active_hosts.append(ip)
                if self.context:
                    self.context.add_ip(ip)
                    self.context.add_note(
                        text=f"scan subnet host discovered: {ip}",
                        source="scan",
                        severity="info",
                    )
        return active_hosts

    def execute(self):
        args = self.target or []
        if len(args) < 2:
            return self.error("usage: scan <ip> <normal|slow|banner|subnet> ...")

        ip = args[0]
        mode = args[1]

        try:
            if mode == "normal":
                if len(args) >= 4:
                    start = int(args[2])
                    end = int(args[3])
                else:
                    start, end = self._normal_range()
                data = {
                    "mode": mode,
                    "range": [start, end],
                    "open_ports": self.normal_scan(ip, start, end),
                }

            elif mode == "slow":
                if len(args) >= 4:
                    start = int(args[2])
                    end = int(args[3])
                else:
                    start, end = self._normal_range()
                data = {
                    "mode": mode,
                    "range": [start, end],
                    "open_ports": self.slow_scan(ip, start, end),
                }

            elif mode == "banner":
                port = int(args[2])
                data = {
                    "mode": mode,
                    "result": self.banner_mode(ip, port),
                }

            elif mode == "subnet":
                active_hosts = self.subnet_scan(ip)
                data = {
                    "mode": mode,
                    "active_hosts": active_hosts,
                    "count": len(active_hosts),
                }

            else:
                return self.error("unknown mode", target=ip)
                
        except Exception as e:
            return self.error(e, target=ip)

        return self.success(target=ip, data=data)
