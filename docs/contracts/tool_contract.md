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
    capabilities: List[str] = field(default_factory=list)  # YENİ — capability/interface
    gathers_evidence: bool = True         # False ise çıktısı kanıt sayılmaz (örn. help)
```

**`input_schema` (v1.4 kararı):**
- Sözleşme seviyesinde **zorunlu**dür — yeni araçlar schema'sız registry'e **giremez** (registration-time doğrulama).
- Migration sırasında mevcut 24 araç için `{}` toleranslı geçiş değeri kullanılır; araçlar kontrollü şekilde teker teker gerçek şemaya migrate edilir.

**`output_kind` (v1.4 kararı):**
- **Yalnızca kayıt amaçlı metadata DEĞİLDİR.** Investigation Engine, tool capability değerlendirmesinde bunu kullanır:
  - `evidence` → bu aracın sonucu `evidence_log`'a girer (planlarken "kanıt üretecek araç" olarak işaretlenir).
  - `data` → sonuç bağlam bütçesine eklenir, evidence sayılmaz.
  - `report_fragment` → rapor block'larına bağlanır.
- Engine `select_next_step()` içinde bu metadata'ya göre "kanıt arayan adım mı, bağlam toplayan adım mı" ayrımını yapar.

**`capabilities` (is_source_adapter yerine — v1.4 kararı):**
- Tool ve Perception **aynı abstraction değildir**: bir tool, Perception adapter'i ÜZERİNDEN dış dünyaya erişir.
- Basit boolean yerine capability/interface ilişkisi kullanılır: ör. `"perception::source"` capability'sine sahip araç, runtime'da ilgili `SourceAdapter`'a bağlanmak zorundadır.
- Migration için eski boolean (`is_source_adapter`) SHİMDİLİK tutulabilir, ancak semantik nettir: **"bu tool dış kaynağı perception pipeline'ına bağlar"**.

### 3.2 ToolResult (standard tek dönüş tipi — canonical)

> **v1.4 kararı:** Agent/Engine sınırında **tek canonical sonuç tipi `ToolResult`'tür.** `Observation`, `ToolResult`'e bağlanan, Evidence Engine'in **iç gözlem kaydıdır** (paralel dış sözleşme değildir).

```python
@dataclass
class ToolResult:
    ok: bool
    tool: str
    data: Dict                    # normalize edilmiş sonuç
    evidence: List[Evidence]      # içeride mevcut core/evidence/model.Evidence nesneleri
    error: Optional[str] = None
    observation_ref: str = ""     # bağlı Observation id'si (Evidence Engine iç kaydı)
```

**Evidence temsili (v1.4 kararı):**
- **İçeride:** `ToolResult.evidence` → mevcut `core/evidence/model.Evidence` **nesneleri** listesidir.
- **Serialization/export:** Yalnızca bu aşamada `Evidence.to_dict()` çağrılır.
- İkinci bir Evidence modeli veya paralel schema **oluşturulmaz.**

**Observation ilişkisi (v1.4 kararı):**
- `ToolExecutor` aracı çalıştırır; dönüş Tipi `ToolResult`'tür.
- `Observation` (Evidence Engine'in gözlem kaydı) bu `ToolResult`'e `observation_ref` üzerinden bağlanır — iki ayrı "çalıştırma API'si" yoktur.

### 3.3 Çalıştırma sözleşmesi (tek akış)

```
engine.decide(next_step) -> ToolDecision                      # InvestigationEngine SEÇER
executor.execute(decision) -> ToolResult                      # Agent İCRA EDER — canonical dönüş
        └── (ToolResult.observation_ref) -> Observation       # Evidence Engine iç gözlem kaydı
```

**SADECE bu akış vardır.** Eski `executor.run() -> Observation` dış sözleşme olmaktan çıkar; `Observation` yalnızca `ToolResult`'e bağlı iç kayıt olarak üretilir.

Sıralama: `Engine karar verdi → SafetyPolicy onayladı → Agent çalıştırdı → ToolResult döndü → Engine state'i güncelledi`.

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

## 6. Açık sorular (v1.4 kararı ile kapatıldı / kalanlar)

- [x] `input_schema` zorunlu; mevcut 24 araç `{}` toleransıyla migrate edilir, yeni araçlar schema'sız girmez.
- [x] `output_kind` Investigation Engine'in tool capability değerlendirmesinde kullanılır (yalnızca kayıt değil).
- [x] Canonical sonuç tipi `ToolResult`; `Observation` ona bağlı iç kayıttır.
- [x] `ToolResult.evidence` içeride `Evidence` nesnesi, serialization'da `to_dict()`; ikinci model yok.
- [x] `is_source_adapter` → `capabilities` (capability/interface) tercih edilir; boolean migration için kalabilir, semantiği netleştirildi.

Kalan:
- [ ] Mevcut 24 `ToolSpec` için gerçek `input_schema`'ların tek tek yazılması (migration adımı).
- [ ] `Parked`: Eski `is_source_adapter` boolean'ının kaldırılma zamanı.