"""Verification test for Corvus Corax v1.2 CLI modules and Chat Natural Language integration."""
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from main import run_module, print_output, context
from core.muninn.store import MuninnStore

def test_cli_and_chat():
    print("=== TEST 4: Live CLI & Chat Dual-Raven Integration ===")
    
    # 1. Muninn'e bir veri ekleyelim
    store = MuninnStore()
    store.record_snapshot("test-corp.com", "domain", {"ip": "1.2.3.4", "registrar": "Namecheap"}, source_module="dns")
    store.record_snapshot("test-corp.com", "domain", {"ip": "5.6.7.8", "registrar": "Cloudflare"}, source_module="whois")

    # 2. CLI `muninn history test-corp.com`
    print("\n[+] Testing CLI: 'muninn history test-corp.com'")
    res_muninn = run_module("muninn", ["history", "test-corp.com"])
    print_output(res_muninn)
    assert res_muninn["status"] == "success"

    # 3. CLI `huginn explain test-corp.com`
    print("\n[+] Testing CLI: 'huginn explain test-corp.com'")
    res_huginn = run_module("huginn", ["explain", "test-corp.com"])
    print_output(res_huginn)
    assert res_huginn["status"] == "success"

    # 4. CLI `huginn synergy test-corp.com`
    print("\n[+] Testing CLI: 'huginn synergy test-corp.com'")
    res_synergy = run_module("huginn", ["synergy", "test-corp.com"])
    print_output(res_synergy)
    assert res_synergy["status"] == "success"

    # 5. Chat Doğal Dil: "test-corp.com hakkında geçmişte ne hatırlıyorsun"
    print("\n[+] Testing Chat Natural Language: 'test-corp.com hakkında geçmişte ne hatırlıyorsun'")
    res_chat_muninn = run_module("chat", ["test-corp.com", "hakkında", "geçmişte", "ne", "hatırlıyorsun"])
    print_output(res_chat_muninn)
    assert res_chat_muninn["status"] == "success"
    assert "MUNINN" in res_chat_muninn["data"]["response"] or "test-corp.com" in res_chat_muninn["data"]["response"]

    # 6. Chat Doğal Dil: "test-corp.com hakkında neden böyle düşündün akıl yürütme açıkla"
    print("\n[+] Testing Chat Natural Language: 'test-corp.com hakkında neden böyle düşündün akıl yürütme'")
    res_chat_huginn = run_module("chat", ["test-corp.com", "hakkında", "neden", "böyle", "düşündün", "akıl", "yürütme"])
    print_output(res_chat_huginn)
    assert res_chat_huginn["status"] == "success"

    print("\n=== ALL V1.2 HUGINN & MUNINN INTEGRATION TESTS PASSED CLEANLY! ===")
    return 0

if __name__ == "__main__":
    sys.exit(test_cli_and_chat())
