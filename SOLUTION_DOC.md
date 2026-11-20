# NyayaSathi (न्यायसाथी) — AI Legal Helper for Ordinary People in India
**Kuku AI Generalist Assignment — Problem 2 Solution Document**  
*Submission Details: Name: [YOUR NAME] | Roll No: [YOUR ROLL NO] | Branch: [YOUR BRANCH] | Prototype Link: [INSERT PROTOTYPE LINK HERE] | GitHub: https://github.com/pramodsharma7851-collab/AI_LAWYER_Nyaysathi_kuku*

---

### 1. Problem Choice & Framing
**Why This Problem?** Over 80% of ordinary Indians abandon legitimate civil grievances (withheld rental deposits, denied consumer refunds, unpaid salaries) because hiring an advocate costs ₹15,000–₹50,000 upfront, procedures are opaque, and formal notices are intimidating. Ordinary people don't need a theoretical constitutional jurist; they need actionable self-help: turning an emotional story into clear facts, knowing where they stand under Indian law, drafting legally grounded notices, and rehearsing arguments before confronting the opposing party.

**Deliberate Scoping (The 3 Critical Everyday Domains):**  
In adherence to the brief's guidance (*"does not need to know all of Indian law; pick what matters most"*), NyayaSathi is strictly bounded to three civil domains:
1. **Tenancy:** Residential security deposit recovery, arbitrary deductions, illegal lockout, notice periods (*Transfer of Property Act 1882, Model Tenancy Act 2021*).
2. **Consumer Protection:** Defective products, refused refunds, service deficiency, dark patterns, e-Daakhil filing (*Consumer Protection Act 2019*).
3. **Employment:** Unpaid/withheld salaries, abrupt termination without notice, full & final (FNF) dues (*Payment of Wages Act 1936, Industrial Disputes Act 1947, Indian Contract Act 1872*).

**Core Assumptions Where the Brief Was Silent:**
- **Zero Criminal / Matrimonial Jurisdiction:** Criminal defense, domestic violence, divorce, and property titles are strictly out of scope. Immediate threats route to National Emergency `112` or Women Helpline `181`.
- **Criminal Reform Cutoff:** The Indian Penal Code (IPC 1860) was repealed on July 1, 2024 by the Bharatiya Nyaya Sanhita (BNS 2023). Citing IPC as current law is strictly barred.
- **State Tenancy Divergence:** Rental laws are state subjects; the Model Tenancy Act 2021 is treated as model guidance while prompting the citizen for state/city context.

---

### 2. Approach, Scale & Division of Labor (AI vs. Deterministic Code)

| Task Domain | Handled By | Why This Split? |
| :--- | :--- | :--- |
| **Conversational Intake & Voice** | **Gemini 3.5 Flash Lite** | Empathetic multi-lingual understanding across English, Hindi, and Hinglish. |
| **Domain Scope Gate** | **Pre-LLM Gate (`core/scope.py`)** | Out-of-scope queries return *"I do not know."* before invoking the LLM. Zero data/prompt leakage. |
| **Statutory Retrieval (RAG)** | **Deterministic BM25 (`core/corpus.py`)** | Models hallucinate statutes; deterministic lexical search grounds citations in a verified statutory corpus. |
| **Legal Citation Hard Gate** | **Regex & Corpus Verifier (`core/verifier.py`)** | Code rejects ungrounded Section/Article/Case Law patterns. If invalid twice, falls back to DLSA helpline. |
| **Document Drafting** | **Pydantic + python-docx / ReportLab** | AI drafts prose; code enforces `[TO BE FILLED]` placeholders for missing facts. Zero hallucinated claims. |
| **Session Persistence** | **SQLAlchemy + SQLite/Postgres** | Full turn ordering (user saved first) and URL query param (`?session_id=...`) refresh survival. |

**Human-in-the-Loop Architecture:**  
AI never files a case autonomously. Citizens review an interactive, editable **Live Fact Sheet** sidebar where human edits override AI extractions. For document generation, citizens download reviewable `.docx` and `.pdf` drafts with prominent disclaimers advising review by an advocate or District Legal Services Authority (DLSA / NALSA Helpline `15100`).

---

