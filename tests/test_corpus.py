"""Unit tests for LegalCorpus and BM25 retriever."""

from core.corpus import LegalCorpus
from core.models import LegalStatus


def test_corpus_loading():
    corpus = LegalCorpus()
    assert len(corpus.entries) >= 20
    # Check key statutory IDs
    assert "CPA_2019_SEC_2_11" in corpus.entries
    assert "MTA_2021_SEC_11" in corpus.entries
    assert "PWA_1936_SEC_5" in corpus.entries
    assert "ICA_1872_SEC_73" in corpus.entries
    assert "LSAA_1987_SEC_12" in corpus.entries


def test_model_tenancy_status():
    corpus = LegalCorpus()
    mta_entry = corpus.get_entry("MTA_2021_SEC_11")
    assert mta_entry is not None
    assert mta_entry.status == LegalStatus.MODEL_LAW


def test_bm25_retrieval_tenancy():
    corpus = LegalCorpus()
    results = corpus.search("landlord refused to return my security deposit when vacating flat", top_k=3)
    assert len(results) > 0
    ids = [r.id for r in results]
    # Expect MTA_2021_SEC_11 or TPA provisions
    assert any("MTA" in i or "TPA" in i for i in ids)


def test_bm25_retrieval_consumer():
    corpus = LegalCorpus()
    results = corpus.search("smartphone bought online has defective display and company denies refund", top_k=3)
    assert len(results) > 0
    ids = [r.id for r in results]
    assert any("CPA" in i for i in ids)


def test_bm25_retrieval_employment():
    corpus = LegalCorpus()
    results = corpus.search("employer did not pay last month salary and final settlement", top_k=3)
    assert len(results) > 0
    ids = [r.id for r in results]
    assert any("PWA" in i or "IDA" in i for i in ids)


def test_format_authority_block():
    corpus = LegalCorpus()
    entries = corpus.search("security deposit", top_k=2)
    block = corpus.format_authority_block(entries)
    assert "AUTHORITY" in block
    assert "START PROVISION" in block
    for e in entries:
        assert e.id in block
