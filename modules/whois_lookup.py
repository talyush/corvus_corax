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

        try:
            iana_response = self._query_server("whois.iana.org", target, timeout)
            referral_server = self._extract_referral_server(iana_response)

            final_server = referral_server or "whois.iana.org"
            final_response = self._query_server(final_server, target, timeout)

            if self.context and "." in target and " " not in target:
                self.context.add_note(
                    text=f"whois lookup completed for {target}",
                    source="whois",
                    severity="info",
                )

            return self.success(
                target=target,
                data={
                    "query": target,
                    "iana_server": "whois.iana.org",
                    "referral_server": referral_server,
                    "server_used": final_server,
                    "raw": final_response.strip(),
                },
            )
        except Exception as e:
            return self.error(e, target=target)
