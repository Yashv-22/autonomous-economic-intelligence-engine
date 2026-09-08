# OmniRoute Integration & Inference Gateway Architecture

## 1. Overview & Architectural Role

OmniRoute is configured as a general-purpose, self-hosted LLM Inference Gateway for the **Autonomous AI Operating-Model Intelligence System**. It provides a unified, OpenAI-compatible proxy interface (`/v1/*`), health checking, dynamic model aliasing, quota-aware fallback, circuit-breaking, and end-to-end token auditing.

```
┌─────────────────────────────────────────────────────────────┐
│                    Research LLM System                      │
│             (Agents, Research Loop, Evaluator)              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             OmniRoute Inference Gateway (Port 20128)        │
│  - Unified OpenAI /v1 API    - Workload Model Aliases       │
│  - Live Audit Logging        - Cooldown & Fallback Engine   │
│  - Circuit Breakers          - WebSocket Live Stream        │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐┌──────────────────────────────┐
│  Google Gemini (AI Studio)   ││         Groq Cloud           │
│   gemini-3.7-flash (Reason)  ││    llama-3.3-70b-versatile   │
└──────────────────────────────┘└──────────────────────────────┘
```

> **Integration Boundary Note:** FreeLLMAPI operates independently on port `3001` and remains completely untouched. OmniRoute operates as an independent, standalone inference gateway on port `20128`.

---

## 2. Runtime Environment & Specifications

- **Location:** `infrastructure/OmniRoute/`
- **Version:** `v3.8.51`
- **Node.js Runtime:** `v24.20.0` (Engine policy: `>=22.22.2 <23 || >=24.0.0 <27` satisfied)
- **Package Manager:** `npm 11.19.0`
- **Native Dependencies:** All 31 externalized packages verified (including `better-sqlite3` native bindings).
- **Persistent Storage:** `AppData\Roaming\omniroute\storage.sqlite`
- **Database Migrations:** 170 migrations successfully applied.
- **Listening Ports:**
  - HTTP Server & Dashboard: `http://127.0.0.1:20128` (or `0.0.0.0:20128`)
  - Live WebSocket Server: `ws://127.0.0.1:20132`
  - Embed WebSocket Proxy: `http://127.0.0.1:20131`

---

## 3. Security-First Configuration

1. **Elimination of Default Passwords:**
   - The default insecure password (`CHANGEME`) was permanently removed.
   - The database management password was updated to a high-entropy secret using `bin/reset-password.mjs --password-stdin`.
   - `INITIAL_PASSWORD` in `infrastructure/OmniRoute/.env` was updated synchronously.
2. **Cryptographic Key Storage:**
   - `JWT_SECRET`, `STORAGE_ENCRYPTION_KEY`, and `API_KEY_SECRET` are automatically loaded from `AppData\Roaming\omniroute\server.env` with zero plain-text leaks in logs or reports.
3. **SSRF & Network Protections:**
   - Loopback and private IP space classifications are enforced via `src/lib/ipUtils.ts`.
   - Outbound proxy and internal fetch requests pin loopback origins to prevent request forgery.
4. **Authentication & Access Control:**
   - Dashboard endpoints (`/dashboard`, `/api/providers`, `/api/models`, `/api/keys`) require session cookie authentication via `/api/auth/login`.
   - API endpoints (`/v1/models`, `/v1/chat/completions`) require Bearer API key authentication.

---

## 4. Model Registry & Workload Aliasing

OmniRoute maps high-level research workload classes to active backend provider models via the `modelAliases` settings engine:

| Workload Class | Alias Name | Target Model | Purpose / Capability |
| :--- | :--- | :--- | :--- |
| **REASONING** | `research-reasoning` / `reasoning` | `gemini/gemini-3.7-flash` | Deep analysis, synthesis, contradiction resolution, formal reasoning token output |
| **FAST** | `research-fast` / `fast` | `gemini/gemini-3.7-flash` | Rapid extraction, triage, entity tagging, query generation |
| **GENERAL** | `research-general` / `general` | `gemini/gemini-3.7-flash` | General orchestration, plan formulation, executive summary drafting |

---

## 5. Verified Endpoints & Test Matrix

| Endpoint | Method | Auth Mode | Test Payload | Result |
| :--- | :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | Public | None | `200 OK` (`{"status": "ok"}`) |
| `/login` | `GET` | Public | None | `200 OK` (Dashboard UI) |
| `/api/auth/login` | `POST` | Management | Secured credentials | `200 OK` (`{"success": true}`) |
| `/api/providers` | `GET` | Session | None | `200 OK` (2 active provider connections) |
| `/api/models` | `GET` | Session | None | `200 OK` (18 active provider models) |
| `/v1/models` | `GET` | Bearer Key | None | `200 OK` (533 models in catalog) |
| `/v1/chat/completions` | `POST` | Bearer Key | Non-streaming test prompt | `200 OK` (`choices[0].message.content = "4"`) |
| `/v1/chat/completions` | `POST` | Bearer Key | Streaming (`stream: true`) | `200 OK` (4 SSE chunks received, content: `"4"`) |
| `/v1/chat/completions` | `POST` | Bearer Key | Alias: `research-reasoning` | `200 OK` (Auto-routed to `gemini-3.7-flash`) |
| `/api/v1/ws` | `GET` | Public | `handshake=1` | `200 OK` (WebSocket handshake valid) |
| `/v1/chat/completions` | `POST` | Invalid Key | Invalid token | `401 Unauthorized` / Auth rejected |
| `/v1/chat/completions` | `POST` | Bearer Key | Non-existent model | `401/404` Handled with structured JSON |

---

## 6. Audit & Observability Verification

OmniRoute logs all inbound inference requests into the SQLite `call_logs` table. Inspected entries verify tracking of:
- `id`, `timestamp`, `method`, `path`, `status`
- `model`, `requested_model`, `provider`
- `tokens_in`, `tokens_out`, `tokens_reasoning`
- `duration`, `correlation_id`

---

## 7. Future Integration Architecture

When ready to integrate OmniRoute into the main Research LLM Python pipeline, the cleanest boundary is via the existing `src/gateway/provider_openai.py` provider:

```python
# Option A: Zero-Code Configuration via Environment
# Point the existing OpenAI provider at OmniRoute's /v1 endpoint:
OPENAI_BASE_URL="http://127.0.0.1:20128/v1"
OPENAI_API_KEY="<OMNIROUTE_API_KEY>"

# Option B: Dedicated OmniRoute Gateway Provider (src/gateway/provider_omniroute.py)
class OmniRouteModelProvider(OpenAIModelProvider):
    name: str = "omniroute"
    def __init__(self):
        super().__init__(
            api_key=os.environ.get("OMNIROUTE_API_KEY"),
            base_url=os.environ.get("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
        )
```

No code modifications were made to `src/gateway/` during this setup, keeping both the Research LLM and FreeLLMAPI completely stable and regression-free.
