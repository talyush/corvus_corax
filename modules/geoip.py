import sys
print("SYS: PATH:", sys.path)

import json
import urllib.request

name = "geoip"

def run(args):

    if not args:
        print("usage: geoip <ip>")
        return

    ip = args[0]

    try:
        url = f"http://ip-api.com/json/{ip}"
        response = urllib.request.urlopen(url, timeout=5)
        data = json.loads(response.read().decode())

        if data["status"] != "success":
            print("Lookup failed.")
            return

        print(f"[+] IP       : {data['query']}")
        print(f"[+] Country  : {data['country']}")
        print(f"[+] Region   : {data['regionName']}")
        print(f"[+] City     : {data['city']}")
        print(f"[+] ISP      : {data['isp']}")
        print(f"[+] Org      : {data['org']}")
        print(f"[+] Lat/Lon  : {data['lat']}, {data['lon']}")

    except Exception as e:
        print("Error:", e)