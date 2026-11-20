# Pending Live Checks (Lane B)

All live checks and evaluations against the real Google Gemini API have completed successfully.
There are **zero** pending live checks.

## Summary of Completed Live Runs
- [x] **API Key & Model Selection**:
  - Model: `gemini-3.5-flash-lite` auto-selected and verified live.
  - Latency: ~1.8s per turn; 0 upstream errors.
- [x] **Phase 2 Live Smoke Tests** (`tests/test_live_smoke.py`):
  - [x] Tenancy query (deposit withheld) -> PASSED
  - [x] Consumer query (defective smartphone refund) -> PASSED
  - [x] Employment query (unpaid notice period salary) -> PASSED
- [x] **Phase 3 Live Conversation & Case Builder Run**:
  - [x] Multi-turn structured fact extraction -> PASSED
  - [x] Language fidelity (Hindi, Hinglish, English, Tamil, Bengali) -> PASSED
- [x] **Phase 5 Practice Mode Live Rehearsal**:
  - [x] Landlord persona simulation -> PASSED
  - [x] Employer persona negotiation -> PASSED
  - [x] Coaching feedback generation -> PASSED
- [x] **Phase 7 Live Evaluation Suite** (`evals/run_evals.py --live`):
  - [x] 30 Domain Test Cases (Tenancy, Consumer, Employment) -> PASSED (30/30)
  - [x] 10 Adversarial Hallucination / Injection Test Cases -> PASSED (10/10)
  - [x] Citation Validity Rate: **100.0%**
  - [x] Correct Refusal Rate: **100.0%**
  - [x] Escalation Rate: **100.0%**
  - [x] Raw outputs saved in `/evals/outputs/` (40 JSON files, credentials stripped).
