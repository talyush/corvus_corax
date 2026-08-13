from core.module_base import BaseModule

class HelpModule(BaseModule):
    name = "help"

    def execute(self):
        inv = self.begin_investigation(
            "Compile Corvus Corax command index & operational documentation",
            ["INDEX COMPILATION", "DOCUMENTATION RENDERING"]
        )
        with inv.phase(0):
            self.status_step("Loading module registry & command usage schemas")
        data = """
================================================================================
  CORVUS CORAX v0.9 — INTELLIGENCE COLLECTION EXPANSION  |  Modular Recon Framework
================================================================================
  Command               | Arguments                    | Description
--------------------------------------------------------------------------------
  help                  |                              | Show commands
  version               |                              | Show tool version
  context               | [--admiralty]                | Show collected context (use --admiralty for intelligence details)
  context               | [--events] [--entities]      | Show temporal event stream / entity registry (v0.9)
  scan                  | <ip> <mode> ...              | Port scan (normal/slow/banner/subnet)
  netscan               | <ip/network>                 | Scan a network/subnet
  footprint             | <domain>                     | Get IP and hostname info
  geoip                 | <ip>                         | Get geolocation info
  whois                 | <domain|ip>                  | Run WHOIS lookup
  dns                   | <domain> [selector]          | Run DNS & email security (SPF/DMARC/DKIM/CAA)
  email                 | <domain> [sample1,sample2]   | Email provider, DMARC contacts & address patterns
  subdomain             | <domain> [wordlist]          | Passive subdomain enum (crt.sh+HackerTarget+RapidDNS)
  tech                  | <url_or_host>                | Detect server, framework & tech stack
  asn                   | <ip_address>                 | ASN lookup: organization, CIDR & related IPs
  crawl                 | <url_or_host>                | Get title, links, forms & status code
  cert                  | <host> [port]                | Fetch & analyze TLS certificate intelligence
  headers               | <url_or_host>                | Fetch & analyze HTTP headers, security & cookies
  metadata              | <url_or_host>                | Collect robots.txt, sitemap, favicon hash & security.txt
  phone                 | <number> [person]            | Phone analysis: format, operator prefix & candidate link (v0.9)
  social                | <username> [person]          | Username OSINT: multi-platform correlation (v0.9)
  org                   | <company> [domain] [person]  | Organization intelligence: domain/personnel mapping (v0.9)
  academic              | <name_or_email>              | Academic intelligence: OpenAlex, ORCID, publications (v0.9)
  wallet                | <address> [chain] [person]   | Crypto wallet analysis: format, chain, balance (v0.9)
  breach                | <email> [--sources=X,Y]      | Breach intelligence: Firefox Monitor + k-anonymity (v0.9)
  github                | <username> [person]          | GitHub intelligence: profile, repos, email correlation (v0.9)
  wayback               | <url>                        | Wayback Machine: web history & snapshots (v0.9)
  geoint                | map|graph|timeline|export    | Geographical map / relationship graph visualization (v0.9)
  context               | save|load [file]             | Persist / restore intelligence state (v0.9)
  nexus                 | [analyze] [--verbose]        | Run Nexus Correlation Engine
  nexus analyze         | [--verbose]                  | Correlate & score all collected data
  nexus export html     | [filepath]                   | Export HTML intelligence dossier
  nexus export json     | [filepath]                   | Export Neo4j-ready graph JSON
  nexus export graph    | [filepath]                   | Export generic graph JSON (AI/ML ready)
================================================================================
  Notes:
    - Nexus commands require prior data collection (scan, footprint, etc.)
    - Use 'nexus analyze --verbose' for detailed Admiralty evidence chains
    - Use 'context --admiralty' for intelligence summary
    - Use 'context <entity> --admiralty' for detailed entity evidence
    - Use 'context --events' for temporal event stream (Pattern of Life basis)
    - Use 'context --entities [type]' for entity registry summary
    - Default export path: logs/nexus_report.html | logs/nexus_neo4j.json | logs/nexus_graph.json
    - phone/social module relations are CANDIDATE — not confirmed ownership (v0.9)
================================================================================
"""
        self.add_note("Help information displayed", severity="info")
        return self.success(target="local", data=data)