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
  CORVUS CORAX v1.4 - PERCEPTION & INVESTIGATION ENGINE  |  Unified Intel Flow
================================================================================
  Command               | Arguments                    | Description
--------------------------------------------------------------------------------
  help                  |                              | Show commands
  version               |                              | Show tool version
  context               | [--admiralty]                | Show collected context (use --admiralty for intelligence details)
  context               | [--events] [--entities]      | Show temporal event stream / entity registry
  context               | save|load [file]             | Persist / restore intelligence state
  system                | status|providers|doctor      | Platform health, LLM providers, diagnostics
  agent                 | <target> [--auto|--ask]      | Autonomous agent: plan -> approve -> act -> reflect
  evidence              | list|findings|gaps|lineage   | Evidence chain, key findings & intelligence gaps
  resolve               | <name_or_entity>             | Entity resolution: identity clustering
  pivot                 | <entity> [--depth=N]         | Cross-entity pivoting: BFS graph traversal
  pol                   | analyze|compare|casefile|timeline | Pattern of Life behavioral analysis
  vault                 | show|events|confirm|stats    | Intelligence vault: persistent memory
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
  wayback               | <url>                        | Wayback Machine: web history & snapshots
  phone                 | <number> [person]            | Phone analysis: format, operator prefix & candidate link
  social                | <username> [person]          | Username OSINT: multi-platform correlation
  org                   | <company> [domain] [person]  | Organization intelligence: domain/personnel mapping
  academic              | <name_or_email>              | Academic intelligence: OpenAlex, ORCID, publications
  wallet                | <address> [chain] [person]   | Crypto wallet analysis: format, chain, balance
  breach                | <email> [--sources=X,Y] [--no-onion] | Breach intel: Firefox Monitor + XposedOrNot + Ahmia + Tor exit
  github                | <username> [person]          | GitHub intelligence: profile, repos, email correlation
  geoint                | map|graph|timeline|export    | Geographical map / relationship graph visualization
  nexus                 | [analyze] [--verbose]        | Run Nexus Correlation Engine
  nexus analyze         | [--verbose]                  | Correlate & score all collected data
  nexus export html     | [filepath]                   | Export HTML intelligence dossier
  nexus export json     | [filepath]                   | Export Neo4j-ready graph JSON
  nexus export graph    | [filepath]                   | Export generic graph JSON (AI/ML ready)
================================================================================
  Notes:
    - v1.4: 18 perception source adapters (whois, dns, subdomain, tech, metadata,
      headers, asn, cert, geoip, email, breach, wayback, github, org, academic,
      phone, wallet, social) -> normalized -> eligibility-gated context writes
    - breach sources: Firefox Monitor, XposedOrNot (check-email + analytics),
      Ahmia (.onion mentions), dan.me.uk (Tor exit node match). Use --no-onion
      to skip the Ahmia .onion search. Meta-data only - never raw records.
    - Nexus commands require prior data collection (scan, footprint, etc.)
    - Use 'nexus analyze --verbose' for detailed Admiralty evidence chains
    - Use 'context --admiralty' for intelligence summary
    - Use 'context --events' for temporal event stream (Pattern of Life basis)
    - Use 'context --entities [type]' for entity registry summary
    - Use 'geoint map/graph' for visualization (open HTML in browser)
    - Use 'pol analyze <entity>' for behavioral analysis
    - Use 'vault show' for persistent memory stats
    - Default export path: logs/nexus_report.html | logs/nexus_neo4j.json | logs/nexus_graph.json
    - phone/social/org/wallet/academic/breach module relations are CANDIDATE -
      not confirmed ownership (metadata correlation, confidence-weighted)
================================================================================
"""
        self.add_note("Help information displayed", severity="info")
        return self.success(target="local", data=data)
