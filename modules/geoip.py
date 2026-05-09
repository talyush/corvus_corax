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

        try:
            url = f"http://ip-api.com/json/{ip}"
            request = urllib.request.Request(url, headers={"User-Agent": user_agent})
            response = urllib.request.urlopen(request, timeout=timeout)
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
                self.context.add_note(
                    text=f"geoip lookup completed for {result_data['ip']}",
                    source="geoip",
                    severity="info",
                )
                if result_data.get("country"):
                    self.context.add_relation(
                        "ip",
                        result_data["ip"],
                        "located_in",
                        "country",
                        result_data["country"],
                        "geoip",
                    )

        except Exception as e:
            return self.error(e, target=ip)

        return self.success(target=ip, data=result_data)
