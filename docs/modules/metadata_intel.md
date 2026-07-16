# Metadata Collection Module

**Module**: `metadata_intel.py`  
**Version**: v0.8  
**Purpose**: Robots.txt, sitemap, favicon hash, and security.txt collection for infrastructure profiling

## Overview

The Metadata Collection Module extracts metadata from web targets including robots.txt parsing for crawler directives, sitemap.xml extraction for content structure, favicon hash calculation using Shodan-compatible MurmurHash3, and security.txt discovery for security policy analysis.

## Architecture

### Class Structure

```python
class MetadataIntelModule(BaseModule):
    name = "metadata"
    
    def execute(self):
        # Normalize target URL
        # Fetch robots.txt
        # Fetch sitemap.xml
        # Fetch and calculate favicon hash
        # Fetch security.txt
        # Parse and analyze
        # Store in context
        # Return standardized payload
```

### Key Components

#### 1. MurmurHash3 Implementation

Pure-Python MurmurHash3_x86_32 (Shodan-compatible):

```python
def _murmur3_x86_32(data: bytes, seed: int = 0) -> int:
    length = len(data)
    h1 = seed & 0xFFFFFFFF
    c1 = 0xcc9e2d51
    c2 = 0x1b873593
    
    nblocks = length // 4
    for i in range(nblocks):
        k1 = int.from_bytes(data[i * 4:i * 4 + 4], "little")
        k1 = (k1 * c1) & 0xFFFFFFFF
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xFFFFFFFF
        k1 = (k1 * c2) & 0xFFFFFFFF
        h1 ^= k1
        h1 = ((h1 << 13) | (h1 >> 19)) & 0xFFFFFFFF
        h1 = (h1 * 5 + 0xe6546b64) & 0xFFFFFFFF
    
    # Tail processing
    tail = data[nblocks * 4:]
    k1 = 0
    tail_len = length & 3
    if tail_len >= 3:
        k1 ^= tail[2] << 16
    if tail_len >= 2:
        k1 ^= tail[1] << 8
    if tail_len >= 1:
        k1 ^= tail[0]
        k1 = (k1 * c1) & 0xFFFFFFFF
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xFFFFFFFF
        k1 = (k1 * c2) & 0xFFFFFFFF
        h1 ^= k1
    
    h1 ^= length
    h1 ^= (h1 >> 16)
    h1 = (h1 * 0x85ebca6b) & 0xFFFFFFFF
    h1 ^= (h1 >> 13)
    h1 = (h1 * 0xc2b2ae35) & 0xFFFFFFFF
    h1 ^= (h1 >> 16)
    
    return h1
```

#### 2. Favicon Hash Calculation (`_calculate_favicon_hash`)

Calculates Shodan-compatible favicon hash:

- **URL Construction**: Constructs favicon URL (/favicon.ico)
- **HTTP Fetch**: Fetches favicon image data
- **Hash Calculation**: Uses MurmurHash3 algorithm
- **Return**: Integer hash value

```python
def _calculate_favicon_hash(self, base_url):
    favicon_url = f"{base_url}/favicon.ico"
    try:
        req = urllib.request.Request(
            favicon_url,
            headers={"User-Agent": self.config.get("user_agent", "CorvusCorax/0.8")}
        )
        with urllib.request.urlopen(req, timeout=self.config.get("timeout", 3.0)) as response:
            favicon_data = response.read()
            return _murmur3_x86_32(favicon_data)
    except Exception:
        return None
```

#### 3. Robots.txt Parsing (`_parse_robots`)

Parses robots.txt for crawler directives:

- **User-Agent Extraction**: Extracts user-agent directives
- **Disallow Rules**: Extracts disallow paths
- **Allow Rules**: Extracts allow paths
- **Crawl-Delay**: Extracts crawl delay values
- **Sitemap**: Extracts sitemap URLs
- **Return**: Structured robots.txt data

```python
def _parse_robots(self, robots_content):
    directives = []
    sitemaps = []
    
    for line in robots_content.splitlines():
        line = line.strip()
        if line.lower().startswith("user-agent:"):
            directives.append({"type": "user-agent", "value": line.split(":")[1].strip()})
        elif line.lower().startswith("disallow:"):
            directives.append({"type": "disallow", "value": line.split(":")[1].strip()})
        elif line.lower().startswith("allow:"):
            directives.append({"type": "allow", "value": line.split(":")[1].strip()})
        elif line.lower().startswith("crawl-delay:"):
            directives.append({"type": "crawl-delay", "value": line.split(":")[1].strip()})
        elif line.lower().startswith("sitemap:"):
            sitemaps.append(line.split(":")[1].strip())
    
    return {"directives": directives, "sitemaps": sitemaps}
```

