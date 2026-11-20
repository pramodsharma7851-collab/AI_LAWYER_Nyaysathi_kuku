<<<<<<< HEAD
# ⚖️ NyayaSathi (न्यायसाथी)
### Production-Ready AI Legal Helper for Ordinary People in India

NyayaSathi is a conversational, retrieval-grounded AI legal assistant built specifically for everyday citizens in India. It empowers ordinary people to navigate common legal disputes—such as security deposits landlords refuse to return, denied consumer refunds, or withheld employment salaries—in their own language without expensive lawyer fees or intimidating legalese.

---

## 🌟 Key Features

1. **Empathetic Conversational Intake (Text & Voice)**:
   - Available in **English, Hindi (हिन्दी), Hinglish, Marathi (मराठी), Tamil (தமிழ்), and Bengali (বাংলা)**.
   - Built-in microphone audio recording (`st.audio_input`) with multi-modal transcription via Gemini.
   - Citizens review and edit the transcript before submitting.

2. **Iterative Case Builder & Live Fact Sheet**:
   - Converts messy, emotional stories into structured case records: parties, key dates, disputed amounts, agreements, held vs missing evidence.
   - Asks at most 2-3 friendly questions at a time.
   - Includes a live, editable sidebar/fact sheet where user edits become the confirmed facts.

3. **Grounded Legal Standing & Options**:
   - Explains citizen rights and actionable paths forward at a 6th–8th grade reading level.
   - Strict citation to source-of-truth statutory provisions with verified India Code URLs.

4. **Strict 3-Topic Scope Gate & Domain Firewall**:
   - Strictly restricted to three actionable everyday civil disputes:
     1. 🏠 **Tenancy** (security deposits, illegal eviction, rent disputes)
     2. 🛒 **Consumer Disputes** (e-commerce refunds, defective products, service deficiency)
     3. 💼 **Employment** (unpaid/withheld salaries, wrongful termination, full & final dues)
   - Pre-LLM gate (`core/scope.py`) intercepts queries *before* model invocation. Non-scoped topics (criminal, family, divorce, property title, traffic, taxation) deterministically receive exactly:
     > *"I do not know."* (or Hindi *"मुझे नहीं पता।"*)
   - Zero model hallucination, zero credential/prompt leakage, and no wasted token budget.
   - Immediate life-safety routing: Immediate physical threats, violence, or domestic abuse route to Emergency `112` or Women Helpline `181`.

5. **Robust Database Persistence & Context Windowing**:
   - **Postgres-Ready SQLAlchemy Storage**: Normalized tables for `sessions`, `messages`, `case_files`, and `summaries`.
   - **Page Refresh Continuity**: Session ID is mirrored in URL query parameters (`?session_id=<uuid>`), ensuring conversation and fact sheet persist across page reloads.
   - **Strict Turn Ordering**: User messages are committed to the DB *first*, the model is invoked, and the assistant reply is committed. Even if generation fails, the user message is never lost.
   - **Rolling Context Builder (`core/context.py`)**: Assembles system prompt, confirmed case JSON, rolling historical summary, verbatim recent N turns, and grounded `AUTHORITY` blocks within a character/token budget.
   - **Privacy & Export**: One-click "Delete my data" cascade wipe and "Download chat transcript (.txt)" button.

6. **Self-Help Document Drafter (PDF & DOCX)**:
   - Drafts formal **Legal Demand Notices** and **Consumer Complaints** (Section 35, CPA 2019 for e-Daakhil).
   - **Zero Hallucinated Facts**: Placeholders are filled strictly from user-confirmed facts; any missing details remain as `[TO BE FILLED]`.
   - Generates in-memory `.docx` (Word) and `.pdf` (ReportLab) files with download buttons and mandatory legal disclaimers.

7. **Practice Mode (Opponent Rehearsal & Negotiation Coaching)**:
   - Rehearse arguments against realistic opposing party personas:
     - 🏠 *Unreasonable Landlord* (repainting charges, deep cleaning, deposit forfeiture)
     - 🛒 *Evasive E-commerce Manager* (return window expired, physical damage excuses)
     - 💼 *Defensive Employer / HR* (client billing delays, notice shortage deductions)
   - Real-time coaching feedback evaluates argument tone, highlights pitfalls, and provides a concrete evidence preparation checklist.

8. **Find Free Legal Help Directory**:
   - Curated directory of verified official government portals and helplines:
     - **NALSA / DLSA Free Legal Aid Helpline**: `15100` (Toll-Free, 24/7)
     - **National Consumer Helpline**: `1915` & **e-Daakhil**: `edaakhil.nic.in`
     - **Ministry of Labour SAMADHAN Portal**: `samadhan.labour.gov.in`
     - **National Emergency**: `112` | **Women Helpline**: `181`

---

## 🛡️ Non-Negotiable Anti-Hallucination Architecture

NyayaSathi never relies on prompt instructions alone. Code enforces strict legal boundaries:
- **Curated Corpus (`/corpus`)**: Statutory provisions from the *Consumer Protection Act 2019*, *Transfer of Property Act 1882*, *Model Tenancy Act 2021*, *Payment of Wages Act 1936*, *Industrial Disputes Act 1947*, *Indian Contract Act 1872*, and *Legal Services Authorities Act 1987*.
- **Repealed Laws Barred**: The Indian Penal Code (IPC 1860) was repealed on July 1, 2024 by the Bharatiya Nyaya Sanhita (BNS 2023). Citing IPC as current law is strictly rejected.
- **BM25 Lexical Retrieval**: Passes only the top matching statutory provisions to the model in an `AUTHORITY` block.
- **Deterministic Citation Verifier (Hard Gate)**: Every cited section must exist in the corpus AND have been retrieved in the authority block. Regex scanners reject ungrounded `Section \d+` or case law claims.
- **Safe Fallback**: Any output failing verification twice is replaced with a safe fallback directing the citizen to DLSA / NALSA.

