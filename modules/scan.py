import socket
import time
from concurrent.futures import ThreadPoolExecutor
from core.module_base import BaseModule

# En çok kullanılan portlar ve ilişkili servis haritası
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "TELNET",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    135: "RPC",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "Oracle",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt"
}

TOP_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 8080, 8443]


class ScanModule(BaseModule):
    name = "scan"
    description = "Port scanner"
    category = "network"
    risk_level = 3

    def scan_port(self, ip, port, timeout=1.0):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        args = self.target or []

        if not args:
            return self.error("Usage: scan <ip> [quick|normal|slow] [start] [end]")

        ip = args[0]
        
        # Varsayılan mod 'quick'
        mode = "quick"
        if len(args) > 1:
            mode = args[1].lower()

        if mode not in ("quick", "normal", "slow"):
            return self.error(f"Unknown mode: {mode}. Choose from: quick, normal, slow", target=ip)

        # Hangi portların taranacağını belirleme
        ports_to_scan = []
        if mode == "quick":
            ports_to_scan = TOP_PORTS
        else:
            # Yapılandırmadan varsayılan port aralığını oku
            start = 1
            end = 1024
            if self.config:
                port_range = self.config.get("scan_defaults", {}).get("normal_port_range", [1, 1024])
                if len(port_range) == 2:
                    start = int(port_range[0])
                    end = int(port_range[1])

            # Komut satırı argümanları ile ez
            if len(args) > 2:
                try:
                    start = int(args[2])
                except ValueError:
                    return self.error(f"Invalid start port: {args[2]}", target=ip)
            if len(args) > 3:
                try:
                    end = int(args[3])
                except ValueError:
                    return self.error(f"Invalid end port: {args[3]}", target=ip)

            if start > end or start < 1 or end > 65535:
                return self.error(f"Invalid port range: {start}-{end}", target=ip)

            ports_to_scan = list(range(start, end + 1))

        # Zaman aşımı ve iş parçacığı ayarları
        timeout = 1.0
        if self.config:
            timeout = float(self.config.get("timeout", 1.0))

        results = []

        if mode in ("normal", "quick"):
            # Yapılandırmadan maksimum iş parçacığı sayısını oku
            max_workers = 100
            if self.config:
                max_workers = int(self.config.get("scan_defaults", {}).get("max_threads", 100))

            # ThreadPoolExecutor ile paralel tarama gerçekleştir
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_port = {
                    executor.submit(self.scan_port, ip, port, timeout): port 
                    for port in ports_to_scan
                }
                
                # Gelecekteki sonuçları topla (sırayla işleme)
                for future in future_to_port:
                    port = future_to_port[future]
                    try:
                        is_open = future.result()
                        if is_open:
                            service_name = self.detect_service(port)
                            results.append({
                                "port": port,
                                "service": service_name
                            })
                            if self.context:
                                self.context.add_port(ip, port, service_name)
                            self.add_note(
                                text=f"Port {port} ({service_name}) discovered open on {ip}",
                                severity="info"
                            )
                            self.add_relation(
                                src_type="ip",
                                src_value=ip,
                                relation="has_open_port",
                                dst_type="port",
                                dst_value=f"{port}/{service_name}",
                                evidence="port scan"
                            )
                    except Exception as e:
                        self.logger.error(f"Error scanning port {port}: {e}")

        elif mode == "slow":
            # Yavaş tarama (sıralı ve gecikmeli) - Stealth amacını korur
            delay = 0.3
            if self.config:
                delay = float(self.config.get("scan_defaults", {}).get("slow_scan_delay", 0.3))

            for port in ports_to_scan:
                if self.scan_port(ip, port, timeout):
                    service_name = self.detect_service(port)
                    results.append({
                        "port": port,
                        "service": service_name
                    })
                    if self.context:
                        self.context.add_port(ip, port, service_name)
                    self.add_note(
                        text=f"Port {port} ({service_name}) discovered open on {ip}",
                        severity="info"
                    )
                    self.add_relation(
                        src_type="ip",
                        src_value=ip,
                        relation="has_open_port",
                        dst_type="port",
                        dst_value=f"{port}/{service_name}",
                        evidence="port scan"
                    )
                time.sleep(delay)

        return self.success(
            target=ip,
            data={
                "ip": ip,
                "mode": mode,
                "open_ports": sorted(results, key=lambda x: x["port"])
            }
        )