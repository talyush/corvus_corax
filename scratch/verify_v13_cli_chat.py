"""Verification test for Corvus Corax v1.3 CLI & Chat Natural Language integration."""
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from main import run_module, print_output, context


def test_cli_and_chat():
    print("=== TEST 5: Live CLI & Chat Human-Centered Intelligence Integration ===")

    # 1. CLI: `human profile alexander_vance`
    print("\n[+] Testing CLI: 'human profile alexander_vance'")
    res_prof = run_module("human", ["profile", "alexander_vance"])
    print_output(res_prof)
    assert res_prof["status"] == "success"

    # 2. CLI: `human stylometry "Bu sistem mimarisi çok katmanlı ve karmaşık bir yapıya sahiptir."`
    print("\n[+] Testing CLI: 'human stylometry ...'")
    res_sty = run_module("human", ["stylometry", "Bu", "sistem", "mimarisi", "çok", "katmanlı", "ve", "karmaşık."])
    print_output(res_sty)
    assert res_sty["status"] == "success"

    # 3. CLI: `human compare user1 user2`
    print("\n[+] Testing CLI: 'human compare user1 user2'")
    res_comp = run_module("human", ["compare", "user1", "user2"])
    print_output(res_comp)
    assert res_comp["status"] == "success"

    # 4. Chat Doğal Dil: "Alexander Vance için insan profili ve yazım stili analizi yap"
    print("\n[+] Testing Chat Natural Language: 'Alexander Vance için insan profili ve yazım stili'")
    res_chat = run_module("chat", ["Alexander", "Vance", "için", "insan", "profili", "ve", "yazım", "stili"])
    print_output(res_chat)
    assert res_chat["status"] == "success"
    assert "HUMAN INTELLIGENCE" in res_chat["data"]["response"] or "Alexander" in res_chat["data"]["response"]

    print("\n=== ALL V1.3 HUMAN INTELLIGENCE TESTS PASSED CLEANLY! ===")
    return 0


if __name__ == "__main__":
    sys.exit(test_cli_and_chat())
