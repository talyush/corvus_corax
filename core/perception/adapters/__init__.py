"""Corvus Perception — Builtin adaptörler.

Mevcut modülleri (modules/*.py) Perception pipeline'a bağlayan wrapper'lar.
Her adaptör, kaynak kodunu değiştirmeden modülü sarar.
"""

from core.perception.adapters.whois import WhoisAdapter
from core.perception.adapters.social import SocialAdapter
from core.perception.adapters.dns import DnsAdapter
from core.perception.adapters.geoip import GeoipAdapter
from core.perception.adapters.asn import AsnAdapter
from core.perception.adapters.cert import CertAdapter
from core.perception.adapters.subdomain import SubdomainAdapter
from core.perception.adapters.tech import TechAdapter
from core.perception.adapters.metadata import MetadataAdapter
from core.perception.adapters.headers import HeadersAdapter

__all__ = [
    "WhoisAdapter",
    "SocialAdapter",
    "DnsAdapter",
    "GeoipAdapter",
    "AsnAdapter",
    "CertAdapter",
    "SubdomainAdapter",
    "TechAdapter",
    "MetadataAdapter",
    "HeadersAdapter",
]