### 3. Quality Checking, Real Evaluation & Anti-Hallucination Controls
NyayaSathi enforces a **5-Pillar Defense-in-Depth Anti-Hallucination Architecture**:
1. **Curated Ground-Truth Corpus (`/corpus`):** 4 curated JSON statutory files verified against official India Code texts.
2. **Pre-LLM Scope Gate & Safety Firewall:** Fast classification intercepts non-scoped topics before LLM execution.
3. **Retrieval-Grounded Authority Injection:** Top matching statutory sections are injected into a strict `AUTHORITY` prompt block.
4. **Deterministic Citation Verifier (Hard Gate):** Every citation's unique `corpus_id` is validated against the retrieved authority set. Free text is scanned with regex for unauthorized `Section \d+`, `Article \d+`, or fake Supreme Court citations (`v.`, `AIR`, `SCC`).
5. **Lawyer Escalation Thresholds:** Automatic referral when claims exceed ₹50 Lakhs (pecuniary commission jurisdiction) or involve eviction warrants.

**Quantitative Test Suite Results (100% Pass Across 85 Tests):**
- **Unit & Integration Suite (`pytest`):** 81 offline tests + 4 live Gemini API smoke tests passing (`tests/`).
- **Scope Gate Evaluation (`evals/run_scope_evals.py`):** 33 test cases evaluated.
  - *Out-of-Scope Rejection Rate:* **100% (24/24)** rejected with exact localized string *"I do not know."* (adversarial jailbreaks, criminal law, divorce, cricket, coding, recipes).
  - *In-Scope Acceptance Rate:* **100% (9/9)** correctly accepted across tenancy, consumer, and employment.
  - *False Rejections / Leaks:* **0**.
- **Adversarial & Injection Testing (`evals/test_cases.py`):** 10 adversarial attacks (repealed IPC prompt injection, system prompt extraction, fake case law requests) captured in `evals/outputs/`. The model and verifier achieved **0 hallucinated citations** and **0 secret leaks**.

---

### 4. Honest Failure Modes & Explicit Boundaries
1. **Borderline / Ambiguous Civil-Criminal Overlaps:** If a landlord locks out a tenant and allegedly steals belongings, the civil deposit recovery is in-scope, but the theft allegation is criminal. The system isolates the in-scope tenancy portion and provides notice guidance while refusing criminal prosecution advice.
2. **State Rent Control Fragmentation:** If a tenant is in Mumbai governed by the *Maharashtra Rent Control Act 1999*, the MTA 2021 corpus principles provide structured negotiation guidance but cannot replace state-specific Competent Authority eviction filings.
3. **Token Budget Summarization:** Conversations exceeding 12,000 characters (~3,000 tokens) compress older turns into rolling summaries. While key amounts and parties are preserved in structured JSON, verbatim conversational nuance from early turns is summarized.
4. **Voice Transcription Hardware Reliance:** Streamlit web audio relies on local browser WebRTC permissions. Under low-quality microphone input or severe background noise, citizens are guided to review the generated transcript before submitting.

---

### 5. Unit Economics & Production Scale

| Metric | Measurement / Cost |
| :--- | :--- |
| **Model Selection** | `gemini-3.5-flash-lite` (Official `google-genai` SDK) |
| **Input / Output Token Pricing** | \$0.075 / million input tokens; \$0.30 / million output tokens |
| **Average Turn Cost** | ~1,200 tokens (System prompt + Case JSON + Authority + Query) $\approx$ **₹0.012 per turn** |
| **Average Full Case Consultation** | 4–6 turns (Intake + Fact Extraction + Advice + Notice Draft) $\approx$ **₹0.06 to ₹0.08 per citizen** |
| **Scale to 100,000 Active Citizens** | Compute & LLM cost is under **₹8,000 ($100 USD)** total per month. |
| **Database Scalability** | SQLAlchemy ORM abstracts SQLite locally to hosted PostgreSQL with zero code changes. |
| **Stateless Deployment** | Document generation (PDF/DOCX) occurs in-memory; zero persistent storage bottleneck. |

*Artifacts & Evidence: All raw unedited evaluation outputs are available in `evals/outputs/` and full evaluation reports in `evals/scope_eval_report.txt` and `evals/report.txt`.*
