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

> **v1.4 kararları:** (1) İlk faz **rule-based** — embedding/ML/LLM tabanlı identity resolution v1.4 başlangıcına girmez. (2) `support_score` bir kimlik olasılığı DEĞİLDİR; candidate'ların kanıt tabanlı **destek/rank puanıdır**. (3) `AMBIGUOUS` veya `UNRESOLVED` durumunda `primary` **null/None** olur.

```python
{
  "candidates": [
    {"entity": "person:Ahmet Yılmaz",    "support_score": 0.9, "ambiguity": "low"},
    {"entity": "person:Ahmet Y. Yılmaz",  "support_score": 0.4, "ambiguity": "medium"}
  ],
  "primary": "person:Ahmet Yılmaz" | None,   # AMBIGUOUS/UNRESOLVED ise None
  "status": "RESOLVED" | "AMBIGUOUS" | "UNRESOLVED"
}
```
> Kural: "Ahmet Yılmaz" doğrudan tek entity olarak kabul edilmez; kanıt zinciri candidate'ları ayrıştırır. **Similarity ≠ Identity** — `core/human/similarity.py` felsefesi. `support_score` kimlik iddiası değil, "bu candidate hangi kanıtlarla destekleniyor" skoru.

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
                       FINALIZED  →  ARCHIVED (ayrı lifecycle action)
```

- **NEEDS_INPUT**: hedef belirsiz (UNRESOLVED), kullanıcıdan netleştirme istenir.
- **AWAITING_EXTERNAL**: onay/API yanıtı bekleniyor — **v1.4 kararı: senkron bekleme/onay** ile; gerçek async altyapı şimdilik kurulmaz.
- **FINALIZED**: `finalized_report` üretildi; evidence ve kararlar rapora gömüldü.

**FINALIZED ≠ ARCHIVED (v1.4 kararı):**
- `FINALIZED`: araştırma bitti, rapor sealed/finalized.
- `ARCHIVED`: state'in kalıcı geçmişe (Muninn) aktarılmasıdır — FINALIZED sonrası **ayrı lifecycle action** olarak kalır.
- Arşivleme şimdilik **otomatikleştirilmez**; ayrı bir tetik (kullanıcı komutu / operator kararı) gerektirir.

## 5. İnvaryantlar

1. State'in **tek yazarı Investigation Engine'dir**; Agent durumu değiştiremez.
2. Her `step` ya `success` (evidence üretti) ya da `error/denied/skipped` (gerekçeli) olur — ortada kalan adım yasak.
3. `FINALIZED` olmadan rapor üretilemez; `finalized_report.evidence_refs` boşsa rapor "kanıtsız" damgası taşır.
4. `resolution.status == AMBIGUOUS` veya `UNRESOLVED` olduğunda `primary` **None** olmalıdır; `investigate` bu durumdayken sonuçlandırılamaz (önce kullanıcıya sorulur / resolution tamamlanır).
5. Stop koşullarına ulaşılmadan sessizce sonlanılamaz; her sonlanış `stop_conditions`'a göre gerekçelendirilir.

## 6. Agent / Engine ayrımı (v1.4'ün kalbi)

### 6.1 State ownership — kesin ayrım

**Investigation State'ın tek yazarı Investigation Engine'dir.**

| Katman | Ne YAPAR | Doğrudan NE YAPAMAZ |
|---|---|---|
| **Investigation Engine** | State sahibi: target resolution, gap analizi, hipotez güncelleme, next-step seçimi, stop kararı, rapor finalize | Araç çalıştırmak |
| **Agent** | Engine kararını alır → SafetyPolicy'den geçirir → tool'u çalıştırır → sonucu Engine'e geri verir | `InvestigationState` **herhangi bir mutation** yapmak; kendi başına "ne yapacağım" kararı vermek |
| **Perception** | Dış dünyadan veri topla + normalize + provenance | State'i değiştirmek |

### 6.2 Akış (kanonik veri yolu)

```
User
  → Investigation Engine      (karar/emir üretir)
  → Agent                     (Engine kararını alır, SafetyPolicy'den geçirir)
  → ActionGuard               (capability sınırı)
  → Tool                      (çalıştırır)
  → ToolResult                (canonical sonuç)
  → Investigation Engine      (state güncellemesini YALNIZCA engine yapar)
  → State update
```

```python
Engine.resolve_target(referent)      # candidates + ambiguity (rule-based)
   → Engine.plan_hypotheses()
   → Engine.select_next_step()       # ToolResult metadata'sına göre («output_kind»)
   → Agent.execute(decision)         # SafetyPolicy + ActionGuard
   → Agent döndür: ToolResult
   → Engine.record_tool_result(r)    # state yazımı — tek nokta
   → Engine.update_hypotheses()
   → Engine.check_stop()             # stop_conditions
   → Engine.finalize()               # rapor sealed
   → [ayrı aksiyon] Engine.archive() # ARCHIVED (otomatik değil)
```

## 7. Kalıcılık / yaşam döngüsü

- `FINALIZED` → rapor kalıcı (exporter/json); seals gerçekleşir.
- `ARCHIVED` → ayrı lifecycle action; `InvestigationState`'i `MuninnStore` snapshot'ına bağlar (gelecekte drift takibi için). **Otomatik değildir.**
- Konuşma: `ConversationMemory` (RAM) ve `MindMemory` (kalıcı) ayrı kalır — Investigation State bunlardan bağımsızdır, yalnızca rapor/arşiv aracılığıyla bağlanır.

## 8. Kararlar özeti (v1.4)

**Varsayılan kapsam — rule-based, tek hedef, senkron:**
- [x] Target Resolution ilk faz **rule-based** (identity_capability + planner.classify üstü) — embedding/ML/LLM tabanlı identity resolution v1.4 başlangıcına girmez.
- [x] **Tek target + çok hypothesis**; multi-target investigation sonraki kapsam.
- [x] `AWAITING_EXTERNAL` senkron approval/API wait ile başlar; gerçek async altyapı yapılmaz.

**Resolution şeması:**
- [x] `support_score` = candidate destek/ranking puanı (identity probability değil); `Similarity != Identity` korunur.
- [x] `status == AMBIGUOUS/UNRESOLVED` iken `primary = None`.

**Ownership:**
- [x] State'in tek yazarı Investigation Engine'dir; Agent state mutation yapamaz.
- [x] Akış: `Engine karar → Agent (SafetyPolicy+ActionGuard) → Tool → ToolResult → Engine → State update`.

**Lifecycle:**
- [x] `FINALIZED ≠ ARCHIVED`; arşivleme FINALIZED sonrası ayrı aksiyon, otomatik değil.

**Veri erişimi (ask/sql):**
- [x] SQLite veya yeni veritabanı kurulmaz; `ask(sql)` v1.4 dependency'si değildir.
- [x] İleride gerekirse Corvus-native bir Query API (ContextManager + Muninn + IntelligenceVault üzerinde abstraction) tasarlanır; storage implementation değiştirilebilir — ama önce abstraction ihtiyacı gerçek kullanım üzerinden doğrulanır.