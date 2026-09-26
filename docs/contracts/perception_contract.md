# Perception Contract — core/perception (v1.4)

Corvus'un dış dünyayı "gördüğü" yüzey. Dış saldırı yüzeyini **tek, kontrollü, normalleştiren, kökenini kanıtlayan** bir köprüye indirger.

> Felsefe: Corvus bugün modülleri doğrudan `ContextManager`'a yazar. v1.4 bunu kırar: dış kaynaktan gelen HER bilgi bu kontrattan geçmeden world modeli kirletemez.

---

## 1. Amaç

- Dış dünyadan **public/authorized** kaynaklardan veri topla.
- Ham veriyi **normalize** et (kaynak formatına bağımlılığı kır).
- Her veri parçasına **provenance** zımbala (nereden, hangi yöntemle, ne zaman, kimliği ne).
- Normalleştirilmiş + kökenli veriyi **mevcut Evidence Engine'e** aktar.
- LLM'i bu boru hattının DIŞINDA tut (LLM yalnızca ses/ifade katmanıdır, veri sahibi değildir).

## 2. İlgili mevcut bileşenler (YENİ dosya açmadan önce bunlar üzerine kurulacak)

| Bileşen | Dosya | Rol |
|---|---|---|
| `SourceAdapter` | `core/perception/adapters/` | YENİ — mevcut `modules/*.py` sensörlerini sarar |
| `EvidenceExtractor` | `core/evidence/extractor.py` | Ham payload → `Observation` → `Evidence` |
| `Evidence` modeli | `core/evidence/model.py` | Atomik kanıt kaydı (status: VALIDATED/UNVERIFIABLE...) |
| `LineageTracker` | `core/evidence/lineage.py` | Provenance silsilesi + IntelligenceGaps |
| `Corroborator` | `core/evidence/corroboration.py` | Çapraz kaynak teyidi + çelişki |
| `ContextManager` | `core/context.py` | World model — yalnızca doğrulama sonrası yazılır |
| `ModuleLoader` | `core/loader.py` | Mevcut modülleri yükler |

## 3. Sözleşme

### 3.1 Kaynak Beyanı (SourceDeclaration)

Her kaynak/adaptör, kendini beyan etmek zorundadır:

```python
@dataclass
class SourceDeclaration:
    source_id: str                 # "whois", "social", "github"...
    kind: str                      # "http", "dns", "registry", "api"...
    auth_level: str                # "public" | "authorized" | "local"
    base_url: Optional[str] = None
    requires_key: bool = False
    rate_limit: float = 1.0        # saniye başına istek sınırı
```

### 3.2 Algı Çağrısı (PerceptionCall)

```
perceive(source_id: str, intent, target, params) -> PerceptionResult
```

Mevcut modül `execute()` çağrısını sarmalar; asla doğrudan context yazmaz.

### 3.3 PerceptionResult (standart çıktı)

```python
@dataclass
class PerceptionResult:
    ok: bool
    source: SourceDeclaration
    target: str
    target_type: str                       # ip|domain|person|email|phone|org...
    raw: Any                               # modülün ham çıktısı (evidence'a gitmez)
    normalized: Dict                       # KANONİK form — dünya modeline gidecek şey bu
    provenance: Dict                       # köken zımbası (aşağıda)
    error: Optional[str] = None
```

### 3.4 Provenance zımbası (zorunlu alanlar)

```python
{
  "source": "social",
  "source_url": "https://...",      # veya API tanımlayıcısı + endpoint
  "fetched_at": "2026-09-..." ,
  "method": "GET" | "search" | "api_call" ...,
  "auth": "public" | "authorized",
  "raw_hash": "sha256-16"           # ham kayıt bütünlüğü (Evidence.raw_hash uyumlu)
}
```

### 3.5 Normalizasyon şeması (kasıtlı minumum)

Maçolama: `normalized` alanı, `ContextManager`'ın `add_entity` / `add_relation` imzalarıyla **birebir** hizalanır:

```python
normalized = {
  "entities": [ {"type":"person","value":"Ahmet Yılmaz","properties":{...}} ],
  "relations": [ {"src":{"type":"person","value":"Ahmet"},"relation":"works_at",
                  "dst":{"type":"org","value":"Acme"},"confidence":0.55} ],
  "notes": [...]
}
```

## 4. İnvaryantlar (kurallar)

1. **Context yazma yasağı** — modüller/kaynaklar `context.write()` ÇAĞIRAMAZ. Tek geçit: `perceive()` → normalize → `evidence` → doğrulama → context.
2. **Kanıt zorunluluğu** — `ok=True` ise veri, `Evidence` kaydına dönüştürülmeden dünya modeline giremez.
3. **Seed ≠ Evidence** — `source="user_input"` olan veri provenance olarak `seed` kalır; asla evidence statüsüne taşınmaz (mevcut `context.add_entity` kuralını korur).
4. **Sahipsiz veri yok** — `provenance.source` boşsa parça yutulur (drop).
5. **Kanal kısıtı** — Dış ağ çağrısı yalnızca adaptör kategorisinden gelir; çekirdek ve cognitive katman dışa "ses" çıkarmaz.

## 5. Akış (perceive → evidence → world model)

```
[SourceAdapter.fetch()]      ham veri
        │
        ▼
[pipeline.normalize()]       kaynak bağımsız kanonik form
        │
        ▼
[provenance stamp()]         source_url + fetched_at + method + raw_hash
        │
        ▼
[EvidenceExtractor]          Observation -> Evidence (mevcut engine)
        │
        ▼
[Validator + Corroborator]   doğrula, çapraz kaynak teyit et
        │
        ▼
[ContextManager]             world model'e yaz (yalnızca buradan)
```

## 6. Kullanım dışı bırakılacak akış

Eski: `modules/*.py` doğrudan `self.context.add_entity()` çağırıyordu.
Yeni: modül aynı kalır ama çıktısı `PerceptionResult` olarak dışa akar; context yazımı yalnızca pipeline içindir.

## 7. Açık sorular (birlikte netleştirilecek)

- [ ] Sorgu arayüzü: `ask(sql)` **yok** — geçmiş gözlemlere erişim için mevcut `MuninnRecallEngine`/`ContextManager.query_entities` üzerine sorgu API'si mi kurulacak (öneri), yoksa gerçek bir veritabanı mı?
- [ ] Modüllerin içindeki `self.context.add_entity` çağrıları: adaptör katmanı Wrapper olarak mı (modüllere dokunmadan) yoksa refactor edilerek mi yapılacak? (Öneri: ilk faz Wrapper — kırılım riski sıfır.)
- [ ] Authorized kaynaklar için API-key yönetimi `.env` üzerinden mi, credentials dosyası mı?