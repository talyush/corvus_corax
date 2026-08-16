"""Corvus Corax v0.9/Faz 6 — Discovery Engine.

Kullanıcı tarafından verilen seed'i başlangıç noktası olarak kabul eder,
otomatik keşif zinciri başlatır ve KULLANICININ BİLMEDİĞİ yeni entity'ler,
evidence'ler ve bağlantılar üretir.

Akış:
  user -> seed -> investigation -> new evidence -> new entities -> pivots -> unexpected relationships

Seed ≠ Evidence:
  - source=user_input olan veri seed'dir, ASLA evidence değildir.
  - source=corvus (modül) tarafından bulunan veri evidence'dır.
"""
from datetime import datetime, timezone


class DiscoveryEngine:
    """Otomatik keşif motoru — seed'den başlayarak yeni istihbarat bulur."""

    # Modül zinciri: her varlık tipi için hangi modül çalıştırılmalı
    MODULE_CHAIN = {
        "person": ["social", "github", "academic"],
        "organization": ["org", "crawl", "dns", "metadata"],
        "domain": ["dns", "cert", "tech", "metadata", "footprint", "whois", "subdomain"],
        "ip": ["geoip", "asn", "scan"],
        "email": ["breach"],
        "phone": ["phone"],
        "wallet": ["wallet"],
    }

    # Keşifhedefi olarak derinleştirilebilecek türler (sosyal/username aracı değil)
    EXPLORABLE_TYPES = {"person", "organization", "domain", "ip", "email", "phone", "wallet"}

    def __init__(self, context_manager, config=None, logger=None, module_registry=None):
        self.context = context_manager
        self.config = config or {}
        self.logger = logger
        self.modules = module_registry or {}

    def _resolve_entity_type(self, value):
        """Context'te 'value' hangi entity tipine ait, bulur."""
        entities = self.context.data.get("entities", {})
        # value tam olarak bir key ise (örn. 'person:ahmet')
        if f"{value}:whatever" in entities:
            pass
        for key, ent in entities.items():
            if ent.get("value") == value:
                return ent.get("type"), key
        # value zaten 'type:value' formatında mı?
        if ":" in value:
            for key, ent in entities.items():
                if key == value:
                    return ent.get("type"), key
        return None, None

    def _run_module(self, module_name, target_value):
        """Belirtilen modülü target_value ile çalıştırır, sonucu context'e işler."""
        if module_name not in self.modules:
            return None
        try:
            module_cls = self.modules[module_name]
            module = module_cls(target=[target_value], config=self.config, logger=self.logger, context=self.context)
            result = module.execute()
            return result
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Discovery: module {module_name} failed: {e}")
            return None

    def investigate(self, seed_value, max_depth=3, max_entities=25):
        """
        Seed değerinden başlayarak otomatik keşif zinciri başlatır.

        Args:
            seed_value: Kullanıcının verdiği başlangıç değeri (örn. 'ahmet', '8.8.8.8', 'example.com')
            max_depth: Maksimum zincir derinliği
            max_entities: Maksimum keşfedilecek entity sayısı

        Returns:
            discovery report dengan seed, discovered entities, novelty score, path
        """
        seed_entities = []
        discovered_path = []      # (depth, entity_type, entity_value, discovered_by, evidence)
        discovered_entities = {} # entity_key -> {type, value, provenance}

        # 1. Seed'i ekle
        seed_entity_key = self.context.add_entity(
            "person", seed_value if ":" not in seed_value else seed_value,
            provenance={"source": "user_input", "status": "seed"}
        )
        seed_entities.append(seed_entity_key)
        discovered_entities[seed_entity_key] = {"type": "person" if ":" not in seed_value else seed_value.split(":")[0], "value": seed_value, "status": "seed"}

        # 2. Seed'in context'te mevcut bilinen ilişkilerini bulsun
        known_relations = self.context.data.get("relations", []) + self.context.data.get("derived_relations", [])

        # BFS keşif
        queue = [(seed_value, 0)]  # (entity_value, depth)
        visited = {seed_value}

        while queue:
            current_value, depth = queue.pop(0)
            if depth >= max_depth or len(discovered_entities) >= max_entities:
                break

            # Mevcut entity tipini bul
            ent_type, ent_key = self._resolve_entity_type(current_value)
            if not ent_type:
                ent_type = "person"  # varsayılan
            if not ent_key:
                ent_key = self.context.add_entity(ent_type, current_value, status="seed")
                discovered_entities[ent_key] = {"type": ent_type, "value": current_value, "status": "seed"}

            # Bu entity tipi için modül zincirini çalıştır
            chain = self.MODULE_CHAIN.get(ent_type, [])
            for module_name in chain:
                result = self._run_module(module_name, current_value)
                if not result or result.get("status") != "success":
                    continue

                # Result'ten YENİ varlıklar bulunup keşif listesine eklenir
                for rel in result.get("relationships", []):
                    src = rel.get("src", {})
                    dst = rel.get("dst", {})
                    # src -> dm7 ilişkiler
                    for side in (("src", src), ("dst", dst)):
                        side_type, side_side_value = side[1].get("type"), side[1].get("value")
                        if not side_type or not side_side_value:
                            continue
                        entity_key = f"{side_type}:{side_side_value}"
                        if entity_key not in discovered_entities:
                            discovered_entities[entity_key] = {
                                "type": side_type,
                                "value": side_side_value,
                                "status": "discovered",
                                "discovered_by": module_name,
                                "confidence": rel.get("confidence", 0.5),
                            }
                            discovered_path.append({
                                "depth": depth + 1,
                                "entity_type": side_type,
                                "entity_value": side_side_value,
                                "discovered_by": module_name,
                                "via": rel.get("relation", ""),
                                "evidence": rel.get("evidence", ""),
                                "from": current_value,
                            })
                            # Queue'ya ekleme — SADECE keşifhedefi türler derinleşir,
                            # social_profile/username gibi aracılar derinleştirilmez (sonsuz döngüyü önler)
                            if (
                                side_type in self.EXPLORABLE_TYPES
                                and side_side_value not in visited
                                and len(discovered_entities) < max_entities
                            ):
                                visited.add(side_side_value)
                                queue.append((side_side_value, depth + 1))

        # 3. Novelty Score hesapla
        total_entities = len(discovered_entities)
        seed_count = 1  # sadece ilk seed
        discovered_count = total_entities - seed_count
        novelty_score = discovered_count / max(total_entities, 1)

        # 4. Beklenmedik ilişkiler (unexpected connections)
        unexpected = [
            p for p in discovered_path
            if any(k in p.get("via", "").lower() for k in ("share", "same", "correlation", "certificate", "asn"))
        ]

        report = {
            "seed": seed_value,
            "seed_count": seed_count,
            "total_entities": total_entities,
            "discovered_count": discovered_count,
            "novelty_score": round(novelty_score, 3),
            "max_depth": max_depth,
            "discovered_path": discovered_path,
            "unexpected_connections": unexpected,
            "entities": list(discovered_entities.values()),
            "no_new_findings": discovered_count == 0,
        }
        return report

    def print_report(self, report):
        """İnsanokuyanablir keşif raporu üretir."""
        lines = []
        lines.append("=" * 70)
        lines.append(f"INVESTIGATION REPORT — Seed: {report['seed']}")
        lines.append("=" * 70)

        if report.get("no_new_findings"):
            lines.append("\n  No new entities discovered beyond seed.")
            return "\n".join(lines)

        lines.append(f"\n  Seed: {report['seed']} [source=user_input, status=seed]")
        for p in report.get("discovered_path", []):
            prefix = "  ├─" if p["depth"] == 1 else f"  │ {' ' * (p['depth']*2)}└─"
            line = f"{prefix} [DISCOVERED] {p['entity_type']}:{p['entity_value']}"
            line += f" (discovered_by={p['discovered_by']})"
            if p.get("via"):
                line += f" via {p['via']}"
            lines.append(line)
            if p.get("evidence"):
                lines.append(f"  │ {' ' * (p['depth']*2)}   evidence: {p['evidence']}")

        lines.append("\n" + "-" * 70)
        lines.append(f"  Novelty Score: {report['novelty_score']:.2f} ({report['discovered_count']} new entities / {report['total_entities']} total)")
        lines.append(f"  Discovery Depth: {report['max_depth']}")
        lines.append(f"  Unexpected Connections: {len(report['unexpected_connections'])}")
        lines.append("=" * 70)
        lines.append("  [NOTE] Seed is user-provided; all discovered entities are Corvus evidence.")
        lines.append("  [NOTE] Found ≠ Verified. Confidence reflects discovery method.")
        return "\n".join(lines)