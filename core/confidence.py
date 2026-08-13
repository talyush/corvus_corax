"""Corvus Corax v0.9 — Confidence Aggregation Motoru.

Aynı hedef varlığa giden birden çok candidate/possible ilişkinin birleşik
güven skorunu hesaplar. Bireysel zayıf kanıtlar birleşince güçlü kanıt olur.

Formül: combined = 1 - (1-c1)*(1-c2)*(1-c3)*...
Bu, "bağımsız kanıtların birleşik olasılığı" prensibine dayanır.
"""
import math
from collections import defaultdict


def combine_confidences(confidences):
    """
    Birden çok bağımsız güven skorunu birleştirir.
    Args:
        confidences: list of float (0-1)
    Returns:
        float (0-1) — birleşik güven
    """
    if not confidences:
        return 0.0
    # 1 - (1-c1)*(1-c2)*...
    product = 1.0
    for c in confidences:
        c = max(0.0, min(1.0, float(c)))
        product *= (1.0 - c)
    return round(1.0 - product, 4)


def aggregate_entity_confidence(context_manager, target_entity, relation_types=None):
    """
    Bir hedef varlığa giden tüm candidate/possible ilişkileri toplar ve
    birleşik güven skoru hesaplar.

    Args:
        context_manager: ContextManager instance
        target_entity: Hedef varlık değeri (örn. "ahmet")
        relation_types: Filtrelemek için ilişki türleri listesi (None = tümü)

    Returns:
        dict with combined_confidence, evidence_count, evidence_list
    """
    relations = context_manager.data.get("relations", [])
    derived = context_manager.data.get("derived_relations", [])

    evidence = []
    for rel in relations + derived:
        src = rel.get("src", {})
        dst = rel.get("dst", {})
        relation = rel.get("relation", "")
        confidence = rel.get("confidence", 1.0)

        # Hedef varlık src veya dst'de mi?
        target_match = (src.get("value") == target_entity or dst.get("value") == target_entity)
        if not target_match:
            continue

        # İlişki türü filtresi
        if relation_types and relation not in relation_types:
            continue

        # Sadece candidate/possible/conflict ilişkileri birleştir
        if not any(k in relation for k in ("candidate", "possible", "associated", "correlation", "conflict")):
            continue

        evidence.append({
            "relation": relation,
            "src": f"{src.get('type')}:{src.get('value')}",
            "dst": f"{dst.get('type')}:{dst.get('value')}",
            "confidence": float(confidence),
            "evidence": rel.get("evidence", ""),
        })

    if not evidence:
        return {
            "target": target_entity,
            "combined_confidence": 0.0,
            "evidence_count": 0,
            "evidence_list": [],
        }

    confidences = [e["confidence"] for e in evidence]
    combined = combine_confidences(confidences)

    return {
        "target": target_entity,
        "combined_confidence": combined,
        "evidence_count": len(evidence),
        "evidence_list": evidence,
    }


def find_identity_clusters(context_manager, threshold=0.7):
    """
    Context'teki tüm varlıkları tarar ve aynı kişiye ait olabilecek
    identity cluster'ları bulur.

    Kural: Aynı değere bağlanan birden çok varlık varsa ve birleşik güven
    threshold'u aşıyorsa identity cluster oluştur.

    Returns:
        list of dict: {identity, entities: [...], combined_confidence}
    """
    # Tüm varlıkları topla
    entities = context_manager.data.get("entities", {})
    relations = context_manager.data.get("relations", [])

    # Her varlık değeri için gelen ilişkileri grupla
    value_relations = defaultdict(list)
    for rel in relations:
        src = rel.get("src", {})
        dst = rel.get("dst", {})
        relation = rel.get("relation", "")
        confidence = rel.get("confidence", 1.0)

        # Candidate/possible ilişkileri topla
        if not any(k in relation for k in ("candidate", "possible", "associated", "correlation")):
            continue

        # src tarafı
        if src.get("value"):
            value_relations[src.get("value")].append({
                "relation": relation,
                "other": f"{dst.get('type')}:{dst.get('value')}",
                "confidence": float(confidence),
            })
        # dst tarafı
        if dst.get("value"):
            value_relations[dst.get("value")].append({
                "relation": relation,
                "other": f"{src.get('type')}:{src.get('value')}",
                "confidence": float(confidence),
            })

    clusters = []
    for value, rels in value_relations.items():
        if len(rels) < 2:
            continue
        confidences = [r["confidence"] for r in rels]
        combined = combine_confidences(confidences)
        if combined >= threshold:
            clusters.append({
                "identity": value,
                "entities": [r["other"] for r in rels],
                "combined_confidence": combined,
                "evidence_count": len(rels),
            })

    # Güven skoruna göre sırala
    clusters.sort(key=lambda x: x["combined_confidence"], reverse=True)
    return clusters