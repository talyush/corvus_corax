# Investigation State — core/investigation (v1.4)

Bir araştırmanın **canlı belgesı**. Corvus'un "gördüğü şeyler arasında kaybolmaması" sorusunun cevabı: her şeyin durumu tek, tutarlı, izlenebilir bir state'te.

> v1.4 prensibi: **Agent** tool'ları çalıştırır, **Investigation Engine** state'e sahiptir (hedef olgunlaştırma, boşluklar, hipotezler, next-step seçimi, durma koşulları). Bu doküman state'in şemasını tanımlar.

---

## 1. Amaç

- Araştırmanın şu anki durumunu (nereye geldik, ne biliyoruz, ne bilmiyoruz, sırada ne var) **tek kaynaktan** temsil et.
- Session boyunca kararların gerekçelerini (decision trace) tut — rapor/izlenebilirlik bunun üstüne biner.
- Investigation Engine'in "sıradaki adım ne" ve "durdur" kararları için gerekli tüm bilgiyi sağla.

## 2. Mevcut dayanaklar

| Bileşen | Dosya | Bugünkü rolü |
|---|---|---|
| `Hypothesis` (status: UNTESTED/CONFIRMED/REFUTED/EXHAUSTED) | `core/strategy.py` | Hipotez kümesi |
| `IntelligenceGaps` | `core/evidence/lineage.py` | "Corvus neyi bilmiyor" |
| `InvestigationGoal` + `_decompose_goals()` | `core/strategy.py` | Hedef ayrıştırma |
| `ContextManager` | `core/context.py` | Altta yatan global dünya modeli |
| `Agent.iterations` + `seen` set + budgets | `core/agent/agent.py` + `policy.py` | Mevcut döngü durumu (engine'e taşınacak) |
| `MuninnRecallEngine` | `core/muninn/recall.py` | Kalıcı geçmiş (aynı state'e bağlanır) |

## 3. Veri modeli

```python
@dataclass
class InvestigationState:
    request: InvestigationRequest
    status: str                    # CREATED|PLANNING|IN_PROGRESS|NEEDS_INPUT|AWAITING_EXTERNAL|FINALIZED|ARCHIVED
    resolution: TargetResolution
    hypotheses: List[Hypothesis]
    gaps: List[IntelligenceGap]
    steps: List[ExecutedStep]
    next_steps: List[PlanStep]
    stop_conditions: StopConditions
    decisions: List[DecisionTrace]
    started_at: str
    updated_at: str
    finalized_report: Optional[Dict] = None
```

### 3.1 Parçalar

**request** — kullanıcı emri (referans olabilir, hedef DEĞİL):
```python
{"intent": "investigate", "referent": "Ahmet Yılmaz", "constraints": {"max_steps": 8}}
```

**resolution (Target Resolution)** — v1.4'ün kritik yeni katmanı:
```python
{
  "candidates": [
    {"entity": "person:Ahmet Yılmaz",   "evidence_weight": 0.9, "ambiguity": "low"},
    {"entity": "person:Ahmet Y. Yılmaz", "evidence_weight": 0.4, "ambiguity": "medium"}
  ],
  "primary": "person:Ahmet Yılmaz",
  "status": "RESOLVED" | "AMBIGUOUS" | "UNRESOLVED"
}
```
> Kural: "Ahmet Yılmaz" doğrudan tek entity olarak kabul edilmez; kanıt zinciri candidate'ları ayrıştırır. **Similarity ≠ Identity** — `core/human/similarity.py` felsefesi.

**steps** — çalıştırılmış adımlar (ya yazma-ekleme, ya da istenmeyen durum yok):
```python
{"tool": "social", "target": "Ahmet Yılmaz", "decision_ref": "dec-001",
 "status": "success|error|denied|skipped", "observation_ref": "obs-002"}
```

**decisions** — döngünün gerekçe zinciri (rapor nasıl oluştu sorusunun cevabı):
```python
{"id":"dec-001", "next_step":"social(Ahmet Yılmaz)",
 "why":"Planner prefs: person->social", "time": "..."}
```

**stop_conditions** — Investigation Engine'in durum kontrolü:
```python
{"max_steps": 8, "confidence_threshold": 0.85,
 "coverage_required": ["identity", "digital_footprint"], "max_network_calls": 6}
```

## 4. Durum makinesi

```
CREATED → PLANNING → IN_PROGRESS ⇄ (NEEDS_INPUT | AWAITING_EXTERNAL) → IN_PROGRESS
                          │
                          ▼
                       FINALIZED → ARCHIVED
```

- **NEEDS_INPUT**: hedef belirsiz (UNRESOLVED), kullanıcıdan netleştirme istenir.
- **AWAITING_EXTERNAL**: onay/API yanıtı bekleniyor.
- **FINALIZED**: `finalized_report` üretildi; evidence ve kararlar rapora gömüldü.
- **ARCHIVED**: state, kalıcı belleğin bir parçası haline gelir (Muninn).

## 5. İnvaryantlar

1. State, döngünün **tek yazarı**dır; Agent durumu değiştiremez, yalnızca engine'in kararını uygulayıp sonucu state'e geri verir.
2. Her `step` ya `success` (evidence üretti) ya da `error/denied/skipped` (gerekçeli) olur — ortada kalan adım yasak.
3. `FINALIZED` olmadan rapor üretilemez; `finalized_report.evidence_refs` boşsa rapor "kanıtsız" damgası taşır.
4. `resolution.status == AMBIGUOUS` iken `investigate` sonuçlandırılamaz (önce kullanıcıya sorulur).
5. Stop koşullarına ulaşılmadan sessizce sonlanılamaz; her sonlanış `stop_conditions`'a göre gerekçelendirilir.

## 6. Agent / Engine ayrımı (v1.4'ün kalbi)

| Katman | Sorumluluğu | YASAK |
|---|---|---|
| **Investigation Engine** | State sahibi, target resolution, gap analizi, hipotez güncelleme, next-step seçimi, stop kararı, rapor finalize | Araç çalıştırmak (kendisi tool'u çağırmaz) |
| **Agent** | Engine'in karar verdiği adımı SafetyPolicy onayıyla icra etmek | Kendi başına "ne yapacağım" kararı vermek |
| **Perception** | Dış dünyadan veri topla + normalize + provenance | State'i değiştirmek |

Akış:
```
UserRequest -> Engine.resolve_target(referent)  # candidates + ambiguity
   → Engine.plan_hypotheses() → Engine.select_next_step()
   → Agent.execute(step) → Engine.record_observation(result)
   → Engine.update_hypotheses() → Engine.check_stop()
   → Engine.finalize() → rapor
```

## 7. Kalıcılık / yaşam döngüsü

- `FINALIZED` → rapor kalıcı (exporter/json).
- `ARCHIVED` → InvestigationState'i `MuninnStore` snapshot'ına bağla (gelecekte drift takibi için).
- Konuşma: `ConversationMemory` (RAM) ve `MindMemory` (kalıcı) ayrı kalır — Investigation State bunlardan bağımsızdır, yalnızca rapor aracılığıyla arşivlenir.

## 8. Açık sorular

- [ ] `Resolution` mantığı ilk fazda kural tabanlı mı (identity_capability + planner.classify üstü) yoksa ML/embedding gerektirir mi? (Öneri: kural tabanlı başla.)
- [ ] Çoklu hedef / çoklu iş emri: bir `InvestigationState` birden çok `InvestigationGoal` taşıyabilir mi, tek hedef mi? (v1.4 başlangıcı: tek hedef, çok hypothesis.)
- [ ] `AWAITING_EXTERNAL` durumu için async olgunluk gerekli mi, yoksa senkron bekleme yeterli mi?