"""Verification script for Corvus Corax v1.1.1 Cognitive Interface Deep Reasoning."""
import sys
import os

# Set root
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.cognitive.dialogue import CognitiveDialogueEngine
from core.cognitive.reasoning_engine import ConversationalReasoningEngine, RegisterClassifier, QuestionRegister
from core.context import ContextManager

def run_tests():
    print("=== Testing Corvus Corax Conversational Reasoning & Cognitive Engine ===")
    ctx = ContextManager()
    engine = CognitiveDialogueEngine(context_manager=ctx)

    test_queries = [
        ("hello corvus", ["Hello, friend", "sistemler", "dinliyorum", "active", "objective"]),
        ("cevapların statik mi dinamik mi", ["statik", "dinamik", "bağlam", "fark"]),
        ("ben kimim", ["kim olduğunu", "araştırmacı", "iz", "soru", "profil"]),
        ("yardım menüsünü aç", ["Yapabileceglerim", "Arastirma", "Cikarim", "komut", "whois", "nexus"]),
        ("anlam nedir", ["Anlam", "ilişki", "bağlantı", "nokta"]),
        ("Alexander Vance kimdir araştır", ["Alexander Vance", "keşif", "protokol"]),
    ]

    passed = 0
    for query, expected_keywords in test_queries:
        print(f"\n[QUERY]: {query}")
        result = engine.chat(query)
        response = result.get("response", "")
        print(f"[RESPONSE]:\n{response}")

        matches = [kw.lower() in response.lower() for kw in expected_keywords]
        if any(matches):
            print(f"-> PASS (Matched keywords: {[kw for kw, m in zip(expected_keywords, matches) if m]})")
            passed += 1
        else:
            print(f"-> FAIL (Expected at least one of: {expected_keywords})")

    print(f"\nSummary: {passed}/{len(test_queries)} tests passed.")
    if passed == len(test_queries):
        print("ALL TESTS PASSED SUCCESSFULLY!")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(run_tests())
