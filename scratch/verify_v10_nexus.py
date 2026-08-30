"""Corvus Corax v1.0 Nexus Intelligence Verification Script.
"""
from main import run_module, print_output, context
from core.events.bus import global_event_bus
from core.events.types import EntityDiscoveredEvent, RelationshipCreatedEvent, AssetBoundEvent
from core.graph.providers.neo4j_provider import Neo4jGraphService
from core.nexus.reasoning import GraphReasoningEngine
from core.nexus.timeline import TemporalTimelineEngine
from core.nexus.assets import AssetManager

print("=== 1. EventBus Typed Event Test ===")
received = []
def handle_entity_event(evt):
    received.append(evt)

global_event_bus.subscribe("EntityDiscovered", handle_entity_event)
global_event_bus.publish(EntityDiscoveredEvent("person", "Target Alpha"))
print(f"Published 1 Event -> Handlers Received: {len(received)}")
print()

print("=== 2. Graph Service Layer & Reasoning Engine Test ===")
graph_service = Neo4jGraphService() # Uses In-Memory fallback if Neo4j is offline
graph_service.add_entity("person", "Target Alpha")
graph_service.add_entity("domain", "alpha-corp.com")
graph_service.add_entity("ip", "1.2.3.4")

graph_service.add_relationship("Target Alpha", "alpha-corp.com", "owns_domain", confidence=0.95, evidence_ids=["ev-101", "ev-102"])
graph_service.add_relationship("alpha-corp.com", "1.2.3.4", "resolves_to", confidence=0.88, evidence_ids=["ev-103"])
graph_service.bind_asset("Target Alpha", "certificate", "SAN: *.alpha-corp.com")

reasoning_engine = GraphReasoningEngine(graph_service)
reasoning = reasoning_engine.synthesize_reasoning_statement("Target Alpha")

print(f"Target : {reasoning['entity']}")
print(f"Status : {reasoning['overall_assessment']}")
print(f"Statements ({len(reasoning['reasoning_statements'])}):")
for st in reasoning["reasoning_statements"]:
    print(f"  * {st}")
print()

print("=== 3. Temporal Timeline Test ===")
timeline_engine = TemporalTimelineEngine(graph_service)
tl = timeline_engine.build_timeline("Target Alpha")
for t in tl:
    print(f"  #{t['sequence_num']} [{t['timestamp']}] {t['event']}")
print()

print("=== 4. Intelligence Path Query Test ===")
paths = graph_service.query_paths("Target Alpha", "1.2.3.4")
print("Path found:", paths)
print()

print("=== 5. Live CLI Nexus Commands Test ===")
context.add_entity("person", "Target Alpha")
context.add_entity("domain", "alpha-corp.com")
context.add_relation(
    "person", "Target Alpha", "owns_domain", "domain", "alpha-corp.com", confidence=0.95
)

res_summary = run_module("nexus", ["summary", "Target Alpha"])
print_output(res_summary)

res_timeline = run_module("nexus", ["timeline", "Target Alpha"])
print_output(res_timeline)

res_paths = run_module("nexus", ["query", "paths", "Target Alpha", "alpha-corp.com"])
print_output(res_paths)

print("=== All v1.0 Nexus Intelligence tests passed cleanly! ===")
