import socket
from core.module_base import BaseModule

class FootprintModule(BaseModule):
    name = "footprint"
    
    def execute(self):
        args = self.target
        if not args:
            print("usage: footprint <domain>")
            return {"module": self.name, "status": "error", "error": "eksik argüman"}

        target = args[0]

        try:
            ip = socket.gethostbyname(target)
            print(f"[+] IP Address : {ip}")
            
            # Context'e ekle
            if self.context:
                self.context.add_domain_mapping(target, ip)

            try:
                host = socket.gethostbyaddr(ip)
                print(f"[+] Hostname   : {host[0]}")
                if self.context:
                    self.context.add_domain_mapping(host[0], ip)
            except:
                pass

        except Exception as e:
            print("Error:", e)
            return {"module": self.name, "status": "error", "error": str(e)}

        return {"module": self.name, "status": "completed"}
