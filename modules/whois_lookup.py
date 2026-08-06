import socket
from core.module_base import BaseModule


class WhoisLookupModule(BaseModule):
    name = "whois"

    def _query_server(self, server, query, timeout):
        with socket.create_connection((server, 43), timeout=timeout) as sock:
            sock.sendall((query + "\r\n").encode("utf-8"))
            chunks = []
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data.decode("utf-8", errors="ignore"))
        return "".join(chunks)

    def _extract_referral_server(self, whois_text):
        for raw_line in whois_text.splitlines():
            line = raw_line.strip()
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key in ("refer", "whois server", "referralserver"):
                if value.lower().startswith("whois://"):
                    value = value[8:]
                return value.split("/")[0].strip()
        return None

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: whois <domain|ip>")

        target = args[0].strip()
        timeout = float(self.config.get("timeout", 3.0)) if self.config else 3.0

        inv = self.begin_investigation(
            f"Query authoritative WHOIS registry data & registrar records for {target}",
            ["IANA REFERRAL", "REGISTRAR QUERY"]
        )

        final_response = None
        final_server = "whois.iana.org"
        with inv.phase(0):
            def run_whois():
                nonlocal final_response, final_server
                iana_response = self._query_server("whois.iana.org", target, timeout)
                referral_server = self._extract_referral_server(iana_response)
                final_server = referral_server or "whois.iana.org"
                final_response = self._query_server(final_server, target, timeout)

            try:
                self.status_step(f"Querying WHOIS servers for {target}", work=run_whois)
            except Exception as e:
                return self.error(f"WHOIS lookup failed: {e}", target=target)

        self.add_relation(
            src_type="domain" if "." in target else "ip",
            src_value=target,
            relation="queried_via_whois",
            dst_type="whois_server",
            dst_value=final_server,
            evidence="whois query"
        )

        self.add_note(
            text=f"WHOIS lookup completed for {target} using server {final_server}",
            severity="info"
        )

        if not final_response:
            return self.error("WHOIS returned no data", target=target)

        return self.success(
            target=target,
            data={
                "query": target,
                "iana_server": "whois.iana.org",
                "referral_server": final_server,
                "server_used": final_server,
                "raw": final_response.strip(),
            },
        )
