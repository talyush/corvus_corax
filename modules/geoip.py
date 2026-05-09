import json
import urllib.request
from core.module_base import BaseModule

class GeoipModule(BaseModule):
    name = "geoip"

    def execute(self):
        args = self.target
        if not args:
            return self.error("usage: geoip <ip>")

        ip = args[0]
        timeout = float((self.config or {}).get("timeout", 5))
        user_agent = (self.config or {}).get("user_agent", "CorvusCorax/0.3")

        url = f"http://ip-api.com/json/{ip}"
        response = urllib.request.urlopen(url, timeout=5)

        data = json.loads(response.read().decode())

        if data.get("status") != "success":
            raise ValueError("Lookup failed")

        return {
            "ip": data.get("query"),
            "country": data.get("country"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "isp": data.get("isp"),
            "org": data.get("org"),
            "lat": data.get("lat"),
            "lon": data.get("lon")
        }
