# FreeLLMAPI Autonomous Inference Infrastructure Integration

## 1. Overview & Architecture

FreeLLMAPI is integrated into the `Researh-LLM` system as an infrastructure-level model routing and inference provider. It exposes an OpenAI-compatible interface (`/v1/chat/completions`, `/v1/models`) backed by free-tier multi-provider balancing, automatic failover, and local quota management.

In the Research LLM architecture, FreeLLMAPI is encapsulated behind the existing `ModelGateway` abstraction (`src/gateway/`), preserving agent decoupling and system modularity.

```
+-------------------------------------------------------------------------+
|                  Autonomous Research Agents & Engine                    |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                    ModelGateway (src/gateway/gateway.py)                |
|  - Token metering & cost accounting                                     |
|  - Event bus observability (MODEL_GENERATION_COMPLETED)                 |
|  - Multi-tier fallback router                                           |
+-------------------------------------------------------------------------+
         |                       |                        |
         v                       v                        v
+-----------------+     +-----------------+     +-------------------------+
| Gemini Provider |     | OpenAI Provider |     | FreeLLMAPI Provider     |
| (Direct API)    |     | (Direct API)    |     | (src/gateway/provider)  |
+-----------------+     +-----------------+     +-------------------------+
         |                       |                                |
         | (fails/throttled)     | (fails/throttled)              |
         +-----------------------+--------------------------------+
                                 |
                                 v
                +---------------------------------+
                |   FreeLLMAPI Daemon (Port 3001) |
                |   OpenAI-Compatible Engine      |
                |   (infrastructure/FreeLLMAPI/)  |
                +---------------------------------+
                         |               |
                         v               v
                +----------------+ +--------------+
                | Google Gemini  | | Groq Models  |
                | Free Tier Pool | | (Llama 3.3)  |
                +----------------+ +--------------+
                                 |
                                 | (all providers fail)
                                 v
                +---------------------------------+
                | MockModelProvider (Deterministic|
                | fallback, ensures 0 crashes)    |
                +---------------------------------+
```

---

## 2. Integrated Components

### A. Provider Adapter (`src/gateway/provider_freellmapi.py`)
- **Class**: `FreeLLMAPIModelProvider(BaseModelProvider)`
- **Capabilities**:
  - **OpenAI Compatibility**: Posts standard `/v1/chat/completions` JSON payloads and parses OpenAI-style response objects.
  - **Model Catalog Listing**: Calls `/v1/models` with unified authentication to inspect operational models across platforms.
  - **Zero-Configuration Key Auto-Discovery**: Automatically queries `infrastructure/FreeLLMAPI/server/data/freeapi.db` for `unified_api_key` if `FREELLMAPI_API_KEY` is not explicitly set in the environment.
  - **Token & Cost Accounting**: Normalizes prompt tokens, completion tokens, execution latency, and records cost as `$0.00` for free-tier routing.
  - **Error Translation**: Translates HTTP errors (e.g. 401 Unauthorized, 429 Rate Limit) into system `ModelGatewayError` instances.

### B. Gateway Routing & Multi-Tier Fallback (`src/gateway/gateway.py`)
- **Registration**: Registered in `ModelGateway.providers["freellmapi"]`.
- **Model Resolution**: Resolves `settings.model.freellmapi_default_model` (default: `gemma-4-31b-it`).
- **Multi-Tier Fallback**:
  1. Primary Provider (e.g., `gemini` or `openai`).
  2. If primary fails (e.g., rate limit, quota exhaustion, network issue), dynamically attempts fallback to `freellmapi` if registered and authenticated.
  3. If `freellmapi` also fails (or was primary and failed), safely falls back to `MockModelProvider`, ensuring zero crashes in autonomous research loops.

### C. Control Center & API Management (`src/server/app.py`)
- **GET `/api/config/llm`**: Exposes the real-time status of `freellmapi` alongside `gemini` and `openai` (configuration status, base URL, and active model).
- **POST `/api/config/llm`**: Allows updating `freellmapi_base_url`, `freellmapi_api_key`, `freellmapi_model`, and `default_provider`, automatically persisting changes to `.env`.

---

## 3. Configuration Reference

The following environment variables in `.env` govern FreeLLMAPI integration:

| Environment Variable | Default Value | Description |
|----------------------|---------------|-------------|
| `FREELLMAPI_BASE_URL` | `http://127.0.0.1:3001/v1` | FreeLLMAPI inference server base URL |
| `FREELLMAPI_API_KEY` | *(auto-discovered from freeapi.db)* | Unified API key for `/v1/*` inference endpoints |
| `FREELLMAPI_DEFAULT_MODEL` | `gemma-4-31b-it` | Default model identifier to route through FreeLLMAPI |
| `DEFAULT_LLM_PROVIDER` | `gemini` | System default provider (`gemini`, `openai`, `freellmapi`, `mock`) |

---

## 4. Running the FreeLLMAPI Service

FreeLLMAPI runs as a standalone daemon on port `3001`:

```bash
cd infrastructure/FreeLLMAPI
npm run dev
```

- **Inference API**: `http://127.0.0.1:3001/v1`
- **Web UI & Key Management**: `http://127.0.0.1:3001/`

---

## 5. Security Guardrails

1. **Local Loopback Communication**: FreeLLMAPI communicates locally over `127.0.0.1:3001` within the host system.
2. **Unified Key Protection**: The server encrypts downstream provider keys with AES-GCM and requires the unified API key for `/v1/*` inference endpoints.
3. **Zero Secrets in Repository**: No raw API keys or passwords are hardcoded or committed. All credentials are sourced securely from `.env` or encrypted database storage.
