import socket
from core.module_base import BaseModule

class FootprintModule(BaseModule):
    name = "footprint"
    
    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: footprint <domain>")

        target = args[0].strip().lower()

        inv = self.begin_investigation(
            f"Perform forward DNS resolution & PTR reverse lookup for domain {target}",
            ["FORWARD RESOLUTION", "REVERSE PTR LOOKUP"]
        )

        ip = None
        with inv.phase(0):
            def resolve_forward():
                nonlocal ip
                ip = socket.gethostbyname(target)

            try:
                self.status_step(f"Resolving IPv4 address for domain {target}", work=resolve_forward)
            except Exception as e:
                return self.error(f"DNS resolution failed: {e}", target=target)

        hostname = None

        with inv.phase(1):
            # Central context mapping
            if self.context:
                self.context.add_domain_mapping(target, ip)

            self.add_note(
                text=f"footprint resolved {target} -> {ip}",
                severity="info"
            )
            self.add_relation(
                src_type="domain", src_value=target,
                relation="resolves_to",
                dst_type="ip", dst_value=ip,
                evidence="footprint dns lookup"
            )

            def do_reverse():
                nonlocal hostname
                host = socket.gethostbyaddr(ip)
                hostname = host[0]

            try:
                self.status_step(f"Performing reverse PTR lookup for {ip}", work=do_reverse)
                if hostname and self.context:
                    self.context.add_domain_mapping(hostname, ip)
                if hostname:
                    self.add_relation(
                        src_type="ip", src_value=ip,
                        relation="reverse_resolves_to",
                        dst_type="domain", dst_value=hostname,
                        evidence="footprint reverse dns lookup"
                    )
            except Exception:
                pass

        return self.success(
            target=target,
            data={"domain": target, "ip": ip, "hostname": hostname},
        )
