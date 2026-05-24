from core.module_base import BaseModule

class HelpModule(BaseModule):
    name = "help"

    def execute(self):
        data = """
================================================================================
  AVAILABLE COMMANDS
================================================================================
  Command     | Arguments            | Description
--------------------------------------------------------------------------------
  help        |                      | Show commands
  version     |                      | Show tool version
  context     |                      | Show clean context summary
  scan        | <ip> <mode> ...      | normal/slow/banner/subnet scan
  netscan     | <ip/network>         | Scan network
  footprint   | <domain>             | Get IP and hostname
  geoip       | <ip>                 | Get geolocation info
  whois       | <domain|ip>          | Run whois lookup
  subdomain   | <domain> [wordlist]  | Passive subdomain enum (crt.sh+wordlist)
  tech        | <url_or_host>        | Detect server, x-powered-by & framework
  crawl       | <url_or_host>        | Get title, links, forms and status code
================================================================================
"""
        self.add_note("Help information displayed", severity="info")
        return self.success(target="local", data=data)