"""Corpus loader and BM25 retriever for NyayaSathi.

Loads verified statutory provisions from /corpus/*.json and provides
lexical BM25 retrieval to ground all LLM generations in strict statutory authority.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from rank_bm25 import BM25Okapi

from core.config import config
from core.models import CorpusEntry, LegalStatus


class LegalCorpus:
    """Manages the source-of-truth legal corpus."""

    def __init__(self, corpus_dir: Optional[Path] = None):
        self.corpus_dir = corpus_dir or config.corpus_dir
        self.entries: Dict[str, CorpusEntry] = {}
        self._corpus_list: List[CorpusEntry] = []
        self._bm25: Optional[BM25Okapi] = None
        self._tokenized_corpus: List[List[str]] = []
        self.load_corpus()

    def load_corpus(self) -> None:
        """Load and validate all JSON files in corpus_dir."""
        self.entries.clear()
        self._corpus_list.clear()

        if not self.corpus_dir.exists():
            return

        json_files = sorted(self.corpus_dir.glob("*.json"))
        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        entry = CorpusEntry(**item)
                        self.entries[entry.id] = entry
                        self._corpus_list.append(entry)
            except Exception as e:
                print(f"[WARN] Error loading corpus file {jf}: {e}")

        # Build BM25 index
        self._tokenized_corpus = []
        for entry in self._corpus_list:
            text_tokens = (
                entry.title.lower() + " " +
                entry.summary.lower() + " " +
                " ".join(entry.keywords).lower() + " " +
                entry.act_name.lower() + " " +
                entry.section_number.lower()
            ).split()
            self._tokenized_corpus.append(text_tokens)

        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)

    def get_entry(self, corpus_id: str) -> Optional[CorpusEntry]:
        """Lookup an entry by its unique corpus ID."""
        return self.entries.get(corpus_id)

    def search(self, query: str, top_k: int = 4, domain: Optional[str] = None) -> List[CorpusEntry]:
        """Search the corpus using BM25 and optional domain filter."""
        if not self._bm25 or not self._corpus_list:
            return []

        query_tokens = query.lower().split()
        scores = self._bm25.get_scores(query_tokens)

        # Pair entries with scores
        scored_entries = []
        for i, score in enumerate(scores):
            entry = self._corpus_list[i]
            if domain and entry.domain != domain and entry.domain != "general":
                # Penalize or skip out of domain
                continue
            scored_entries.append((score, entry))

        # Sort descending by score
        scored_entries.sort(key=lambda x: x[0], reverse=True)

        results = [entry for score, entry in scored_entries[:top_k]]
        return results

    def format_authority_block(self, entries: List[CorpusEntry]) -> str:
        """Format retrieved entries into a clear AUTHORITY block for LLM prompting."""
        if not entries:
            return "AUTHORITY:\n[No statutory provisions matched. You have NO authority to cite law for this query.]"

        lines = ["AUTHORITY (You may cite ONLY provisions from this list using their exact ID):"]
        for e in entries:
            lines.append(f"--- START PROVISION [{e.id}] ---")
            lines.append(f"Act: {e.act_name} ({e.year})")
            lines.append(f"Section/Rule: {e.section_number}")
            lines.append(f"Title: {e.title}")
            lines.append(f"Status: {e.status.value}")
            lines.append(f"Plain Summary: {e.summary}")
            lines.append(f"Extract: {e.verbatim_extract}")
            lines.append(f"--- END PROVISION [{e.id}] ---")
        return "\n".join(lines)


# Global singleton instance
corpus_db = LegalCorpus()
