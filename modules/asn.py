import urllib.request
import urllib.error
import json
import ipaddress
from core.module_base import BaseModule

class ASNModule(BaseModule):
    """
    Corvus Corax v0.8 — ASN Intelligence Module.
    
    Performs ASN lookup for IP addresses to extract:
    - AS Number and Organization
    - CIDR blocks and network ranges
    - Related IPs in the same network
    - Country and ISP information
    
    Enables Nexus correlation: shares_asn, same_provider, same_prefix
    """
    name = "asn"
    
    def __init__(self, target=None, config=None, logger=None, context=None):
        super().__init__(target, config, logger, context)
        self.api_timeout = float(self.config.get("timeout", 5.0)) if self.config else 5.0
    
    def _build_request(self, url):
        ua = "Mozilla/5.0 (compatible; CorvusCorax/0.8; ASNIntel)"
        if self.config:
            ua = self.config.get("user_agent", ua)
        return urllib.request.Request(url, headers={"User-Agent": ua})
    
    def _lookup_asn_ipapi(self, ip):
        """
        ASN lookup using ip-api.com (free, no auth required).
        Returns: dict with asn, org, cidr, country, isp, etc.
        """
        url = f"http://ip-api.com/json/{ip}"
        try:
            req = self._build_request(url)
            with urllib.request.urlopen(req, timeout=self.api_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                
                if data.get("status") == "fail":
                    self.logger.warning(f"ASN lookup failed for {ip}: {data.get('message')}")
                    return None
                
                return {
                    "asn": data.get("as"),
                    "as_number": self._extract_asn_number(data.get("as", "")),
                    "org": data.get("org"),
                    "isp": data.get("isp"),
                    "country": data.get("country"),
                    "country_code": data.get("countryCode"),
                    "cidr": data.get("cidr") or self._infer_cidr(ip, data.get("as")),
                    "query": data.get("query"),
                    "timezone": data.get("timezone"),
                    "source": "ip-api.com"
                }
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP error during ASN lookup for {ip}: {e.code}")
        except Exception as e:
            self.logger.error(f"ASN lookup error for {ip}: {e}")
        return None
    
    def _extract_asn_number(self, as_string):
        """Extract AS number from string like 'AS15169 Google LLC'"""
        if not as_string:
            return None
        import re
        match = re.search(r'AS(\d+)', as_string)
        return match.group(1) if match else None
    
    def _infer_cidr(self, ip, as_string):
        """
        Infer CIDR from AS number if not provided by API.
        This is a fallback - actual CIDR requires proper BGP data.
        """
        # For now, return /24 as a reasonable default for correlation
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.version == 4:
                return f"{ip}/24"
            else:
                return f"{ip}/64"
        except:
            return None
    
    def _generate_related_ips(self, cidr, limit=10):
        """
        Generate related IPs in the same CIDR block.
        Returns a list of IP addresses (excluding the query IP).
        """
        if not cidr:
            return []
        
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            hosts = list(network.hosts())
            
            # Limit results and exclude first/last few for safety
            if len(hosts) > limit + 5:
                hosts = hosts[2:limit+2]
            elif len(hosts) > limit:
                hosts = hosts[:limit]
            
            return [str(host) for host in hosts]
        except Exception as e:
            self.logger.error(f"Error generating related IPs for {cidr}: {e}")
            return []
    
    def execute(self):
        args = self.target or []
        
        if not args:
            return self.error("Usage: asn <ip_address>")
        
        ip = args[0].strip()
        
        # Basic IP validation
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return self.error(f"Invalid IP address: {ip}", target=ip)
        
        # Perform ASN lookup
        asn_data = self._lookup_asn_ipapi(ip)
        
        if not asn_data:
            return self.error(f"ASN lookup failed for {ip}", target=ip)
        
        # Generate related IPs
        cidr = asn_data.get("cidr")
        related_ips = self._generate_related_ips(cidr, limit=10)
        asn_data["related_ips"] = related_ips
        asn_data["related_count"] = len(related_ips)
        
        # Build result data
        result_data = {
            "ip": ip,
            "asn": asn_data.get("asn"),
            "as_number": asn_data.get("as_number"),
            "organization": asn_data.get("org"),
            "isp": asn_data.get("isp"),
            "country": asn_data.get("country"),
            "country_code": asn_data.get("country_code"),
            "cidr": cidr,
            "related_ips": related_ips,
            "related_count": len(related_ips),
            "timezone": asn_data.get("timezone"),
            "source": asn_data.get("source")
        }
        
        # Notes
        self.add_note(
            f"ASN Intelligence for {ip}: {asn_data.get('asn')} ({asn_data.get('org')}) - CIDR: {cidr}",
            severity="info"
        )
        
        if asn_data.get("country"):
            self.add_note(
                f"Geographic ASN data: {ip} is in {asn_data.get('country')} ({asn_data.get('country_code')})",
                severity="info"
            )
        
        if related_ips:
            self.add_note(
                f"Found {len(related_ips)} related IPs in same CIDR block {cidr}",
                severity="info"
            )
        
        # Relations
        if asn_data.get("as_number"):
            self.add_relation(
                src_type="ip", src_value=ip,
                relation="belongs_to_asn",
                dst_type="asn", dst_value=asn_data.get("as_number"),
                evidence=f"ASN lookup: {asn_data.get('asn')}"
            )
        
        if asn_data.get("org"):
            self.add_relation(
                src_type="ip", src_value=ip,
                relation="owned_by",
                dst_type="organization", dst_value=asn_data.get("org"),
                evidence=f"ASN organization: {asn_data.get('org')}"
            )
        
        if cidr:
            self.add_relation(
                src_type="ip", src_value=ip,
                relation="in_cidr",
                dst_type="network", dst_value=cidr,
                evidence=f"Network block: {cidr}"
            )
        
        # Save to context
        if self.context:
            self.context.add_asn_intel(ip, result_data)
        
        return self.success(target=ip, data=result_data)