#### 4. Sitemap.xml Parsing (`_parse_sitemap`)

Parses sitemap.xml for content structure:

- **XML Parsing**: Uses ElementTree for XML parsing
- **URL Extraction**: Extracts URL locations
- **Priority Extraction**: Extracts priority values
- **ChangeFreq Extraction**: Extracts change frequency
- **LastMod Extraction**: Extracts last modification dates
- **Return**: Structured sitemap data

```python
def _parse_sitemap(self, sitemap_content):
    urls = []
    
    try:
        root = ET.fromstring(sitemap_content)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        
        for url_elem in root.findall("ns:url", namespace):
            loc = url_elem.find("ns:loc", namespace)
            priority = url_elem.find("ns:priority", namespace)
            changefreq = url_elem.find("ns:changefreq", namespace)
            lastmod = url_elem.find("ns:lastmod", namespace)
            
            urls.append({
                "loc": loc.text if loc is not None else "",
                "priority": priority.text if priority is not None else None,
                "changefreq": changefreq.text if changefreq is not None else None,
                "lastmod": lastmod.text if lastmod is not None else None
            })
    except Exception:
        pass
    
    return urls
```

#### 5. Security.txt Parsing (`_parse_security_txt`)

Parses security.txt for security policy:

- **Field Extraction**: Extracts standard fields (Contact, Expires, etc.)
- **URI Parsing**: Parses contact URIs (mailto:, https:)
- **Return**: Structured security.txt data

```python
def _parse_security_txt(self, security_content):
    fields = {}
    
    for line in security_content.splitlines():
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip().lower()] = value.strip()
    
    return fields
```

#### 6. Generator Meta Tag Extraction (`_extract_generator`)

Extracts generator meta tags from HTML:

- **Meta Tag Parsing**: Searches for generator meta tags
- **CMS Detection**: Identifies CMS from generator values
- **Return**: Generator value or None

```python
def _extract_generator(self, html_content):
    pattern = r'<meta\s+name=["\']generator["\']\s+content=["\']([^"\']+)["\']'
    match = re.search(pattern, html_content, re.IGNORECASE)
    return match.group(1) if match else None
```

## Data Flow

```
Input: url_or_host
    ↓
Normalize URL
    ↓
Fetch robots.txt → Parse Directives
    ↓
Fetch sitemap.xml → Parse URLs
    ↓
Fetch favicon.ico → Calculate MurmurHash3
    ↓
Fetch security.txt → Parse Fields
    ↓
Fetch HTML → Extract Generator
    ↓
Structured Metadata Intelligence
    ↓
ContextManager.add_metadata_intel()
    ↓
Standardized Payload
```

## Context Integration

### Metadata Data Storage

Metadata is stored in `context.data["metadata_intel"]`:

```python
{
    "example.com": {
        "robots": {
            "present": true,
            "directives": [
                {"type": "user-agent", "value": "*"},
                {"type": "disallow", "value": "/admin"}
            ],
            "sitemaps": ["https://example.com/sitemap.xml"]
        },
        "sitemap": {
            "present": true,
            "urls": [
                {
                    "loc": "https://example.com/page1",
                    "priority": "0.8",
                    "changefreq": "weekly",
                    "lastmod": "2024-01-01"
                }
            ]
        },
        "favicon_hash": 1234567890,
        "security": {
            "present": true,
            "contact": "mailto:security@example.com",
            "expires": "2025-01-01"
        },
        "generator": "WordPress 6.1.3"
    }
}
```

### Relationships Added

- **Domain to Sitemap**: `has_sitemap` relation
- **Domain to Security Contact**: `has_security_contact` relation
- **Domain to Generator**: `uses_cms` relation

### Notes Added

- Robots.txt discovery notes
- Sitemap discovery notes
- Favicon hash notes
- Security.txt discovery notes
- Generator detection notes

## Configuration

### Required Config Parameters

```json
{
  "timeout": 3.0,
  "user_agent": "CorvusCorax/0.8"
}
```

