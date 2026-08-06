import json
import urllib.request
from core.module_base import BaseModule

class GeoipModule(BaseModule):
    name = "geoip"

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: geoip <ip>")

        ip = args[0].strip()
        timeout = float((self.config or {}).get("timeout", 5.0))
        user_agent = (self.config or {}).get("user_agent", "CorvusCorax/0.3")

        inv = self.begin_investigation(
            f"Determine physical location & ISP attribution for IP {ip}",
            ["GEOIP QUERY", "ISP ATTRIBUTION"]
        )

        with inv.phase(0):
            def fetch_geo():
                url = f"http://ip-api.com/json/{ip}"
                request = urllib.request.Request(url, headers={"User-Agent": user_agent})
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8", errors="ignore"))

            try:
                data = self.status_step(f"Querying GeoIP location database for {ip}", work=fetch_geo)
            except Exception as e:
                return self.error(f"GeoIP query failed: {e}", target=ip)

        with inv.phase(1):
            self.status_step(f"Resolving ISP attribution & geographic coordinates for {ip}")

        if data is None:
            return self.error("GeoIP lookup returned no data", target=ip)

        if data.get("status") != "success":
            return self.error(data.get("message", "Lookup failed"), target=ip)

        # Extract location details
        country = data.get("country", "")
        region = data.get("regionName", "")
        city = data.get("city", "")
        isp = data.get("isp", "")
        org = data.get("org", "")
        lat = data.get("lat")
        lon = data.get("lon")

        geo_payload = {"country": country, "region": region, "city": city,
                       "isp": isp, "org": org, "lat": lat, "lon": lon}

        if self.context:
            self.context.add_geo(ip, geo_payload)

        self.add_note(
            text=f"GeoIP intelligence gathered for {ip}: located in {city}, {country} (ISP: {isp})",
            severity="info"
        )
        self.add_relation(
            src_type="ip", src_value=ip,
            relation="located_in",
            dst_type="location",
            dst_value=f"{city}, {region}, {country}".strip(", "),
            evidence="geoip lookup"
        )

        return self.success(
            target=ip,
            data={"ip": ip, "country": country, "region": region,
                  "city": city, "isp": isp, "org": org, "lat": lat, "lon": lon}
        )
