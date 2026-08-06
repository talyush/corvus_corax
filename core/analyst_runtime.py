"""
Context-aware analyst commentary during live module execution.
Reads the shared ContextManager graph and emits preflight + finding insights.
"""


class AnalystRuntime:
    def __init__(self, context, module_name, target_args=None):
        self.context = context
        self.module_name = module_name
        self.target_args = target_args or []

    def _data(self):
        if not self.context or not hasattr(self.context, "data"):
            return {}
        return self.context.data

    def _target(self, index=0, default=""):
        if index < len(self.target_args):
            return str(self.target_args[index]).strip()
        return default

    def preflight(self):
        handler = getattr(self, f"_preflight_{self.module_name}", None)
        if handler:
            return handler()
        return self._preflight_generic()

    def _preflight_generic(self):
        msgs = []
        data = self._data()
        relations = data.get("relations", [])
        notes = data.get("notes", [])
        if relations:
            msgs.append(
                f"Context holds {len(relations)} relation(s) — new evidence will be cross-linked automatically"
            )
        if not notes and not relations:
            msgs.append("Cold start — establishing first intelligence baseline for this session")
        elif notes:
            msgs.append(f"Building on {len(notes)} prior analyst note(s) in context")
        return msgs

    def _preflight_dns(self):
        msgs = self._preflight_generic()
        domain = self._target().lower()
        if not domain:
            return msgs
        if domain in self._data().get("dns_records", {}):
            msgs.append(f"Existing DNS profile for '{domain}' — refreshing & merging")
        dom_ctx = self._data().get("domains", {}).get(domain, {})
        if dom_ctx.get("ips"):
            msgs.append(f"Context maps '{domain}' to {len(dom_ctx['ips'])} IP(s) — will reconcile")
        return msgs

    def _preflight_footprint(self):
        msgs = self._preflight_generic()
        domain = self._target().lower()
        if domain in self._data().get("domains", {}):
            msgs.append(f"'{domain}' already in domain graph — resolution will update mappings")
        return msgs

    def _preflight_scan(self):
        msgs = self._preflight_generic()
        ip = self._target()
        ports = self._data().get("ips", {}).get(ip, {}).get("ports", [])
        if ports:
            msgs.append(f"Context already lists {len(ports)} port(s) on {ip} — scan will extend coverage")
        return msgs

    def _preflight_netscan(self):
        msgs = self._preflight_generic()
        network = self._target()
        if network:
            msgs.append(f"Host discovery scope: {network} — live hosts feed the context IP graph")
        return msgs

    def _preflight_geoip(self):
        msgs = self._preflight_generic()
        ip = self._target()
        geo = self._data().get("ips", {}).get(ip, {}).get("geo", {})
        if geo:
            msgs.append(f"Prior geo data for {ip} — refreshing location intelligence")
        return msgs

    def _preflight_subdomain(self):
        msgs = self._preflight_generic()
        domain = self._target().lower()
        known = [d for d in self._data().get("domains", {}) if d.endswith(f".{domain}") or d == domain]
        if known:
            msgs.append(f"Context already tracks {len(known)} host(s) under '{domain}' — expanding surface")
        return msgs

    def _preflight_email(self):
        msgs = self._preflight_generic()
        domain = self._target().lower()
        if domain not in self._data().get("dns_records", {}):
            msgs.append(f"No DNS context for '{domain}' — run 'dns {domain}' first for richer analysis")
        else:
            msgs.append(f"DNS context available — correlating MX/SPF/DMARC with email patterns")
        return msgs

    def _preflight_cert(self):
        msgs = self._preflight_generic()
        host = self._target().lower()
        certs = self._data().get("certificates", {})
        if certs:
            msgs.append(f"{len(certs)} certificate(s) in context — SAN overlap will be evaluated")
        if host in self._data().get("dns_records", {}):
            msgs.append(f"DNS records on file for '{host}' — cert SANs may reveal hidden hosts")
        return msgs

    def _preflight_headers(self):
        msgs = self._preflight_generic()
        domain = self._target().lower().replace("https://", "").replace("http://", "").split("/")[0]
        if domain in self._data().get("http_headers", {}):
            msgs.append(f"Prior header audit exists for '{domain}' — re-evaluating posture")
        return msgs

    def _preflight_metadata(self):
        msgs = self._preflight_generic()
        domain = self._target().lower().replace("https://", "").replace("http://", "").split("/")[0]
        if domain in self._data().get("metadata_intel", {}):
            msgs.append(f"Metadata already collected for '{domain}' — refreshing fingerprints")
        return msgs

    def _preflight_tech(self):
        msgs = self._preflight_generic()
        domain = self._target().lower().replace("https://", "").replace("http://", "").split("/")[0]
        if domain in self._data().get("tech_intel", {}):
            msgs.append(f"Tech stack profile exists for '{domain}' — re-fingerprinting")
        hdr = self._data().get("http_headers", {}).get(domain)
        if hdr:
            msgs.append("HTTP header context available — cross-referencing server/runtime signals")
        return msgs

    def _preflight_crawl(self):
        msgs = self._preflight_generic()
        msgs.append("Surface mapping mode — links & forms may reveal admin panels or auth endpoints")
        return msgs

    def _preflight_nexus(self):
        msgs = self._preflight_generic()
        data = self._data()
        entity_count = (
            len(data.get("ips", {}))
            + len(data.get("domains", {}))
            + len(data.get("dns_records", {}))
        )
        if entity_count < 2:
            msgs.append("Sparse context — run recon modules first for meaningful correlation")
        else:
            msgs.append(f"Correlating across {entity_count}+ entity buckets in context graph")
        derived = data.get("derived_relations", [])
        if derived:
            msgs.append(f"{len(derived)} derived relation(s) already computed — engine will refresh")
        return msgs

    def _preflight_asn(self):
        msgs = self._preflight_generic()
        ip = self._target()
        if ip in self._data().get("ips", {}):
            msgs.append(f"{ip} exists in IP graph — ASN data will enrich routing context")
        return msgs

    def _preflight_whois(self):
        msgs = self._preflight_generic()
        target = self._target()
        if target in self._data().get("domains", {}):
            msgs.append(f"'{target}' in domain graph — WHOIS will add registration intelligence")
        return msgs
