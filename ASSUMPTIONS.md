# System Assumptions and Design Decisions

This document records key architectural assumptions, scope definitions, and choices made during the development of NyayaSathi.

## 1. Legal Domain Scope
- **Tenancy**: Covers residential security deposit recovery, notice periods, and wrongful eviction. Because tenancy is governed by state-specific rent control acts (e.g., Delhi Rent Control Act, Maharashtra Rent Control Act) while the Model Tenancy Act 2021 serves as a non-binding model for states, the system explicitly asks the user for their state/city and notes state law variations.
- **Consumer Protection**: Governed uniformly under the Consumer Protection Act, 2019 (CPA 2019), including district/state/national commission pecuniary jurisdiction, e-Daakhil filing, and 2-year limitation period (Section 69).
- **Employment**: Focuses on private sector wage disputes, salary withholding, and termination without notice. Because the Code on Wages 2019 and Industrial Relations Code 2020 were passed by Parliament but their implementation rules across all states have not fully replaced legacy statutes, the corpus grounds citations in currently operative provisions (e.g., Payment of Wages Act 1936, Industrial Disputes Act 1947, Indian Contract Act 1872) while highlighting transitional legal provisions.
- **Criminal & Emergencies**: Strictly out of scope. Criminal defense, domestic violence, or immediate physical threats trigger safe handoffs to 112 (National Emergency), 181 (Women Helpline), or 15100 (NALSA free legal aid).

## 2. LLM and SDK Architecture
- **SDK**: Official `google-genai` SDK (`from google import genai`).
- **Model Selection**: When `GEMINI_MODEL=auto`, `check_env.py` queried available models via `client.models.list()`. Legacy models (`gemini-2.5-flash` and `gemini-2.5-flash-lite`) reported deprecated 404 endpoints directing users to Gemini 3 series. While `gemini-3.8-flash` had upstream temporary high-demand (503 spikes), `gemini-3.5-flash-lite` successfully passed live execution with low latency (~2s), excellent multi-lingual comprehension (Hindi/Hinglish/regional languages), and reliable JSON structured schema compliance. It was therefore chosen as the primary production model and written into `.env`.
- **Pydantic Hard Gate**: All LLM generation adheres to a strict Pydantic schema. Answers containing citations not found in the verified retrieved corpus are rejected and sanitized by deterministic code.

## 3. Storage, Database Architecture, and Multi-Turn Context
- **Database Engine**: SQLAlchemy ORM with default SQLite storage (`data/nyayasathi.db`), designed for zero-code migration to PostgreSQL (`DATABASE_URL=postgresql://...`).
- **Normalized Schema**:
  - `sessions`: Tracks `id` (UUID), `created_at`, `last_active_at`, `language`, and `case_type`.
  - `messages`: Records every turn (`session_id`, `role`, `content`, `language`, `in_scope`, `created_at`). Strict transactional write order ensures user messages are persisted prior to LLM calls.
  - `case_files`: Stores extracted case fact JSON (`parties`, `timeline`, `amount`, `evidence_have`, `evidence_missing`, `steps_tried`, `state/city`).
  - `summaries`: Stores `rolling_summary` covering conversation up to `covers_up_to_message_id`.
- **Safe Auto-Migration (`init_and_migrate_db`)**: Detects legacy schemas (e.g. SQLite legacy column `sessions.session_id`) and executes safe `ALTER TABLE` renames without data loss.
- **Context Builder Budgeting (`core/context.py`)**: Enforces a 12,000-character budget across system prompt, case file, rolling summary, verbatim recent turns, and grounded `AUTHORITY` blocks.
- **Untrusted Input Isolation**: User input from historical messages is wrapped in `<user_message>` data delimiters to prevent prompt injection from stored chat logs.
- **Privacy First**: Temporary local session records can be wiped at any time using the "Delete my data" button (cascade deletion across all 4 tables). Sessions inactive for >30 days are automatically pruned.

## 4. Scope Gate Design & Safety Firewall (`core/scope.py`)
- **Strict 3-Domain Gate**: Queries are classified into `tenancy`, `consumer`, `employment`, `greeting_or_intake`, or `out_of_scope`.
- **Deterministic Rejection**: Out-of-scope queries return the exact string `"I do not know."` (or translated Hindi `"मुझे नहीं पता।"`) without calling generative models.
- **Confidence Threshold**: Classifications below 0.70 confidence or failing structured validation default to `out_of_scope` to prevent accidental hallucination on ambiguous queries.
- **Follow-Up Awareness**: Classification evaluates the latest message alongside previous conversation context so that short contextual replies (e.g. "yes", "draft notice", "he didn't pay") in active cases remain in-scope.
- **Emergency Exception**: Immediate physical harm or domestic abuse triggers immediate routing to 112 (National Emergency) or 181 (Women Helpline).
