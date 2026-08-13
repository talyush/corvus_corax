from core.module_base import BaseModule
from core.confidence import aggregate_entity_confidence, find_identity_clusters, combine_confidences


class ResolveModule(BaseModule):
    """
    v0.9/Faz 5.5 — Entity Resolution (Identity Clustering).

    Aynı kişiye ait olabilecek farklı varlıkları birleştirir:
    - person:ahmet, email:ahmet@example.com, social_profile:github/ahmet...
    - Kural bazlı tanıma + Confidence aggregation
    """
    name = "resolve"

    def _find_same_identity(self, target):
        """
        Hedef varlığa bağlı candidate/possible ilişkileri bulur ve
        identity cluster oluşturur.
        """
        relations = self.context.data.get("relations", [])
        derived = self.context.data.get("derived_relations", [])

        # Hedef değerine bağlanan tüm ilişkiler
        related = []
        for rel in relations + derived:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            relation = rel.get("relation", "")
            confidence = rel.get("confidence", 1.0)

            # Hedef src veya dst'de mi?
            target_match = target in (src.get("value"), dst.get("value"))
            if not target_match:
                continue

            # Candidate/possible/associated ilişkileri topla
            if not any(k in relation for k in ("candidate", "possible", "associated", "correlation")):
                continue

            other = dst if src.get("value") == target else src
            related.append({
                "type": other.get("type"),
                "value": other.get("value"),
                "relation": relation,
                "confidence": float(confidence),
                "evidence": rel.get("evidence", ""),
            })

        return related

    def _build_identity_key(self, value):
        """Varlık değerinden kimlik anahtarı üretir (normalizasyon)."""
        value = str(value).lower().strip()
        # email ise @ öncesi
        if "@" in value:
            value = value.split("@")[0]
        # github/username formatı
        if "/" in value:
            value = value.split("/")[-1]
        # nokta/alt çizgi/tire aynı kişi olabilir
        value = value.replace(".", "").replace("_", "").replace("-", "")
        return value

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: resolve <name_or_entity>")

        target = args[0]

        self.begin_investigation(
            goal=f"Entity Resolution — {target}",
            phases=[
                (1, "RELATIONSHIP DISCOVERY"),
                (2, "IDENTITY CLUSTERING"),
                (3, "CONFIDENCE AGGREGATION"),
            ],
        )

        # 1. Hedefe bağlı tüm candidate ilişkileri bul
        self.status_step(f"Discovering candidate relationships for '{target}'")
        related = self._find_same_identity(target)

        # 2. Kimlik anahtarını normalize et (aynı kişiye ait olabilecekleri bul)
        self.status_step("Normalizing identity keys")
        target_key = self._build_identity_key(target)

        # Context'teki tüm varlıkları tara — aynı normalizasyona sahip olanları bul
        same_key_entities = []
        entities = self.context.data.get("entities", {})
        for key, ent in entities.items():
            ent_val = ent.get("value")
            if not ent_val:
                continue
            if self._build_identity_key(ent_val) == target_key and ent_val != target:
                same_key_entities.append({
                    "type": ent.get("type"),
                    "value": ent_val,
                })

        # 3. Confidence aggregation
        self.status_step("Aggregating combined confidence")
        agg = aggregate_entity_confidence(self.context, target)

        # 4. Identity cluster ilişkisi kur
        identity_created = None
        all_related = list(related)
        for e in same_key_entities:
            all_related.append({
                "type": e["type"],
                "value": e["value"],
                "relation": "identity_match",
                "confidence": 0.8,
                "evidence": f"Normalized identity key matches: {target} == {e['value']}",
            })

        if agg["evidence_count"] >= 2 or len(same_key_entities) >= 1:
            # Birleşik güven skorunu hesapla
            confidences = [r["confidence"] for r in all_related]
            combined = combine_confidences(confidences)

            # Identity cluster varlığı oluştur
            self.add_entity("identity", target, {
                "combined_confidence": combined,
                "entity_count": len(all_related),
            })

            # Tüm ilgili varlıkları identity cluster'a bağla
            for r in all_related:
                if r.get("value") == target:
                    continue
                self.add_relation(
                    "identity", target, "resolves_to", r["type"], r["value"],
                    evidence=f"Identity resolution: {target} resolves to {r['type']}:{r['value']} "
                             f"(combined conf: {combined:.2f})",
                    confidence=combined,
                )

            identity_created = {
                "identity": target,
                "combined_confidence": combined,
                "entity_count": len(all_related),
            }

        self.add_note(
            f"Entity resolution for {target}: {len(all_related)} related entities, "
            f"combined confidence: {agg['combined_confidence']:.2f}",
            severity="info",
        )

        data = {
            "target": target,
            "target_key": target_key,
            "related": related,
            "same_key_entities": same_key_entities,
            "aggregated_confidence": agg,
            "identity_cluster": identity_created,
            "entity_count": len(all_related),
        }
        return self.success(target=target, data=data)