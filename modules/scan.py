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

            print(f"[BANNER {port}] {banner.strip()}\n")
            s.close()
        except:
            print(f"[BANNER {port}] alınamadı")

    def normal_scan(self, ip, start, end):
        print("Normal scan başlatıldı\n")
        self.context.add_ip(ip)

        for port in range(start, end+1):
            if self.scan_port(ip, port):
                service = self.detect_service(port)
                print(f"[OPEN] {port} ({service})")
                self.context.add_port(ip, port, service)

    def slow_scan(self, ip, start, end):
        print("Slow scan başlatıldı\n")
        self.context.add_ip(ip)

        for port in range(start, end+1):
            if self.scan_port(ip, port):
                service = self.detect_service(port)
                print(f"[OPEN] {port} ({service})")
                self.context.add_port(ip, port, service)
            time.sleep(0.3)

    def banner_mode(self, ip, port):
        print("Banner grabbing...\n")
        self.context.add_ip(ip)
        
        if self.scan_port(ip, port):
            self.banner_grab(ip, port)
            self.context.add_port(ip, port, self.detect_service(port))
        else:
            print("Port kapalı.")

    def subnet_scan(self, base_ip):
        print("Subnet scan başlatıldı...\n")
        base = ".".join(base_ip.split(".")[:-1])

        for i in range(1, 255):
            ip = f"{base}.{i}"
            if self.scan_port(ip, 80, 0.3) or self.scan_port(ip, 22, 0.3):
                print(f"[AKTİF] {ip}")
                self.context.add_ip(ip)

    def execute(self):
        args = self.target
        if len(args) < 2:
            print("Kullanım:")
            print("scan <ip> normal <start> <end>")
            print("scan <ip> slow <start> <end>")
            print("scan <ip> banner <port>")
            print("scan <ip> subnet")
            return {"module": self.name, "status": "error", "error": "eksik parametre"}

        ip = args[0]
        mode = args[1]

        try:
            if mode == "normal":
                start = int(args[2])
                end = int(args[3])
                self.normal_scan(ip, start, end)

            elif mode == "slow":
                start = int(args[2])
                end = int(args[3])
                self.slow_scan(ip, start, end)

            elif mode == "banner":
                port = int(args[2])
                self.banner_mode(ip, port)

            elif mode == "subnet":
                self.subnet_scan(ip)

            else:
                print("Unknown mode.")
                return {"module": self.name, "status": "error", "error": "unknown mode"}
                
        except Exception as e:
            return {"module": self.name, "status": "error", "error": str(e)}

        return {"module": self.name, "status": "completed"}
