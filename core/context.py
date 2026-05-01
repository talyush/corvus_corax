import json

class ContextManager:
    """
    Tüm modüllerden gelen Recon verisini tutan Çoklu Bağlam Analizi sınıfı.
    Sosyal mühendislik ve diğer hedefler için yapılandırılmış merkezi bellek.
    """
    def __init__(self):
        self.data = {
            "ips": {},        # ip: {ports: [], geo: {}, hostname: ""}
            "domains": {},    # domain: {ips: []}
            "notes": []       # genel notlar / tespitler
        }

    def add_ip(self, ip):
        """Merkezi zihne bir IP adresi ekler."""
        if ip not in self.data["ips"]:
            self.data["ips"][ip] = {"ports": [], "geo": {}, "hostname": None}

    def add_port(self, ip, port, service="Unknown"):
        """Bir IP'ye ait port ve servis bilgisini bağlar."""
        self.add_ip(ip)
        port_info = {"port": port, "service": service}
        if port_info not in self.data["ips"][ip]["ports"]:
            self.data["ips"][ip]["ports"].append(port_info)

    def add_geo(self, ip, geo_data):
        """Bir IP'ye Coğrafi lokasyon bilgilerini bağlar."""
        self.add_ip(ip)
        self.data["ips"][ip]["geo"].update(geo_data)

    def add_domain_mapping(self, domain, ip):
        """Domain ile IP adresini haritalar."""
        if domain not in self.data["domains"]:
            self.data["domains"][domain] = {"ips": []}
        if ip not in self.data["domains"][domain]["ips"]:
            self.data["domains"][domain]["ips"].append(ip)
        
        # IP'nin hostname bilgisini de dönüp güncelleyelim
        self.add_ip(ip)
        self.data["ips"][ip]["hostname"] = domain

    def get_summary(self):
        """O ana kadar elde edilen verileri temizleyip döner."""
        return json.dumps(self.get_clean_data(), indent=4, ensure_ascii=False)

    def get_clean_data(self):
        """
        Nexus uyumluluğu için veri şemasını korur,
        sadece boş/noise alanları temizler.
        """
        clean_ips = {}
        for ip, ip_data in self.data["ips"].items():
            ports = ip_data.get("ports", [])
            geo = {k: v for k, v in ip_data.get("geo", {}).items() if v not in (None, "", [])}
            hostname = ip_data.get("hostname")
            clean_ips[ip] = {
                "ports": ports,
                "geo": geo,
                "hostname": hostname if hostname else None,
            }

        clean_domains = {}
        for domain, domain_data in self.data["domains"].items():
            ips = domain_data.get("ips", [])
            if ips:
                clean_domains[domain] = {"ips": ips}

        clean_notes = [n for n in self.data["notes"] if n]

        return {
            "ips": clean_ips,
            "domains": clean_domains,
            "notes": clean_notes,
        }
