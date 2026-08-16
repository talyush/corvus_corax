"""Corvus Corax v0.9.1-autonomous Verification Script.
"""
from main import run_module, print_output, context
from core.capabilities.identity_capability import IdentityCapability
from core.capabilities.search_capability import SearchCapability
from core.capabilities.enrichment_capability import EnrichmentCapability
from core.strategy import AutonomousStrategyEngine

print("=== 1. Identity Capability Test ===")
name = "Ahmet Bağcı"
norm = IdentityCapability.normalize_text(name)
handles = IdentityCapability.generate_username_permutations(name)
emails = IdentityCapability.generate_candidate_emails(name, domain="company.com")

print(f"Normalized Name : '{norm}'")
print(f"Top 5 Handles   : {handles[:5]}")
print(f"Top 5 Emails    : {emails[:5]}")
print()

print("=== 2. Search Capability Dork Generator Test ===")
dorks = SearchCapability.generate_osint_dorks(name, domain="company.com")
for idx, dork in enumerate(dorks, 1):
    print(f"  Dork {idx}: {dork}")
print()

print("=== 3. Enrichment Capability Gravatar Test ===")
grav = EnrichmentCapability.check_gravatar_profile("test@gmail.com")
print(f"Gravatar Status : {grav.get('status')}")
print(f"Gravatar Hash   : {grav.get('gravatar_hash')}")
print()

print("=== 4. Live Discover Command Test ===")
res = run_module("discover", ["Ahmet Bağcı"])
print_output(res)
print()
print("=== All v0.9.1-autonomous tests completed successfully! ===")