### Module-Specific Config

None - uses default timeout from config.

## Error Handling

### HTTP Request Errors

- **Timeout**: Returns error with timeout message
- **404 Not Found**: Sets present=False for missing resources
- **Connection Errors**: Returns error with connection details

### Parse Errors

- **Invalid XML**: Continues with partial parsing
- **Malformed Robots.txt**: Continues with successfully parsed directives
- **Invalid Security.txt**: Continues with successfully parsed fields

## Nexus Integration

### Shared Infrastructure Detection

Nexus Engine uses favicon hash for shared infrastructure detection:

```python
# RULE 9: Shared Favicon Pivoting
favicon_hashes = {}
for domain, meta_data in context.data["metadata_intel"].items():
    hash_val = meta_data.get("favicon_hash")
    if hash_val:
        favicon_hashes.setdefault(hash_val, []).append(domain)

for hash_val, domains in favicon_hashes.items():
    if len(domains) >= 2:
        for dom_a, dom_b in combinations(domains, 2):
            context.add_derived_relation(
                src_type="domain", src_value=dom_a,
                relation="shares_favicon",
                dst_type="domain", dst_value=dom_b,
                evidence=f"Both domains share favicon hash {hash_val}",
                confidence=0.85
            )
```

### Metadata Contact Mapping

Nexus Engine maps metadata contacts to entities:

```python
# RULE 10: Metadata Contact Mapping
for domain, meta_data in context.data["metadata_intel"].items():
    security = meta_data.get("security", {})
    contact = security.get("contact")
    
    if contact:
        context.add_derived_relation(
            src_type="domain", src_value=domain,
            relation="has_security_contact",
            dst_type="contact", dst_value=contact,
            evidence="security.txt contact field",
            confidence=0.9
        )
```

### Admiralty Scoring

Metadata intelligence has medium source reliability (B) due to potential spoofing:

```python
EvidenceType.SHARED_FAVICON = {
    "base_weight": 25,
    "source_reliability": SourceReliability.B,  # Can be spoofed
    "info_reliability": InformationReliability.PROBABLY_TRUE
}
```

## Output Format

### Success Payload

```json
{
  "module": "metadata",
  "target": "https://example.com",
  "status": "success",
  "data": {
    "url": "https://example.com",
    "robots": {
      "present": true,
      "directives": [
        {"type": "user-agent", "value": "*"},
        {"type": "disallow", "value": "/admin"}
      ],
      "sitemaps": ["https://example.com/sitemap.xml"]
    },
    "sitemap": {
      "present": true,
      "urls": [
        {
          "loc": "https://example.com/page1",
          "priority": "0.8"
        }
      ]
    },
    "favicon_hash": 1234567890,
    "security": {
      "present": true,
      "contact": "mailto:security@example.com"
    },
    "generator": "WordPress 6.1.3"
  },
  "notes": [
    {
      "text": "robots.txt discovered with 2 directives",
      "source": "metadata_intel",
      "severity": "info",
      "confidence": 1.0
    }
  ],
  "relationships": [
    {
      "src": {"type": "domain", "value": "example.com"},
      "relation": "has_sitemap",
      "dst": {"type": "sitemap", "value": "https://example.com/sitemap.xml"},
      "evidence": "robots.txt sitemap directive",
      "confidence": 1.0
    }
  ]
}
```

### Error Payload

```json
{
  "module": "metadata",
  "target": "https://example.com",
  "status": "error",
  "error": "HTTP request timeout",
  "notes": [],
  "relationships": []
}
```

## Performance Considerations

- **Multiple HTTP Requests**: Up to 5 HTTP requests per target
- **Hash Calculation**: MurmurHash3 is fast
- **XML Parsing**: ElementTree parsing is efficient
- **Regex Matching**: Minimal overhead for generator extraction

## Security Considerations

- **Public Resources**: All resources are publicly accessible
- **Favicon Hash**: Shodan-compatible for external correlation
- **Security.txt**: Standard security policy location
- **No Authentication**: No authentication required

## Future Enhancements

- **Well-Known URIs**: Support .well-known/ security.txt location
- **Favicon Variants**: Check multiple favicon locations
- **Robots.txt Analysis**: Analyze for hidden paths
- **Sitemap Depth**: Recursively parse sitemap index files
- **Meta Tag Analysis**: Extract additional meta tags for tech detection
