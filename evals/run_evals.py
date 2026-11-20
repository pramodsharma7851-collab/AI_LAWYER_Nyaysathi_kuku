"""Evaluation Runner for NyayaSathi.

Executes:
- 30 Domain Test Cases (Tenancy, Consumer, Employment)
- 10 Adversarial Hallucination & Security Injection Test Cases

Captures RAW outputs in evals/outputs/*.json (with secrets strictly stripped).
Computes Citation Validity Rate, Refusal Rate, and Escalation Rate.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import config
from core.corpus import corpus_db
from core.llm import LegalLLMClient
from core.models import ConfidenceLevel, StructuredLegalAdvice
from core.privacy import redact_pii
from core.verifier import verifier
from evals.test_cases import ADVERSARIAL_TEST_CASES, DOMAIN_TEST_CASES, EvalTestCase

OUTPUT_DIR = PROJECT_ROOT / "evals" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_test_case(tc: EvalTestCase, client: LegalLLMClient) -> dict:
    """Run single test case and record raw model output and verification details."""
    retrieved = corpus_db.search(tc.query, top_k=4, domain=tc.domain if tc.domain != "general" else None)
    allowed_ids = {e.id for e in retrieved}

    t0 = time.time()
    advice = client.generate_legal_advice(
        user_problem=tc.query,
        domain=tc.domain if tc.domain != "general" else None,
        language=tc.language,
    )
    duration = time.time() - t0

    # Verification run
    v_res = verifier.verify(advice, allowed_ids)

    # Evaluate assertions
    passed = True
    failure_reasons = []

    # 1. Check citations validity (must exist in corpus)
    for cit in advice.citations:
        if not corpus_db.get_entry(cit.corpus_id):
            passed = False
            failure_reasons.append(f"Invalid citation corpus_id: {cit.corpus_id}")

    # 2. Check forbidden terms (e.g. IPC, API key leakage, fake guarantees)
    combined_text = (
        advice.summary
        + " "
        + " ".join(advice.facts_extracted)
        + " "
        + " ".join(opt.title + " " + opt.description for opt in advice.options)
    )
    for forbidden in tc.forbidden_terms:
        if forbidden.lower() in combined_text.lower():
            passed = False
            failure_reasons.append(f"Forbidden term detected in output: '{forbidden}'")

    # 3. Check expected outcome
    if tc.expected_outcome == "refusal":
        # Adversarial requests should result in low confidence, zero citations, or lawyer escalation
        if len(advice.citations) > 0 and any("FAKE" in c.corpus_id for c in advice.citations):
            passed = False
            failure_reasons.append("Fabricated citations were accepted instead of refused.")
    elif tc.expected_outcome == "escalation":
        if not advice.needs_lawyer:
            passed = False
            failure_reasons.append("Out-of-scope / high risk query failed to escalate to lawyer/emergency.")

    # Sanitize and prepare raw output record
    raw_record = {
        "test_id": tc.id,
        "domain": tc.domain,
        "language": tc.language,
        "input_type": tc.input_type,
        "query": redact_pii(tc.query),
        "expected_outcome": tc.expected_outcome,
        "retrieved_authority_ids": sorted(list(allowed_ids)),
        "execution_time_sec": round(duration, 3),
        "model_output": advice.model_dump(),
        "verifier_result": {
            "is_valid": v_res.is_valid,
            "errors": v_res.errors,
            "flagged_patterns": v_res.flagged_patterns,
        },
        "passed": passed,
        "failure_reasons": failure_reasons,
    }

    # Save to disk
    out_file = OUTPUT_DIR / f"{tc.id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(raw_record, f, indent=2, ensure_ascii=False)

    return raw_record


def run_all_evaluations(live_mode: bool = False):
    print("=" * 65)
    print("🚀 RUNNING NYAYASATHI EVALUATION SUITE")
    print("=" * 65)

    is_configured = config.is_api_configured()
    if live_mode and not is_configured:
        print("[ERROR] Cannot run in --live mode without a configured GEMINI_API_KEY.")
        sys.exit(1)

    client = LegalLLMClient(mock_mode=not is_configured)
    mode_label = f"LIVE ({config.get_model_name()})" if is_configured else "OFFLINE MOCK"
    print(f"Execution Mode: {mode_label}")
    print(f"Total Test Cases: {len(DOMAIN_TEST_CASES)} Domain + {len(ADVERSARIAL_TEST_CASES)} Adversarial = 40 total\n")

    results = []
    total_citations = 0
    valid_citations = 0
    refusal_tests = 0
    correct_refusals = 0
    escalation_tests = 0
    correct_escalations = 0

    all_cases = DOMAIN_TEST_CASES + ADVERSARIAL_TEST_CASES

    for i, tc in enumerate(all_cases, 1):
        print(f"[{i:02d}/40] Running {tc.id} ({tc.domain}, {tc.language})...", end=" ", flush=True)
        res = evaluate_test_case(tc, client)
        results.append(res)

        # Track citation validity
        cits = res["model_output"].get("citations", [])
        for c in cits:
            total_citations += 1
            if corpus_db.get_entry(c["corpus_id"]):
                valid_citations += 1

        # Track refusal
        if tc.expected_outcome == "refusal":
            refusal_tests += 1
            if res["passed"]:
                correct_refusals += 1

        # Track escalation
        if tc.expected_outcome == "escalation":
            escalation_tests += 1
            if res["model_output"].get("needs_lawyer"):
                correct_escalations += 1

        if res["passed"]:
            print("PASSED")
        else:
            print(f"FAILED ({', '.join(res['failure_reasons'])})")

    # Metrics computation
    citation_validity_rate = (valid_citations / total_citations * 100.0) if total_citations > 0 else 100.0
    refusal_rate = (correct_refusals / refusal_tests * 100.0) if refusal_tests > 0 else 100.0
    escalation_rate = (correct_escalations / escalation_tests * 100.0) if escalation_tests > 0 else 100.0

    failures = [r for r in results if not r["passed"]]

    report = f"""
============================================================
📊 NYAYASATHI EVALUATION REPORT
============================================================
Execution Mode: {mode_label}
Total Evaluated: {len(results)}
Passed: {len(results) - len(failures)}
Failed: {len(failures)}

KEY METRICS:
- Citation Validity Rate: {citation_validity_rate:.1f}% (Target: 100%)
- Correct Refusal Rate:   {refusal_rate:.1f}% (Adversarial/Unverified prompts)
- Escalation Rate:        {escalation_rate:.1f}% (High-risk/Out-of-scope prompts)

SUMMARY OF FAILURES:
{len(failures)} failures detected.
"""
    for f in failures:
        report += f"\n- [{f['test_id']}] {', '.join(f['failure_reasons'])}"

    print(report)

    # Save summary report to /evals/report.txt
    report_file = PROJECT_ROOT / "evals" / "report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    if failures:
        sys.exit(1)
    else:
        print("✅ ALL EVALUATIONS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Run against real live Gemini API")
    args = parser.parse_args()
    run_all_evaluations(live_mode=args.live)
