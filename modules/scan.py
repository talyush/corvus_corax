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
    description = "Port scanner"
    category = "network"
    risk_level = 3

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

    def execute(self):
        args = self.target

        if not args or len(args) < 2:
            return self.error("Usage: scan <ip> normal <start> <end>")

        ip = args[0]
        mode = args[1]

        results = []

        if mode == "normal":
            start = int(args[2])
            end = int(args[3])

            for port in range(start, end + 1):
                if self.scan_port(ip, port):
                    service_name = self.detect_service(port)
                    results.append({
                        "port": port,
                        "service": service_name
                    })
                    if self.context:
                        self.context.add_port(ip, port, service_name)

        elif mode == "slow":
            start = int(args[2])
            end = int(args[3])

            for port in range(start, end + 1):
                if self.scan_port(ip, port):
                    service_name = self.detect_service(port)
                    results.append({
                        "port": port,
                        "service": service_name
                    })
                    if self.context:
                        self.context.add_port(ip, port, service_name)
                time.sleep(0.3)

        else:
            return self.error("Unknown mode", target=ip)

        return self.success(
            target=ip,
            data={
                "ip": ip,
                "mode": mode,
                "open_ports": results
            }
        )