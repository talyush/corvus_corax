# Tool Contract — core/agent (v1.4)

Agent'ın "el"i ve "duyu"su. Araç (tool) = dış dünyaya veya yerel analize yapılan **tek, doğrulanabilir, geri çekilebilir** bir eylem.

> v1.4 ayrımı: **Agent** araçları çalıştırır, **Investigation Engine** hangi aracın neden, ne zaman çalışacağına karar verir. Bu kontrat yalnızca "araç nasıl çağrılır ve ne döner" sorusunu kesinleştirir.

---

## 1. Hedefler

- Araç envanteri (Registry) şeffaf ve ayrıştırılabilir olsun.
- Her aracın **input şeması** doğrulanabilsin (`input_schema` JSON Schema).
- Her aracın çıktısı, **mevcut Evidence Engine** ile uyumlu olsun (yeni model YOK).
- Dış ağ çağrısı içeren araçlar onay akışına (SafetyPolicy) tabi kalsın.

## 2. Mevcut dayanaklar (YENİ değil, genişletilecek)

| Bileşen | Dosya |
|---|---|
| `ToolSpec` (dataclass) | `core/agent/tools.py` |
| `ToolRegistry.BUILTIN` (24 araç tanımı) | `core/agent/tools.py` |
| `SafetyPolicy` + `Approval` + `ToolScope` | `core/agent/policy.py` |
| `ToolExecutor.run()` → `Observation` | `core/agent/executor.py` |
| `Planner.classify()` + `plan()` | `core/agent/planner.py` |
| `Observation` (dataclass) | `core/agent/executor.py` |

## 3. Sözleşme

### 3.1 ToolSpec (genişletilmiş)

Mevcut alanlara ek olarak:

```python
@dataclass
class ToolSpec:
    name: str
    target_types: List[str]
    description: str = ""
    calls_network: bool = False
    max_depth: int = 1
    requires_target: bool = True
    # YENİ (v1.4):
    input_schema: Optional[Dict] = None   # JSON Schema — kwargs doğrulaması
    output_kind: str = "data"             # "data" | "evidence" | "report_fragment"
    is_source_adapter: bool = False       # True ise PerceptionContract'e bağlanır
    gathers_evidence: bool = True         # False ise çıktısı kanıt sayılmaz (örn. help)
```

### 3.2 ToolResult (standart dönüş)

```python
@dataclass
class ToolResult:
    ok: bool
    tool: str
    data: Dict                    # normalize edilmiş sonuç
    evidence: List[Evidence]      # core/evidence/model.Evidence — örnek uyumlu
    error: Optional[str] = None
    observation_ref: str = ""     # ToolExecutor'un ürettiği gözlem id'sine bağ
```

**Kritik kural:** `ToolResult.evidence`, `core/evidence/model.Evidence.to_dict()` şemasıyla uyumlu **diclerden** oluşur — ikinci bir evidence modeli tanımlanmaz, umuluruz.

### 3.3 Çalıştırma sözleşmesi

```
executor.run(tool_name, target, registry, **kwargs) -> Observation
engine.decide(next_step) -> ToolDecision     # InvestigationEngine SEÇER
executor.execute(decision) -> ToolResult     # Agent İCRA EDER
```

Sıralama: `Engine karar verdi → SafetyPolicy onayladı → Agent çalıştırdı`.

## 4. İnvaryantlar

1. Her `ToolSpec` `name` + `description` içermek zorundadır; registry'e eklenmeden önce doğrulanır.
2. `calls_network=True` olan her araç `ToolScope.NETWORK` grubunda (onay gerekir); `scan`/`netscan` `DENIED` (istisna) — mevcut `policy.py` korunur.
3. `ok=True` ise `data` dolu; hata ise istisna fırlatılmaz, `error` alanına yazılır.
4. `gathers_evidence=False` araçlar (help, version) asla `evidence` üretemez.
5. Aynı `(tool, target)` çifti bir oturumda **tek kez** çalışır (tekrar koruması — mevcut `seen` seti v1.3.5).
6. Araçlar stateless'tir; durum Investigation State'e aittir.

## 5. Registry akışı

```
Loader (core/loader.py) -> modules/{...}
        │
        v
ToolRegistry.sync_with_modules(module_registry)   # mevcut
        │
        v
Planner.plan(intent, target) -> [PlanStep]        # mevcut
        │
        v
Policy.decide(step) -> approved/denied            # mevcut
        │
        v
Executor.run(step) -> Observation                 # mevcut + evidence bağı YENİ
```

## 6. Açık sorular

- [ ] `input_schema` ilk fazda zorunlu mu, yoksa registry'deki mevcut 24 araç için isteğe bağlı mı? (Öneri: zorunlu tut, eksikleri boş şema ile toleranslı geç.)
- [ ] `output_kind` planning'e (hangi araç kanıt üretir) bilgi sağlayacak mı, yalnızca kayıt amaçlı mı?
- [ ] Araçlar `PerceptionContract` ile nasıl bağlanır: `is_source_adapter=True` olanlar adaptör beyninden mi geçer?