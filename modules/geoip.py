import json
import urllib.request
from core.module_base import BaseModule

class GeoipModule(BaseModule):
    name = "geoip"

    def execute(self):
        args = self.target
        if not args:
            print("usage: geoip <ip>")
            return {"module": self.name, "status": "error", "error": "eksik argüman"}

        ip = args[0]

        try:
            url = f"http://ip-api.com/json/{ip}"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode())

            if data["status"] != "success":
                print("Lookup failed.")
                return {"module": self.name, "status": "error", "error": "lookup failed"}

            print(f"[+] IP       : {data['query']}")
            print(f"[+] Country  : {data['country']}")
            print(f"[+] Region   : {data['regionName']}")
            print(f"[+] City     : {data['city']}")
            print(f"[+] ISP      : {data['isp']}")
            print(f"[+] Org      : {data['org']}")
            print(f"[+] Lat/Lon  : {data['lat']}, {data['lon']}")

            # Hedef veriyi ContextManager'a (Zihin) aktaralım
            if self.context:
                geo_info = {
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                    "latitude": data.get("lat"),
                    "longitude": data.get("lon")
                }
                self.context.add_geo(data['query'], geo_info)

        except Exception as e:
            print("Error:", e)
            return {"module": self.name, "status": "error", "error": str(e)}

        return {"module": self.name, "status": "completed"}
