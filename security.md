# Security Policy & Governance Controls

## Overview

The **Autonomous Economic Intelligence & Opportunity Engine** treats security as an architectural invariant, not an afterthought or prompt-level recommendation. Because autonomous multi-agent systems ingest untrusted third-party content from the public Internet, execute dynamic analytical workflows, and invoke model gateways, rigorous defense-in-depth isolation is strictly required.

---

## 1. Zero Secrets in Source Control

* **Strict Policy:** No production API keys, bearer tokens, passwords, TLS certificates, private keys, database connection strings, or session cookies are ever checked into source control.
* **Environment-Variable Based Credentials:** All sensitive runtime configurations must be supplied via local environment variables or loaded from a strictly ignored `.env` file at process launch.
* **Sanitized Templates:** Only `.env.example` is committed to Git, containing empty or generic placeholder values with detailed documentation for developers.
* **Git Pre-Commit Scanning:** Developers and CI systems run automated secret detection before any code is staged or merged.

---

## 2. Production Secret Management & Rotation

* **Secret Storage:** In production environments, credentials should be injected at runtime using dedicated secret managers (such as HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager, or Kubernetes Secrets).
* **Key Rotation:** 
  * LLM provider keys (OpenAI, Gemini, Groq, Anthropic) should be rotated every 90 days or immediately upon suspicion of exposure.
  * Internal JWT signing keys used by the identity broker must be rotated automatically on service startup or via scheduled key rotation pipelines.
* **Revocation Procedures:** If an active credential is leaked or suspected compromised:
  1. Revoke the key immediately in the provider dashboard.
  2. Issue a replacement key and update the secret store.
  3. Inspect logs and audit trails to ensure no unauthorized inference or data extraction occurred.

---

## 3. Untrusted Internet Content & Prompt-Injection Protections

> [!CAUTION]
> **Fundamental Security Principle:** All content retrieved from the Internet (including web scrapes, search results, RSS feeds, PDFs, DOCXs, and third-party APIs) is **untrusted external data**. It must NEVER be treated as system instructions, authorization overrides, or trusted execution context.

### Mitigations:
1. **Instruction / Data Separation:** External scraped content is parsed, stripped of active markup/scripts, and wrapped in strict data delimiters before being presented to analysis agents.
2. **Schema Enforcement:** Extraction outputs must strictly conform to strongly typed Pydantic models. Any model output attempting to return arbitrary commands or altered agent roles is rejected.
3. **Out-of-Process Policy Gate (OPA):** Crucial agent actions (database writes, opportunity promotions, network calls) must pass an out-of-process Open Policy Agent (OPA) validation check. Foundation models cannot override or disable policy plane rules.

---

## 4. Server-Side Request Forgery (SSRF) & Outbound Network Controls

1. **IP Range Restrictions:** Ingestion and scraper modules prohibit requests targeting loopback addresses (`127.0.0.1`, `localhost`), internal private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), or cloud instance metadata endpoints (`169.254.169.254`).
2. **Domain Allowlisting:** Research tasks can be configured to restrict outbound crawling to verified scientific, financial, or academic domains (e.g., `arxiv.org`, `sec.gov`).
3. **Dedicated Egress Proxy:** When deployed in containerized production, worker agents route outbound network traffic through an egress proxy enforcing TLS inspection and protocol limits.

---

## 5. Authentication Boundaries & Ephemeral Non-Human IAM

* **Ephemeral Identity Broker:** When subtasks require access to backend databases or ledger APIs, short-lived, cryptographically signed JWT tokens with strict TTLs (60–120 seconds) are issued.
* **No Shared Master Keys:** Individual researcher agents do not possess ambient administrative authority or long-lived database write access.
* **Cryptographic Provenance:** Every claim and opportunity in the knowledge ledger is anchored by SHA-256 content hashes, associating every finding with its exact immutable source paragraph.

---

## 6. Public Deployment & Production Hardening

* **Bind Addresses:** Development defaults bind to `127.0.0.1`. For production deployments, bind to container network interfaces behind a hardened reverse proxy (e.g., NGINX, Cloudflare, or Envoy) terminating TLS.
* **CORS Policies:** Restrict cross-origin resource sharing (`CORS`) to verified hostnames; do not allow wildcard (`*`) origins with credentialed access.
* **Rate Limiting:** Protect public ingestion and query endpoints using token-bucket rate limiters to prevent resource exhaustion and DoS attacks.

---

## 7. Logging & Sensitive Data Handling

* **Redaction:** Logs must never output raw API keys, bearer headers, or user authentication payloads.
* **Minimal Logging:** Scraped documents containing potential PII (Personally Identifiable Information) are sanitized prior to persistent indexing.
* **Audit Trail Integrity:** System mutations are tracked in an append-only audit log with reverse-delta rollback capability to support rapid recovery from anomalous agent outputs.

---

## 8. Third-Party Infrastructure Isolation

The engine integrates with external services and local daemons including:
* **OmniRoute** (Multi-provider model proxy)
* **FreeLLMAPI** (Local inference router)
* **Agent Reach** (Multi-channel search & scraping runtime)

### Boundaries:
* These daemons run in isolated processes or micro-containers.
* Their administrative endpoints and internal configurations must never be exposed directly to public networks.
* Credentials and session cookies required by third-party local daemons must reside in ignored local configuration files and never cross into core repository commits.

---

## 9. Reporting Security Vulnerabilities

If you discover a potential security vulnerability within this project, please report it responsibly:
* **Contact:** Open a private security advisory on GitHub or email the repository maintainers.
* **Response Timeline:** We acknowledge vulnerability reports within 48 hours and strive to release a patch or mitigation within 7 days.
