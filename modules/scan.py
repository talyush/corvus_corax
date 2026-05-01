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

    def scan_port(self, ip, port, timeout=1):
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
            s.settimeout(2)
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
        open_ports = []

        for port in range(start, end+1):
            if self.scan_port(ip, port):
                service = self.detect_service(port)
                open_ports.append({"port": port, "service": service})
                if self.context:
                    self.context.add_port(ip, port, service)
        return open_ports

    def slow_scan(self, ip, start, end):
        if self.context:
            self.context.add_ip(ip)
        open_ports = []

        for port in range(start, end+1):
            if self.scan_port(ip, port):
                service = self.detect_service(port)
                open_ports.append({"port": port, "service": service})
                if self.context:
                    self.context.add_port(ip, port, service)
            time.sleep(0.3)
        return open_ports

    def banner_mode(self, ip, port):
        if self.context:
            self.context.add_ip(ip)
        
        if self.scan_port(ip, port):
            banner = self.banner_grab(ip, port)
            service = self.detect_service(port)
            if self.context:
                self.context.add_port(ip, port, service)
            return {"port": port, "service": service, "banner": banner}
        else:
            return {"port": port, "state": "closed"}

    def subnet_scan(self, base_ip):
        base = ".".join(base_ip.split(".")[:-1])
        active_hosts = []

        for i in range(1, 255):
            ip = f"{base}.{i}"
            if self.scan_port(ip, 80, 0.3) or self.scan_port(ip, 22, 0.3):
                active_hosts.append(ip)
                if self.context:
                    self.context.add_ip(ip)
        return active_hosts

    def execute(self):
        args = self.target or []
        if len(args) < 2:
            return self.error("usage: scan <ip> <normal|slow|banner|subnet> ...")

        ip = args[0]
        mode = args[1]

        try:
            if mode == "normal":
                start = int(args[2])
                end = int(args[3])
                data = {
                    "mode": mode,
                    "range": [start, end],
                    "open_ports": self.normal_scan(ip, start, end),
                }

            elif mode == "slow":
                start = int(args[2])
                end = int(args[3])
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
