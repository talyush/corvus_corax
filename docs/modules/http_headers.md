# HTTP Header Intelligence Module

**Module**: `http_headers.py`  
**Version**: v0.8  
**Purpose**: HTTP header extraction, security evaluation, and technology fingerprinting

## Overview

The HTTP Header Intelligence Module performs comprehensive HTTP header analysis, including security header evaluation (CSP, HSTS, X-Frame-Options), CORS policy analysis, cookie security assessment, and technology fingerprinting from header signatures.

## Architecture

### Class Structure

```python
class HttpHeadersModule(BaseModule):
    name = "headers"
    
    def execute(self):
        # Normalize target (add https://)
        # Fetch HTTP headers
        # Parse security headers
        # Analyze CORS policy
        # Parse cookies
        # Detect technologies
        # Store in context
        # Return standardized payload
```

### Key Components

#### 1. Target Normalization (`_normalize_target`)

Ensures proper URL format:

- **Protocol Handling**: Adds `https://` if protocol not specified
- **Default Protocol**: Prefers HTTPS for security header evaluation
- **Return**: Normalized URL string

```python
def _normalize_target(self, target):
    target = target.strip()
    if target.startswith("http://") or target.startswith("https://"):
        return target
    return f"https://{target}"
```

#### 2. Cookie Parsing (`_parse_cookie_header`)

Detailed cookie attribute extraction:

- **Name/Value**: Extracts cookie name and value
- **Security Flags**: Detects HttpOnly, Secure, SameSite attributes
- **Value Truncation**: Truncates long values for display
- **Return**: Structured cookie data

```python
def _parse_cookie_header(self, cookie_str):
    parts = [p.strip() for p in cookie_str.split(";")]
    name_val = parts[0].split("=", 1)
    name = name_val[0] if name_val else "Unknown"
    value = name_val[1] if len(name_val) > 1 else ""
    
    httponly = False
    secure = False
    samesite = None
    
    for part in parts[1:]:
        part_lower = part.lower()
        if part_lower == "httponly":
            httponly = True
        elif part_lower == "secure":
            secure = True
        elif part_lower.startswith("samesite="):
            samesite = part.split("=", 1)[1]
    
    return {
        "name": name,
        "value": value[:20] + "..." if len(value) > 20 else value,
        "httponly": httponly,
        "secure": secure,
        "samesite": samesite
    }
```

#### 3. Security Header Analysis

##### CSP Analysis (`_analyze_csp`)

Content Security Policy evaluation:

- **Directive Parsing**: Extracts default-src, script-src, style-src directives
- **Unsafe Detection**: Detects unsafe-inline, unsafe-eval
- **Policy Strength**: Evaluates policy strictness
- **Return**: Structured CSP analysis

##### HSTS Analysis (`_analyze_hsts`)

HTTP Strict Transport Security evaluation:

- **Max-Age**: Extracts max-age value
- **IncludeSubDomains**: Detects includeSubDomains flag
- **Preload**: Detects preload flag
- **Return**: Structured HSTS analysis

##### X-Frame-Options Analysis

Clickjacking protection evaluation:

- **Directive**: Extracts DENY, SAMEORIGIN, ALLOW-FROM
- **Security Assessment**: Evaluates protection level
- **Return**: Structured X-Frame-Options analysis

#### 4. CORS Policy Analysis (`_analyze_cors`)

Cross-Origin Resource Sharing evaluation:

- **Origin Header**: Extracts Access-Control-Allow-Origin
- **Methods**: Extracts Access-Control-Allow-Methods
- **Credentials**: Extracts Access-Control-Allow-Credentials
- **Wildcard Detection**: Detects wildcard origin usage
- **Return**: Structured CORS analysis

#### 5. Technology Detection

##### Server Detection

Server header analysis:

- **Server String**: Extracts Server header value
- **Pattern Matching**: Matches against known server signatures
- **Version Detection**: Extracts version information
- **Return**: Server technology data

##### WAF/CDN Detection

WAF and CDN identification:

- **Header Patterns**: Matches against known WAF/CDN header signatures
- **Detection List**: Cloudflare, Akamai, Sucuri, AWS, etc.
- **Return**: List of detected WAF/CDN services

```python
WAF_CDN_HEADERS = [
    ("CF-Ray", r".+", "Cloudflare"),
    ("X-Sucuri-ID", r".+", "Sucuri WAF"),
    ("Server", r"cloudflare", "Cloudflare"),
    ("Via", r"akamai", "Akamai CDN"),
    # ... more patterns
]
```

## Data Flow

```
Input: url_or_host
    ↓
_normalize_target()
    ↓
HTTP Request (urllib)
    ↓
Header Extraction
    ↓
_parse_cookie_header() + Security Analysis + CORS Analysis + Tech Detection
    ↓
Structured HTTP Intelligence
    ↓
ContextManager.add_http_headers()
    ↓
Standardized Payload
```

## Context Integration

### HTTP Headers Data Storage

Headers are stored in `context.data["http_headers"]`:

