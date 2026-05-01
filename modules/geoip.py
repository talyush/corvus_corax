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

        try:
            url = f"http://ip-api.com/json/{ip}"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode())

            if data["status"] != "success":
                return self.error("lookup failed", target=ip)

            result_data = {
                "ip": data.get("query"),
                "country": data.get("country"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "isp": data.get("isp"),
                "org": data.get("org"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
            }

            # Hedef veriyi ContextManager'a (Zihin) aktaralım
            if self.context:
                geo_info = {
                    "country": result_data["country"],
                    "region": result_data["region"],
                    "city": result_data["city"],
                    "isp": result_data["isp"],
                    "org": result_data["org"],
                    "latitude": result_data["lat"],
                    "longitude": result_data["lon"]
                }
                self.context.add_geo(result_data["ip"], geo_info)

        except Exception as e:
            return self.error(e, target=ip)

        return self.success(target=ip, data=result_data)
