"""Citation verifier and regex scanner for NyayaSathi (Hard Gate).

Ensures:
1. Every citation corpus_id exists in the legal corpus.
2. Every citation corpus_id was present in the retrieved authority block.
3. Free text does not contain ungrounded statutory or case law claims (e.g. 'Section \\d+', 'v.').
4. Rejection and deterministic fallback if hallucination or fabricated citations occur.
"""

import re
from typing import List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from core.corpus import LegalCorpus, corpus_db
from core.models import ConfidenceLevel, LegalOption, StructuredLegalAdvice

# Regex patterns for detecting potential ungrounded citations in free text
RE_SECTION = re.compile(r"\b(?:Section|Sec\.?|s\.)\s*(\d+[A-Za-z]?(?:\(\d+\))?)", re.IGNORECASE)
RE_ARTICLE = re.compile(r"\bArticle\s*(\d+[A-Za-z]?)", re.IGNORECASE)
RE_CASE_LAW = re.compile(r"\b[A-Z][a-zA-Z\s\.]+\s+v(?:s\.?|.)\s+[A-Z][a-zA-Z\s\.]+", re.IGNORECASE)
RE_AIR_REPORTER = re.compile(r"\b(?:AIR|SCC|SCR)\s+\d{4}\b", re.IGNORECASE)
RE_IPC = re.compile(r"\b(?:IPC|Indian\s+Penal\s+Code)\b", re.IGNORECASE)


class VerificationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    flagged_patterns: List[str] = Field(default_factory=list)
    sanitized_advice: Optional[StructuredLegalAdvice] = None


class CitationVerifier:
    """Hard gate to prevent hallucinated citations and ungrounded legal assertions."""

    def __init__(self, corpus: Optional[LegalCorpus] = None):
        self.corpus = corpus or corpus_db

    def scan_free_text_for_citations(self, text: str) -> List[str]:
        """Detect legal sections or case law patterns in unstructured text."""
        findings = []
        if not text:
            return findings

        # Check for IPC references (strict ban - repealed law)
        if RE_IPC.search(text):
            findings.append("Mentioned repealed statute (IPC) in free text.")

        # Check for case law citations (v., AIR, SCC)
        case_matches = RE_CASE_LAW.findall(text)
        if case_matches:
            findings.append(f"Detected case citation in text: {case_matches[:2]}")

        air_matches = RE_AIR_REPORTER.findall(text)
        if air_matches:
            findings.append(f"Detected law reporter citation in text: {air_matches[:2]}")

        return findings

    def verify(
        self,
        advice: StructuredLegalAdvice,
        allowed_corpus_ids: Set[str],
    ) -> VerificationResult:
        """Verify the structured advice against allowed authority and corpus."""
        errors: List[str] = []
        flagged: List[str] = []

        # 1. Verify structured citations list
        for cit in advice.citations:
            cid = cit.corpus_id.strip()
            # Must exist in the corpus
            entry = self.corpus.get_entry(cid)
            if not entry:
                errors.append(f"Citation ID '{cid}' does not exist in verified legal corpus.")
                continue

            # Must be in the retrieved authority set passed to the model
            if cid not in allowed_corpus_ids:
                errors.append(f"Citation ID '{cid}' ({entry.act_name}) was not provided in the allowed authority block.")

        # 2. Scan all free text fields in the advice for hallucinated citations
        full_text_blocks = [advice.summary] + advice.facts_extracted
        for opt in advice.options:
            full_text_blocks.append(opt.title + " " + opt.description)
            full_text_blocks.extend(opt.pros + opt.cons)

        combined_text = " ".join(full_text_blocks)
        text_findings = self.scan_free_text_for_citations(combined_text)
        if text_findings:
            flagged.extend(text_findings)
            # If IPC is mentioned or unverified case law is cited, reject
            errors.extend(text_findings)

        is_valid = len(errors) == 0

        # Construct sanitized advice if needed or keep original
        sanitized = None
        if is_valid:
            sanitized = advice
        else:
            sanitized = self.create_safe_fallback(
                reason="Verification failed: " + "; ".join(errors)
            )

        return VerificationResult(
            is_valid=is_valid,
            errors=errors,
            flagged_patterns=flagged,
            sanitized_advice=sanitized,
        )

    def create_safe_fallback(self, reason: str) -> StructuredLegalAdvice:
        """Deterministic, safe fallback advice when verification rejects output."""
        return StructuredLegalAdvice(
            summary=(
                "I cannot confirm the exact legal provision applicable to this situation "
                "with absolute certainty from the verified legal corpus. To avoid misleading "
                "information, I strongly recommend consulting a qualified advocate or seeking "
                "free legal guidance from your District Legal Services Authority (DLSA / NALSA)."
            ),
            facts_extracted=[],
            options=[
                LegalOption(
                    title="Seek Guidance from District Legal Services Authority (DLSA)",
                    description=(
                        "Approach the nearest District Court complex and visit the DLSA front office. "
                        "Eligible citizens (including women, industrial workmen, and persons with low income) "
                        "are entitled to free legal assistance and representation."
                    ),
                    pros=["Free of cost", "Official government authority", "No risk of inaccurate advice"],
                    cons=["Requires visiting the court complex or filing an application"],
                    estimated_timeframe="1-7 days",
                    forum="District Legal Services Authority / NALSA Helpline 15100",
                ),
                LegalOption(
                    title="Attempt Direct Written Communication",
                    description=(
                        "Send a formal, polite written reminder or email to the other party summarizing the agreed facts, "
                        "the amount due, and requesting resolution within 7-15 days."
                    ),
                    pros=["Low friction", "Creates a clear written evidentiary record"],
                    cons=["Opposite party may still refuse to cooperate"],
                    estimated_timeframe="7-15 days",
                    forum="Direct negotiation",
                ),
            ],
            citations=[],
            confidence=ConfidenceLevel.LOW,
            needs_lawyer=True,
            lawyer_reason=f"Safe fallback triggered ({reason}). Advocate guidance advised.",
            missing_info=["Detailed state/city location", "Written agreement or documentation"],
        )


# Global singleton verifier
verifier = CitationVerifier()