```python
{
    "example.com": {
        "server": "nginx/1.18.0",
        "security_headers": {
            "csp": {
                "present": true,
                "policy": "default-src 'self'",
                "unsafe_inline": false,
                "unsafe_eval": false
            },
            "hsts": {
                "present": true,
                "max_age": 31536000,
                "include_subdomains": true,
                "preload": false
            },
            "x_frame_options": {
                "present": true,
                "directive": "SAMEORIGIN"
            },
            "x_content_type_options": {
                "present": true,
                "nosniff": true
            }
        },
        "cors": {
            "allow_origin": "*",
            "allow_methods": ["GET", "POST"],
            "allow_credentials": false,
            "wildcard_origin": true
        },
        "cookies": [
            {
                "name": "sessionid",
                "httponly": true,
                "secure": true,
                "samesite": "Lax"
            }
        ],
        "waf_cdn": ["Cloudflare"],
        "tech_stack": ["nginx"]
    }
}
```

### Relationships Added

- **Domain to Server**: `runs_on_server` relation
- **Domain to WAF/CDN**: `protected_by_waf` relation
- **Domain to Technology**: `uses_technology` relation

### Notes Added

- Missing security header warnings
- Insecure CORS policy warnings
- Cookie security warnings
- WAF/CDN detection notes

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
- **Connection Errors**: Returns error with connection details
- **SSL Errors**: Returns error with SSL details
- **HTTP Errors**: Returns error with HTTP status code

### Header Parsing Errors

- **Malformed Headers**: Skips malformed headers
- **Cookie Parse Errors**: Continues with successfully parsed cookies
- **Missing Headers**: Sets default values for missing headers

## Nexus Integration

### Technology Stack Correlation

Nexus Engine uses HTTP header intelligence for tech stack correlation:

```python
# RULE 11: Technology Stack Correlation
for domain, header_data in context.data["http_headers"].items():
    tech_stack = header_data.get("tech_stack", [])
    waf_cdn = header_data.get("waf_cdn", [])
    
    # Add WAF/CDN protection relations
    for waf in waf_cdn:
        context.add_derived_relation(
            src_type="domain", src_value=domain,
            relation="has_waf_protection",
            dst_type="waf_cdn", dst_value=waf,
            evidence=f"WAF/CDN detected: {waf}",
            confidence=0.9
        )
```

### Security Posture Assessment

Nexus Engine evaluates web security posture:

```python
# RULE 7: Web Security Posture Assessment
for domain, header_data in context.data["http_headers"].items():
    security = header_data.get("security_headers", {})
    
    if not security.get("hsts", {}).get("present"):
        context.add_derived_relation(
            src_type="domain", src_value=domain,
            relation="missing_security_header",
            dst_type="security", dst_value="HSTS",
            evidence="HSTS header not present",
            confidence=1.0
        )
```

### Admiralty Scoring

HTTP header intelligence has medium source reliability (B) due to potential header spoofing:

```python
EvidenceType.SECURITY_HEADER = {
    "base_weight": 10,
    "source_reliability": SourceReliability.B,  # Can be spoofed
    "info_reliability": InformationReliability.RELIABLE
}
```

## Output Format

### Success Payload

```json
{
  "module": "headers",
  "target": "https://example.com",
  "status": "success",
  "data": {
    "url": "https://example.com",
    "server": "nginx/1.18.0",
    "security_headers": {
      "csp": {
        "present": true,
        "policy": "default-src 'self'",
        "unsafe_inline": false
      },
      "hsts": {
        "present": true,
        "max_age": 31536000,
        "include_subdomains": true
      },
      "x_frame_options": {
        "present": true,
        "directive": "SAMEORIGIN"
      }
    },
    "cors": {
      "allow_origin": "*",
      "allow_methods": ["GET", "POST"],
      "wildcard_origin": true
    },
    "cookies": [
      {
        "name": "sessionid",
        "httponly": true,
        "secure": true,
        "samesite": "Lax"
      }
    ],
    "waf_cdn": ["Cloudflare"],
    "tech_stack": ["nginx"]
  },
  "notes": [
    {
      "text": "HSTS configured with max-age=31536000",
      "source": "http_headers",
      "severity": "info",
      "confidence": 1.0
    }
  ],
  "relationships": [
    {
      "src": {"type": "domain", "value": "example.com"},
      "relation": "runs_on_server",
      "dst": {"type": "server", "value": "nginx"},
      "evidence": "Server header",
      "confidence": 0.9
    }
  ]
}
```

### Error Payload

```json
{
  "module": "headers",
  "target": "https://example.com",
  "status": "error",
  "error": "HTTP request timeout",
  "notes": [],
  "relationships": []
}
```

## Performance Considerations

- **HTTP Request**: Single HTTP request per target
- **Header Parsing**: Minimal overhead
- **Pattern Matching**: Regex patterns for WAF/CDN detection
- **Cookie Parsing**: Linear time based on cookie count

## Security Considerations

- **HTTPS Preferred**: Uses HTTPS by default for security header evaluation
- **User Agent**: Uses configured user agent for requests
- **Cookie Data**: Only stores cookie metadata, not values
- **Header Spoofing**: Headers can be spoofed by server

## Future Enhancements

- **Response Body Analysis**: Analyze HTML body for additional tech detection
- **Cookie Value Analysis**: Analyze cookie values for patterns
- **Header Chain Analysis**: Analyze redirect header chains
- **HTTP/2 Support**: Support HTTP/2 header analysis
- **Timing Analysis**: Analyze response timing for WAF detection
