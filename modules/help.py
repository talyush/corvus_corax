from core.module_base import BaseModule

class HelpModule(BaseModule):
    name = "help"

    def execute(self):
        data = """
Available Commands:

scan <ip>            -> ping + port scan
help                 -> show commands
version              -> show tool version
footprint <domain>   -> get IP and hostname
geoip <ip>           -> get geolocation info
netscan <ip/network> -> scan network
"""

        return {
            "module": self.name,
            "target": "local",
            "status": "success",
            "data": data
        }