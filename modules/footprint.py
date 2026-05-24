import socket
from core.module_base import BaseModule

class FootprintModule(BaseModule):
    name = "footprint"
    
    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: footprint <domain>")

        target = args[0].strip().lower()

        try:
            ip = socket.gethostbyname(target)
            hostname = None
            
            # Central context mapping
            if self.context:
                self.context.add_domain_mapping(target, ip)
                
            # Add semantic notes and relations
            self.add_note(
                text=f"footprint resolved {target} -> {ip}",
                severity="info"
            )
            self.add_relation(
                src_type="domain",
                src_value=target,
                relation="resolves_to",
                dst_type="ip",
                dst_value=ip,
                evidence="footprint dns lookup"
            )

            try:
                host = socket.gethostbyaddr(ip)
                hostname = host[0]
                if self.context:
                    self.context.add_domain_mapping(hostname, ip)
                
                self.add_relation(
                    src_type="ip",
                    src_value=ip,
                    relation="reverse_resolves_to",
                    dst_type="domain",
                    dst_value=hostname,
                    evidence="footprint reverse dns lookup"
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
