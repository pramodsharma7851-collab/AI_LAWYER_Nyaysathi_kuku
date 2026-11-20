"""Unit tests for CitationVerifier and regex scanner."""

from core.corpus import LegalCorpus
from core.models import CitationItem, ConfidenceLevel, LegalOption, StructuredLegalAdvice
from core.verifier import CitationVerifier


def test_verifier_valid_citation():
    corpus = LegalCorpus()
    verifier = CitationVerifier(corpus=corpus)

    allowed = {"CPA_2019_SEC_2_11", "CPA_2019_SEC_39"}
    advice = StructuredLegalAdvice(
        summary="Your service provider committed a deficiency in service.",
        facts_extracted=["Product was not repaired within 30 days."],
        options=[
            LegalOption(
                title="File Consumer Grievance",
                description="Lodge a complaint on e-Daakhil.",
                pros=["Official forum"],
                cons=["Takes time"],
                estimated_timeframe="30 days",
                forum="District Commission",
            )
        ],
        citations=[
            CitationItem(
                corpus_id="CPA_2019_SEC_2_11",
                provision_name="Consumer Protection Act, 2019 Section 2(11)",
                relevance="Defines deficiency in service.",
            )
        ],
        confidence=ConfidenceLevel.HIGH,
        needs_lawyer=False,
    )

    result = verifier.verify(advice, allowed)
    assert result.is_valid
    assert len(result.errors) == 0


def test_verifier_rejects_unknown_corpus_id():
    corpus = LegalCorpus()
    verifier = CitationVerifier(corpus=corpus)

    allowed = {"CPA_2019_SEC_2_11"}
    advice = StructuredLegalAdvice(
        summary="Advice with fabricated citation ID.",
        citations=[
            CitationItem(
                corpus_id="FAKE_ACT_2025_SEC_999",
                provision_name="Fake Act Section 999",
                relevance="Invented provision.",
            )
        ],
        confidence=ConfidenceLevel.HIGH,
        needs_lawyer=False,
    )

    result = verifier.verify(advice, allowed)
    assert not result.is_valid
    assert any("does not exist in verified legal corpus" in err for err in result.errors)
    assert result.sanitized_advice is not None
    assert result.sanitized_advice.confidence == ConfidenceLevel.LOW


def test_verifier_rejects_unretrieved_corpus_id():
    corpus = LegalCorpus()
    verifier = CitationVerifier(corpus=corpus)

    # Allowed set does NOT include PWA_1936_SEC_5
    allowed = {"CPA_2019_SEC_2_11"}
    advice = StructuredLegalAdvice(
        summary="Citing valid provision that was not retrieved in prompt.",
        citations=[
            CitationItem(
                corpus_id="PWA_1936_SEC_5",
                provision_name="Payment of Wages Act Section 5",
                relevance="Payment within 2 days.",
            )
        ],
        confidence=ConfidenceLevel.HIGH,
        needs_lawyer=False,
    )

    result = verifier.verify(advice, allowed)
    assert not result.is_valid
    assert any("was not provided in the allowed authority block" in err for err in result.errors)


def test_regex_scanner_flags_repealed_ipc():
    corpus = LegalCorpus()
    verifier = CitationVerifier(corpus=corpus)

    allowed = {"CPA_2019_SEC_2_11"}
    advice = StructuredLegalAdvice(
        summary="The landlord committed cheating under Indian Penal Code Section 420.",
        citations=[],
        confidence=ConfidenceLevel.MEDIUM,
        needs_lawyer=False,
    )

    result = verifier.verify(advice, allowed)
    assert not result.is_valid
    assert any("repealed statute (IPC)" in err for err in result.errors)


def test_regex_scanner_flags_unverified_case_law():
    corpus = LegalCorpus()
    verifier = CitationVerifier(corpus=corpus)

    allowed = {"CPA_2019_SEC_2_11"}
    advice = StructuredLegalAdvice(
        summary="As held in Ramesh Kumar v. State of Delhi, AIR 2018 SC 123.",
        citations=[],
        confidence=ConfidenceLevel.MEDIUM,
        needs_lawyer=False,
    )

    result = verifier.verify(advice, allowed)
    assert not result.is_valid
    assert any("case citation" in err.lower() or "reporter citation" in err.lower() for err in result.errors)
