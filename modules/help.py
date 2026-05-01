from core.module_base import BaseModule

class HelpModule(BaseModule):
    name = "help"

    def execute(self):
        data = """
Available Commands:

scan <ip> <mode> ... -> normal/slow/banner/subnet scan
help                 -> show commands
version              -> show tool version
footprint <domain>   -> get IP and hostname
geoip <ip>           -> get geolocation info
netscan <ip/network> -> scan network
context              -> show clean context summary
"""
        return self.success(target="local", data=data)