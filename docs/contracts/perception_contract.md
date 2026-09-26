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
| `SourceAdapter` | `core/perception/adapters/` | YENİ — mevcut `modules/*.py` sensörlerini **sarmalar (Wrapper)** |
| `EvidenceExtractor` | `core/evidence/extractor.py` | Ham payload → `Observation` → `Evidence` |
| `Evidence` modeli | `core/evidence/model.py` | Atomik kanıt kaydı (status: VALIDATED/UNVERIFIABLE...) |
| `EvidenceValidator` | `core/evidence/validator.py` | Kanıt durumu (VALIDATED / SYNTAX_ERROR / UNVERIFIABLE / EXPIRED) |
| `LineageTracker` | `core/evidence/lineage.py` | Provenance silsilesi + IntelligenceGaps |
| `Corroborator` | `core/evidence/corroboration.py` | Çapraz kaynak teyidi + çelişki |
| `ContextManager` | `core/context.py` | World model — yalnızca ELIGIBILITY gate'i geçen yazılır |
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

Mevcut modül `execute()` çağrısını **Wrapper** aracılığıyla sarar; asla doğrudan context yazmaz.

> **v1.4 kararı:** Mevcut `modules/*.py` dosyaları topluca refactor edilmez. Adapter/wrapper katmanı, modülleri Perception pipeline'ına bağlar — migration düşük riskli ve geri çevrilebilir olur.

### 3.3 PerceptionResult (standart çıktı)

```python
@dataclass
class PerceptionResult:
    ok: bool
    source: SourceDeclaration
    target: str
    target_type: str                       # ip|domain|person|email|phone|org...
    raw: Any                               # modülün ham çıktısı (evidence'a gitmez)
    normalized: Dict                       # KANONİK form — dünya modeline aday olan şey bu
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
  "raw_hash": "<16-hex>"           # core/evidence/model.py:22 ile BİREBİR aynı formül
}
```

**`raw_hash` — gerçek uygulama ile birebir uyum (v1.4 kararı):**
```python
raw_hash = hashlib.sha256(str(payload).encode("utf-8")).hexdigest()[:16]
```
Yani: SHA-256'nın ilk 16 heksadesimal karakteri — `core/evidence/model.py` `Observation.raw_hash` ile **aynı**. Ayrı bir hash standardı üretilmez; Perception, Observation oluşturulurken aynı hesaplamayı kullanır.

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

### 3.6 World-model alınabilirlik (ELIGIBILITY gate) — YENİ

Bir verinin `ContextManager`'a yazılması için gereken koşullar **açıkça** tanımlı; Evidence'in "var olması" tek başına yazma garantisi DEĞİLDİR:

```python
eligibility_state = {
    "eligible": bool,
    "gate": "evidence" | "validation" | "provenance" | "seed",
    "reason": str,
}
```

Yazım kuralları:
- Yalnızca `Evidence.status == "VALIDATED"` (veya çapraz teyitle `A1/B1` admiralty'ye ulaşan) bilgiler world model'e **doğrulanmış gerçek** olarak yazılır.
- `UNVERIFIABLE`, `SYNTAX_ERROR`, `EXPIRED`, `MALFORMED`, `CONFLICT` statüleri **yazılmaz**; yalnızca `IntelligenceGaps` / gap listesine işlenir.
- `provenance.auth == "user_input"` veya `status == "seed"` olan veri asla `verified` bayrağı taşımaz — seed kendi kaydında kalır.

## 4. İnvaryantlar (kurallar)

1. **Context yazma yasağı** — modüller/kaynaklar `context.write()` ÇAĞIRAMAZ. Tek geçit: `perceive()` → normalize → `evidence` → **eligibility gate** → context.
2. **Evidence varlığı yazma garantisi değildir** — 3.6'daki eligibility kuralları (status, provenance, validation) geçerli olmadan world model'e yazılamaz.
3. **Seed ≠ Evidence** — `source="user_input"` olan veri provenance olarak `seed` kalır; asla evidence statüsüne taşınmaz (mevcut `context.add_entity` kuralını korur).
4. **Sahipsiz veri yok** — `provenance.source` boşsa parça yutulur (drop).
5. **Kanal kısıtı** — Dış ağ çağrısı yalnızca adaptör kategorisinden gelir; çekirdek ve cognitive katman dışa "ses" çıkarmaz.

## 5. Akış (perceive → evidence → world model)

```
[SourceAdapter.fetch()]      ham veri (modül execute() wrapper'ı)
        │
        ▼
[pipeline.normalize()]       kaynak bağımsız kanonik form
        │
        ▼
[provenance stamp()]         source_url + fetched_at + method + raw_hash (model.py:22)
        │
        ▼
[EvidenceExtractor]          Observation -> Evidence (mevcut engine)
        │
        ▼
[EvidenceValidator]          VALIDATED | SYNTAX_ERROR | UNVERIFIABLE | EXPIRED
        │
        ▼
[ELIGIBILITY GATE]           Yalnızca VALIDATED -> yazılabilir; gerisi gaps'e
        │
        ▼
[ContextManager]             world model'e yaz (yalnızca buradan)
```

## 6. Kullanım dışı bırakılacak akış

Eski: `modules/*.py` doğrudan `self.context.add_entity()` çağırıyordu.
Yeni: modül aynı kalır ama çıktısı `PerceptionResult` olarak dışa akar; context yazımı yalnızca eligibility gate geçtikten sonra pipeline içinden yapılır.

## 7. Credentials / secret yönetimi (v1.4 kararı)

- **Mevcut provider/secret deseni kullanılır:** `.env` → `core/__init__._load_env_file()` → `os.getenv()` (ör: `api_providers.py`'de `CORVUS_OLLAMA_HOST`).
- Credential'lar **asla** source adapter içine veya Git'e gömülmez.
- `.env` yalnızca **secret/config katmanı** olarak beyan edilir (`.env` zaten `.gitignore`'da).
- Authorized kaynak adaptörleri anahtarını `KEY = os.getenv("<PREFIX>_API_KEY")` ile okur; yoksa `requires_key=True` + `auth_level="authorized"` olarak beyan edilir ve kullanım anında okuyucuya açıklanır.

## 8. Kararlar özeti (v1.4)

- [x] Wrapper yaklaşımı — modüller topluca refactor edilmez.
- [x] Evidence varlığı ≠ ContextManager yazma garantisi; eligibility gate tanımlı.
- [x] UNVERIFIABLE / seed bilgiler world model'e doğrulanmış gerçek olarak yazılmaz.
- [x] `raw_hash` = `model.py:22` (SHA-256 → ilk 16 hex) ile birebir.
- [x] Credential'lar mevcut `.env → env → provider` deseninden; kaynak içine gömülmez.