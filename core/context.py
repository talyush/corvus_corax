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
        """O ana kadar elde edilen tüm benzersiz verileri döner."""
        return json.dumps(self.data, indent=4)
