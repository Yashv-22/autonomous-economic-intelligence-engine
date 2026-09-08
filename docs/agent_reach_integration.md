# Agent Reach Autonomous Integration

## 1. Overview & Architecture

Agent Reach (v1.5.0) is integrated into the `Researh-LLM` system as a modular, provider-agnostic capability backend.
It extends the existing Internet abstraction (`src/internet/providers/`) without replacing any core research loop, query generation, ranking, provenance tracking, security policy, or continuous learning workflows.

```
+-------------------------------------------------------------------------+
|                  Autonomous Research Engine & Loop                      |
+-------------------------------------------------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
MultiProviderSearchEngine                            BaseFetchProvider
          |                                                   |
   +------+------+------+                              +------+------+
   |             |      |                              |             |
DuckDuckGo     arXiv  AgentReachSearchProvider       WebFetcher   AgentReachFetchProvider
                        |                                            |
               +--------+--------+                          +--------+--------+
               |        |        |                          |        |        |
              Exa     GitHub   Bilibili                   Jina      RSS    YouTube
             (MCP)   (API/gh)  / V2EX                   (Reader) (parser)  (yt-dlp)
                                                                     |
                                                           Security Sanitizer
                                                        (SSRF + Prompt Injection)
                                                                     |
                                                             Raw / Normalized
                                                                  Corpus
                                                                     |
                                                            Provenance Ledger
                                                          (SHA-256 Merkle Root)
```

---

## 2. Integrated Components

### A. Search Provider (`src/internet/providers/agent_reach_provider.py`)
- **Class**: `AgentReachSearchProvider(BaseSearchProvider)`
- **Capabilities**:
  - **Exa AI Semantic Web Search**: Executes natural-language searches via `mcporter call exa.web_search_exa`.
  - **GitHub Search**: Code and repository discovery via `gh` CLI or GitHub REST API.
  - **Bilibili Public Search**: Chinese video community search via public web endpoints.
  - **V2EX Topics**: Chinese developer community hot topics and discussions.
  - **Web Fallback**: Automatic failover to DuckDuckGo if an upstream provider is unconfigured or throttled.
- **Normalization**: Returns `SearchResultItem` records preserving source URLs, domain, snippet, timestamp, rank, and metadata (`backend`, `channel`).

### B. Fetch Provider (`src/internet/providers/agent_reach_provider.py`)
- **Class**: `AgentReachFetchProvider(BaseFetchProvider)`
- **Capabilities**:
  - **General Web Pages**: Read through Agent Reach's Jina Reader backend (`https://r.jina.ai/<url>`), transforming web pages into clean, ad-free Markdown.
  - **RSS / Atom Feeds**: Parsed via `feedparser` into structured entries.
  - **YouTube Transcripts**: Extract video metadata and English subtitles via `yt-dlp` using the system's Node.js runtime.
  - **Strict SSRF Check**: Enforces `network_validator.validate_url(url)` to prevent access to private IP subnets and loopback addresses.
  - **Prompt Injection Defense**: Every retrieved document passes through `ContentSanitizer.detect_prompt_injection()` and `ContentSanitizer.sanitize_untrusted_text()` to defuse adversarial instructions (`<system>`, `ignore previous instructions`, etc.).
- **Normalization**: Returns `FetchResult` with full metadata, MIME type, latency, and SHA-256 content hash.

### C. System Tool (`src/tools/agent_reach_tool.py`)
- **Class**: `AgentReachTool(BaseTool)`
- **Tool Name**: `agent_reach`
- **Permission**: `ToolPermission.READ_ONLY`
- **Registered**: Automatically registered in `default_tool_registry`.
- **Supported Actions**:
  - `search`: `run(action="search", query="...", max_results=5, channel=None)`
  - `read_url`: `run(action="read_url", url="...")`
  - `read_rss`: `run(action="read_rss", url="...")`
  - `youtube_transcript`: `run(action="youtube_transcript", url="...")`
  - `doctor`: `run(action="doctor")`

---

## 3. Channel Readiness & Status

| Channel | Platform | Status | Backend / Method | Requirements |
|---|---|---|---|---|
| `web` | General Web | **Active (Tier 1)** | Jina Reader (`r.jina.ai`) | Zero-config |
| `rss` | RSS / Atom Feeds | **Active (Tier 1)** | `feedparser` | Zero-config |
| `youtube` | YouTube Transcripts | **Active (Tier 1)** | `yt-dlp` + Node.js | Configured (`--js-runtimes node`) |
| `exa_search` | Full-Web Semantic | **Active (Tier 1)** | `mcporter` + Exa MCP | Configured in `mcporter.json` |
| `v2ex` | V2EX Community | **Active (Tier 1)** | Public REST API | Zero-config |
| `bilibili` | Bilibili Videos | **Active (Tier 2)** | Public Search API | Zero-config |
| `github` | GitHub Code/Repos | **Active (Tier 1)** | GitHub REST / `gh` CLI | Zero-config public search |
| `reddit` | Reddit Posts | Login-Required | `opencli` / `rdt` | Requires Reddit session/cookies |
| `twitter` | Twitter / X | Login-Required | `twitter-cli` | Requires `TWITTER_AUTH_TOKEN` |
| `linkedin` | LinkedIn | Login-Required | `opencli` | Requires LinkedIn session |
| `xiaohongshu` | XiaoHongShu | Login-Required | `opencli` | Requires Chrome session |
| `facebook` | Facebook | Login-Required | `opencli` | Requires Facebook session |
| `instagram` | Instagram | Login-Required | `opencli` | Requires Instagram session |
| `xueqiu` | Xueqiu Finance | Login-Required | `opencli` | Requires Xueqiu session |
| `xiaoyuzhou` | Xiaoyuzhou Podcasts | Login-Required | Audio download + Whisper | Requires Whisper / Groq API key |

---

## 4. Security & Provenance Enforcement

1. **Untrusted Data Isolation**:
   External content retrieved via Agent Reach is treated strictly as **DATA**, never as **INSTRUCTIONS**.
2. **SSRF Guard**:
   Target URLs are checked before connection. Attempts to query `localhost`, `127.0.0.1`, `169.254.169.254`, or private subnets are blocked with HTTP 403.
3. **Cryptographic Lineage**:
   Every acquired artifact is hashed with SHA-256, stored in `RawCorpus`, decomposed into `SourceSpan`s, and logged into `ProvenanceLedger` generating a deterministic Merkle provenance root.

---

## 5. Verification Commands

Run diagnostics and tests:
```powershell
# Check Agent Reach platform health
agent-reach doctor

# Run integration tests
python -m unittest tests/test_agent_reach_integration.py

# Run complete system test suite
python -m unittest discover tests
```
