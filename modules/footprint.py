import socket
from core.module_base import BaseModule

class FootprintModule(BaseModule):
    name = "footprint"
    
    def execute(self):
        args = self.target
        if not args:
            return self.error("usage: footprint <domain>")

        target = args[0]

        try:
            ip = socket.gethostbyname(target)
            hostname = None
            
            # Context'e ekle
            if self.context:
                self.context.add_domain_mapping(target, ip)
                self.context.add_note(
                    text=f"footprint resolved {target} -> {ip}",
                    source="footprint",
                    severity="info",
                )
                self.context.add_relation(
                    "domain",
                    target,
                    "resolves_to",
                    "ip",
                    ip,
                    "footprint",
                )

            try:
                host = socket.gethostbyaddr(ip)
                hostname = host[0]
                if self.context:
                    self.context.add_domain_mapping(hostname, ip)
                    self.context.add_relation(
                        "ip",
                        ip,
                        "reverse_resolves_to",
                        "domain",
                        hostname,
                        "footprint reverse dns",
                    )
            except Exception:
                pass

        except Exception as e:
            return self.error(e, target=target)

        return self.success(
            target=target,
            data={
                "domain": target,
                "ip": ip,
                "hostname": hostname,
            },
        )
