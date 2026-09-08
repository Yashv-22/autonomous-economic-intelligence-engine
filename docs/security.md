# Security Architecture & Threat Mitigation

## 1. Core Principles

The security model of the **Autonomous Economic Intelligence & Opportunity Engine** is grounded in defense-in-depth:
1. **Zero Ambient Trust:** Agents operate with zero persistent credentials and ephemeral subtask identity.
2. **Untrusted External Data:** Ingested web data is untrusted input and isolated from instruction streams.
3. **Out-of-Process Policy Governance:** OPA Rego policies evaluate all persistent writes and external calls.
4. **Cryptographic Auditing:** Append-only transaction logging with reverse-delta rollbacks.

For full vulnerability reporting policies and operational secret handling, see [SECURITY.md](../SECURITY.md).

---

## 2. Threat Model Matrix (STRIDE)

| Threat Category | Attack Vector | Architectural Mitigation |
| :--- | :--- | :--- |
| **Spoofing** | Rogue agent imposter injecting fraudulent claims into the ledger. | Cryptographic task tokens & ephemeral JWT identity broker. |
| **Tampering** | Prompt-injection payload in scraped HTML attempting to alter system prompt. | Strict Pydantic JSON extraction boundaries & HTML tag stripping. |
| **Repudiation** | Untraceable database mutations or opportunity promotions. | Append-only SHA-256 audit ledger with actor attribution. |
| **Information Disclosure** | API keys or user credentials leaked in logs or error traces. | Automated log sanitization, `.env` exclusion, and zero-secrets Git policy. |
| **Denial of Service** | Recursive research loops exhausting LLM tokens or API budgets. | Hard recursion depth limits, cost circuit breakers, and rate limiters. |
| **Elevation of Privilege** | Sandbox escape or agent modifying governance rules. | Read-only container rootfs, unprivileged user execution, out-of-process OPA. |

---

## 3. Sandboxing & Runtime Controls

When deployed in multi-agent autonomous mode:
* Research scrapers run in isolated containers with limited egress.
* Code synthesis and evaluation workers operate with `--net=none` (zero network connectivity).
* File writes are restricted to ephemeral `/tmp/workspace` mounts that are discarded after execution.

---

## 4. Policy-as-Code (OPA) Enforcement

All sensitive agent operations are subject to Rego policy rules:
```rego
package enterprise.agent.governance

default allow_action = false

# Allow read-only research tools for certified research agents
allow_action {
    input.agent_role in ["AGENT-RSCH-002", "AGENT-RSCH-003"]
    input.tool_type == "READ_ONLY"
}

# Allow opportunity creation within budget limits
allow_action {
    input.agent_role == "AGENT-ARCH-010"
    input.estimated_cost_usd <= 250
    input.schema_validation_passed == true
}
```
If an agent attempts an action not authorized by the policy plane, the call is rejected immediately with a policy denial audit event.
