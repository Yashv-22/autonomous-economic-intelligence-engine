"""
End-to-end multi-topic stress test for the Autonomous Economic Intelligence & Opportunity Engine.
Tests multiple diverse, random domain search inputs against all endpoints, parameters, and features:
1. Dynamic topic research loop execution (/api/research/run)
2. Dynamic SaaS opportunity synthesis & calibrated scoring (/api/opportunities?topic=...)
3. Dynamic Solution Architecture Blueprints (/api/solutions/{id}?topic=...)
4. Dynamic Adversarial Falsification Reports (/api/opportunities/{id}/validate?topic=...)
5. Epistemic Claim Ledger with Tier Filtering (/api/claims?grade=FACT/EVIDENCE)
6. Provenance Cryptographic Merkle Root & Span Hash Proofs (/api/provenance/audit, /api/provenance/verify)
7. Knowledge Graph Topology & Semantic Search (/api/graph/topology, /api/search/semantic)
8. Multi-Provider AI Gateway & Fallback Telemetry (/api/gateway/status)
"""

import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://127.0.0.1:8000"

RANDOM_TOPICS = [
    "Autonomous Multi-Agent Supply Chain Logistics and Bottlenecks",
    "Decentralized Liquidity Routing in Automated Market Makers",
    "Team AI Creativity Breakdown and Cross-Department Communication Friction",
    "Clinical Trial Patient Recruitment Agentic Automation and Protocol Optimization"
]

def request_json(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Accept": "application/json"}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_tests():
    print("=" * 70)
    print("[RUN] STARTING MULTI-TOPIC FULL PARAMETER STRESS TEST")
    print("=" * 70)
    
    # 1. Check Initial Status & Gateway Telemetry
    print("\n[STEP 1] Validating System Health & Multi-Provider AI Gateway...")
    status = request_json("/api/status")
    assert status["status"] == "HEALTHY", f"System not healthy: {status}"
    print(f"  [PASS] System status: HEALTHY (Total claims: {status['total_claims']}, Nodes: {status['graph_nodes']})")
    
    gw = request_json("/api/gateway/status")
    provider_names = [p["name"] for p in gw.get("providers", [])]
    print(f"  [PASS] Gateway Provider: {gw.get('active_provider')} (Available: {provider_names})")
    assert len(provider_names) >= 2

    # 2. Iterate through random domain topics
    for idx, topic in enumerate(RANDOM_TOPICS, 1):
        print(f"\n" + "-" * 70)
        print(f"[STEP 2.{idx}] Testing Search Input: '{topic}'")
        print("-" * 70)
        
        t0 = time.time()
        res = request_json("/api/research/run", method="POST", data={"topic": topic, "max_cycles": 1})
        elapsed = time.time() - t0
        
        assert res.get("status") in ["COMPLETED", "SUCCESS", "HEALTHY"], f"Research run failed: {res}"
        print(f"  [PASS] Research run executed in {elapsed:.2f}s (Status: {res.get('status')})")
        print(f"  [PASS] Spans acquired: {res.get('total_spans', 0)}, Claims: {res.get('total_claims', 0)}, Contradictions: {res.get('total_contradictions', 0)}")
        
        # 2a. Validate Dynamic Opportunities
        enc_topic = urllib.parse.quote(topic)
        opps_data = request_json(f"/api/opportunities?topic={enc_topic}")
        opps = opps_data.get("solution_opportunities") or opps_data.get("opportunities", [])
        assert len(opps) >= 3, f"Expected >= 3 opportunities, got {len(opps)}"
        top_opp = opps[0]
        print(f"  [PASS] Dynamic Opportunity #1: '{top_opp['solution_title']}' (Score: {top_opp['opportunity_score']})")
        assert top_opp['opportunity_score'] > 0
        assert "target_buyer_icp" in top_opp
        assert "monetization_model" in top_opp
        
        # 2b. Validate Dynamic Solution Blueprint
        opp_id = top_opp["opportunity_id"]
        bp = request_json(f"/api/solutions/{opp_id}?topic={enc_topic}")
        assert "technical_architecture" in bp or "concept" in bp
        print(f"  [PASS] Dynamic Solution Blueprint: Concept='{bp.get('concept', '')[:40]}...' | Architecture: {bp.get('technical_architecture', '')[:40]}...")
        
        # 2c. Validate Adversarial Falsification Stress Test
        val = request_json(f"/api/opportunities/{opp_id}/validate?topic={enc_topic}")
        assert val.get("opportunity_id") == opp_id
        assert "verdict" in val
        assert len(val.get("existing_competitors", [])) > 0 or "verdict_rationale" in val
        print(f"  [PASS] Adversarial Falsification: Verdict='{val.get('verdict')}' | Rationale: {val.get('verdict_rationale', '')[:50]}...")

    # 3. Test Epistemic Claims Ledger & Filtering
    print(f"\n[STEP 3] Validating Epistemic Claims Ledger & Tiers...")
    for grade in ["FACT", "EVIDENCE", "INFERENCE"]:
        claims_res = request_json(f"/api/claims?grade={grade}")
        count = claims_res.get("count") or claims_res.get("total", 0)
        print(f"  [PASS] Claims filtered by grade='{grade}': {count} records returned")
        assert count > 0, f"Expected claims for grade {grade}"

    # 4. Test Provenance Ledger & Cryptographic Proofs
    print(f"\n[STEP 4] Validating Provenance Ledger & Merkle Root...")
    audit = request_json("/api/provenance/audit")
    merkle_root = audit.get("merkle_root")
    events_count = audit.get("total_events", 0)
    print(f"  [PASS] Provenance Merkle Root: {merkle_root} (Audit events: {events_count})")
    assert merkle_root and len(merkle_root) == 64, "Invalid Merkle root SHA-256"

    # Verify cryptographic proof endpoint
    sample_text = "Autonomous AI operations require strict epistemic provenance verification."
    import hashlib
    sample_hash = hashlib.sha256(sample_text.encode("utf-8")).hexdigest()
    verify_res = request_json("/api/provenance/verify", method="POST", data={
        "text": sample_text,
        "span_hash": sample_hash
    })
    print(f"  [PASS] Cryptographic Hash Verification: Match={verify_res.get('match')} (Computed: {verify_res.get('computed_hash')[:16]}...)")
    assert verify_res.get("match") is True

    # 5. Test Knowledge Graph Topology & Semantic Vector Search
    print(f"\n[STEP 5] Validating Knowledge Graph & Semantic Vector Search...")
    graph = request_json("/api/graph")
    node_count = len(graph.get("nodes", []))
    edge_count = len(graph.get("edges", []))
    print(f"  [PASS] Knowledge Graph Topology: {node_count} nodes, {edge_count} edges")
    assert node_count > 0 and edge_count > 0

    search_res = request_json(f"/api/semantic/search?query=Autonomous+agent+coordination&top_k=5")
    matches = search_res.get("results", [])
    print(f"  [PASS] Semantic Vector Search: {len(matches)} relevant matches returned")
    assert len(matches) > 0

    # 6. Test Comprehensive Diagnostics (/api/test/all_parameters)
    print(f"\n[STEP 6] Running Internal Diagnostic Suite (/api/test/all_parameters)...")
    diag = request_json("/api/test/all_parameters")
    all_passed = diag.get("all_passed", False)
    print(f"  [PASS] Diagnostic Suite Result: All Passed = {all_passed}")
    for test in diag.get("checks", []):
        print(f"     - [{test.get('status')}] {test.get('param')}")
    assert all_passed is True

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL 6 PARAMETER TESTS PASSED WITH 100% SUCCESS ACROSS ALL TOPICS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
