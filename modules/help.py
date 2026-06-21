from core.module_base import BaseModule

class HelpModule(BaseModule):
    name = "help"

    def execute(self):
        data = """
================================================================================
  CORVUS CORAX v0.7 — NEXUS INTELLIGENCE  |  Modular Recon Framework
================================================================================
  Command               | Arguments                    | Description
--------------------------------------------------------------------------------
  help                  |                              | Show commands
  version               |                              | Show tool version
  context               |                              | Show collected context
  scan                  | <ip> <mode> ...              | Port scan (normal/slow/banner/subnet)
  netscan               | <ip/network>                 | Scan a network/subnet
  footprint             | <domain>                     | Get IP and hostname info
  geoip                 | <ip>                         | Get geolocation info
  whois                 | <domain|ip>                  | Run WHOIS lookup
  subdomain             | <domain> [wordlist]          | Passive subdomain enum (crt.sh+wordlist)
  tech                  | <url_or_host>                | Detect server, framework & tech stack
  crawl                 | <url_or_host>                | Get title, links, forms & status code
  nexus                 | [analyze]                    | Run Nexus Correlation Engine
  nexus analyze         |                              | Correlate & score all collected data
  nexus export html     | [filepath]                   | Export HTML intelligence dossier
  nexus export json     | [filepath]                   | Export Neo4j-ready graph JSON
================================================================================
  Notes:
    - Nexus commands require prior data collection (scan, footprint, etc.)
    - Default export path: logs/nexus_report.html | logs/nexus_neo4j.json
    - Use 'context' at any time to inspect the collected intelligence graph
================================================================================
"""
        self.add_note("Help information displayed", severity="info")
        return self.success(target="local", data=data)