See [HALLUCINATION_CONTROLS.md](HALLUCINATION_CONTROLS.md) for detailed architecture and live test outputs.

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.11+ installed.
- (Docker is **not** required).

### 2. Setup Virtual Environment
```bash
# Clone or navigate to the repository
cd nyayasathi

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

### 3. Configure Gemini API Key
The project uses the non-blocking API key protocol.
1. Open the `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=auto
   ```
2. Or set it interactively without revealing it on screen:
   ```bash
   python scripts/set_key.py
   # or: make set-key
   ```
3. Run the environment checker:
   ```bash
   python scripts/check_env.py
   # or: make check-env
   ```
   *The system automatically detects available models, tests live connectivity, and pins `gemini-3.5-flash-lite`.*

### 4. Run the Application
```bash
streamlit run app.py
# or: make run
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Testing and Live Evaluations

### Full Test Suite (100% Offline Passing: 85 Tests)
```bash
pytest tests/ -v
# or: make test
```
*Executes all 85 unit and integration tests across database persistence, context builder, scope gate, BM25 retrieval, citation verifier, document drafter, and Streamlit AppTest UI.*

### Scope Gate Boundary Evaluation
```bash
python evals/run_scope_evals.py
```
*Evaluates the pre-LLM scope gate across 33 test cases (adversarial jailbreaks, criminal law, divorce, property titles, multi-turn follow-ups, and mixed messages). Current results: **100% In-Scope Acceptance (9/9), 100% Out-of-Scope Rejection (24/24), 0 False Rejections, 0 Failures**.*

### Live Legal Evaluation Suite (Real Gemini Model)
```bash
python evals/run_evals.py --live
# or: make live
```
*Executes 40 comprehensive domain evaluation tests. Raw outputs are captured in `evals/outputs/*.json` with credentials stripped.*

---

## 🌐 Production Deployment Guide

### Option 1: Streamlit Community Cloud (Recommended for MVP)
1. Push the repository to a private or public GitHub repository (ensure `.env` is gitignored).
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app pointing to `app.py`.
3. In App Settings -> **Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key_here"
   GEMINI_MODEL = "auto"
   ```
4. Deploy! The app reads Streamlit secrets dynamically and works out of the box.

### Option 2: Linux VPS (Ubuntu / Debian with systemd & Nginx)
*(Marked as standard configuration; test locally before production)*
1. Clone repo onto VPS and set up virtual environment.
2. Create systemd service `/etc/systemd/system/nyayasathi.service`:
   ```ini
   [Unit]
   Description=NyayaSathi Streamlit App
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/nyayasathi
   ExecStart=/var/www/nyayasathi/venv/bin/streamlit run app.py --server.port 8501 --server.headless true
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Configure Nginx reverse proxy with WebSocket support on port 80/443 pointing to `http://localhost:8501`.

---

## 📂 Project Structure

```
├── app.py                      # Main Streamlit web application
├── core/                       # Decoupled core backend (no Streamlit dependencies)
│   ├── case_builder.py         # Multi-turn fact extraction and guided questioning
│   ├── config.py               # Pydantic configuration loader
│   ├── context.py              # Context builder with rolling summaries & authority
│   ├── corpus.py               # Corpus loader and BM25 retriever
│   ├── database.py             # SQLite/Postgres SQLAlchemy session persistence
│   ├── drafter.py              # Notice and complaint drafter (PDF & DOCX)
│   ├── llm.py                  # Google-genai client wrapper with rate limiting
│   ├── models.py               # Pydantic schemas (hard gate I/O)
│   ├── privacy.py              # PII redaction (Aadhaar, phone, email)
│   ├── practice.py             # Practice mode opponent personas and coach
│   ├── scope.py                # Pre-LLM 3-topic scope gate & safety firewall
│   ├── verifier.py             # Hard gate citation verifier & regex scanner
│   └── voice.py                # Audio transcription adapter
├── corpus/                     # Source-of-truth statutory provisions
│   ├── consumer.json           # Consumer Protection Act, 2019
│   ├── tenancy.json            # TPA 1882 & Model Tenancy Act 2021
│   ├── employment.json         # Payment of Wages 1936 & IDA 1947
│   └── general.json            # Contract Act 1872 & Legal Services Authorities Act
├── pages/                      # Multi-page Streamlit application
│   ├── 1_📄_Document_Drafter.py
│   ├── 2_🎭_Practice_Mode.py
│   └── 3_🏛️_Find_Free_Legal_Help.py
├── tests/                      # Pytest unit and integration test suite
├── evals/                      # 40-case evaluation suite and raw outputs
├── scripts/                    # check_env.py, set_key.py, security_check.py
├── DEMO_SCRIPT.md              # 3-minute walkthrough demo script
├── HALLUCINATION_CONTROLS.md   # Architectural explanation of anti-hallucination
├── CORPUS_SOURCES.md           # Statutory sources and verification dates
├── ASSUMPTIONS.md              # Architectural decisions and model selection
├── LIMITATIONS.md              # Scope boundaries and known limitations
└── Makefile                    # make check-env, run, test, live
```
=======
# AI_LAWYER_Nyaysathi_kuku
>>>>>>> 573966de19dfc16b1928212fdaf764adfb1aff2e
