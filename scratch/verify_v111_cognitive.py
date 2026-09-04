"""Corvus Corax v1.1.1 - Cognitive Interface & Machine Persona Verification Suite.
"""
from main import run_module, print_output, context
from core.cognitive.dialogue import CognitiveDialogueEngine
from core.cognitive.memory import ConversationMemory
from core.cognitive.intent import IntentExtractor

print("============================================================")
print("  TEST 1: 'HELLO, FRIEND' & MACHINE PERSONA GREETING TEST")
print("============================================================")
dialogue = CognitiveDialogueEngine(context_manager=context)

# 1. English greeting
res_en = dialogue.chat("hello corvus")
print(f" [+] User query : 'hello corvus'")
print(f" [+] Provider   : {res_en['provider']}")
print(f" [+] Response   :\n     {res_en['response']}")
assert "Hello, friend" in res_en["response"], "Response must include canonical 'Hello, friend.' greeting"
print(" [+] English Persona Greeting: PASSED\n")

# 2. Turkish greeting
res_tr = dialogue.chat("merhaba corvus")
print(f" [+] User query : 'merhaba corvus'")
print(f" [+] Response   :\n     {res_tr['response']}")
assert "Hello, friend" in res_tr["response"], "Turkish response must include canonical 'Hello, friend.' greeting"
print(" [+] Turkish Persona Greeting: PASSED\n")

print("============================================================")
print("  TEST 2: MULTI-TURN CONVERSATION MEMORY & PRONOUN RESOLUTION")
print("============================================================")
memory = ConversationMemory()
extractor = IntentExtractor()

# Turn 1: Introduce entity
t1_text = "Alexander Vance adında bir hedef tespit ettik."
intent1 = extractor.extract(t1_text)
memory.add_user_message(t1_text, intent=intent1.intent_type, entities=intent1.entities)
if intent1.entities:
    memory.update_focal_target(intent1.entities[0])
print(f" [Turn 1] User: '{t1_text}' -> Active Target: '{memory.active_target}'")
assert memory.active_target == "Alexander Vance", "Turn 1 must capture 'Alexander Vance'"

# Turn 2: Refer to entity using pronoun ("bu kişinin")
t2_text = "bu kişinin altyapısını ve domainlerini incele"
resolved_ref = memory.resolve_reference(t2_text)
intent2 = extractor.extract(t2_text, fallback_target=resolved_ref)
print(f" [Turn 2] User: '{t2_text}' -> Resolved Target: '{intent2.entities[0]}' | Intent: '{intent2.intent_type}'")
assert intent2.entities[0] == "Alexander Vance", "Turn 2 must resolve pronoun to 'Alexander Vance'"
assert intent2.intent_type == "INVESTIGATE", "Turn 2 intent must be INVESTIGATE"
print(" [+] Multi-Turn Context & Reference Resolution: PASSED\n")

print("============================================================")
print("  TEST 3: NOISY / COMPLEX / SLANG NATURAL LANGUAGE PARSING")
print("============================================================")
noisy_queries = [
    ("ya su vance-corp.com u bi arastirsana ne var ne yok cikar", "vance-corp.com", "INVESTIGATE"),
    ("198.51.100.42 ile vance-corp.com arasinda ne baglanti var", "198.51.100.42", "BRIDGE"),
    ("bu hedef hakkinda ne dusunuyorsun cikarim yap", None, "INFER"),
]

for query, expected_entity, expected_intent in noisy_queries:
    res = extractor.extract(query)
    print(f" [+] Query : '{query}'")
    print(f"     -> Intent: {res.intent_type} | Entities: {res.entities}")
    if expected_entity:
        assert expected_entity in res.entities, f"Expected entity '{expected_entity}' in {res.entities}"
    assert res.intent_type == expected_intent, f"Expected intent '{expected_intent}' but got '{res.intent_type}'"

print(" [+] Noisy Natural Language Parsing: PASSED\n")

print("============================================================")
print("  TEST 4: LIVE CLI CHAT MODULE EXECUTION")
print("============================================================")
res_chat_1 = run_module("chat", ["selam", "corvus"])
print_output(res_chat_1)

res_chat_2 = run_module("chat", ["vance-corp.com", "hakkında", "ne", "düşünüyorsun"])
print_output(res_chat_2)

print("=== ALL V1.1.1 COGNITIVE INTERFACE TESTS PASSED CLEANLY! ===")
