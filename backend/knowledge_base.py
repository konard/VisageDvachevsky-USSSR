"""Lightweight retrieval layer for the leader chat.

This module is the skeleton of a RAG pipeline.  It can be used standalone
(today) to pull the most relevant snippets from the leader's database row,
and it is designed to be extended with external sources (Wikipedia dumps,
historical archives, custom uploads) once the maintainer is ready to add
them — see :meth:`KnowledgeBase.add_documents`.

The retriever supports two modes:

* **Embedding mode** — semantic similarity via a sentence-transformers model.
* **TF-IDF fallback** — a tiny pure-python ranker so the chat keeps working
  in environments where ML dependencies are not installed.

Documents are scoped by ``leader_id`` so a question about Stalin only
retrieves Stalin's knowledge fragments.
"""

from __future__ import annotations

import logging
import math
import os
import re
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeDocument:
    """A single retrievable knowledge chunk."""

    leader_id: int
    text: str
    source: str = "leader_profile"
    title: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    # Set lazily by the knowledge base when the doc is added.
    embedding: Optional[Sequence[float]] = None
    # Bag-of-words (lowercased token -> count); cached for the TF-IDF fallback.
    _tokens: Optional[Dict[str, int]] = None

    def as_snippet(self, max_chars: int = 320) -> str:
        text = self.text.strip()
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 1].rstrip() + "…"


_TOKEN_RE = re.compile(r"[\wёЁ]+", re.UNICODE)


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) >= 2]


def _chunk_text(text: str, max_chars: int = 360) -> List[str]:
    """Split text into reasonably sized chunks on sentence boundaries."""
    text = (text or "").strip()
    if not text:
        return []
    # Split on sentence boundaries first.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    buf = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if not buf:
            buf = sentence
            continue
        if len(buf) + 1 + len(sentence) <= max_chars:
            buf = f"{buf} {sentence}"
        else:
            chunks.append(buf)
            buf = sentence
    if buf:
        chunks.append(buf)
    return chunks


class KnowledgeBase:
    """In-memory store of knowledge documents per historical leader.

    The store is intentionally simple.  When you want to plug a real RAG
    backend (Chroma, Qdrant, pgvector, …) replace this class while keeping
    the :meth:`retrieve` / :meth:`add_documents` API stable.
    """

    def __init__(
        self,
        embedder=None,
        leader_loader: Optional[Callable[[], Iterable[Dict]]] = None,
    ) -> None:
        self._embedder = embedder
        self._docs: Dict[int, List[KnowledgeDocument]] = {}
        self._df: Dict[str, int] = {}  # token -> document frequency
        self._lock = threading.Lock()
        self._bootstrapped: set[int] = set()
        self._leader_loader = leader_loader
        self._all_leaders_loaded = False
        self._enabled = os.environ.get("CHAT_RAG_DISABLED", "").lower() not in {"1", "true", "yes"}

    # ------------------------------------------------------------------
    # Public API

    def is_enabled(self) -> bool:
        return self._enabled

    def add_documents(self, documents: Iterable[KnowledgeDocument]) -> int:
        """Insert one or more documents.  Returns the number actually stored."""
        if not self._enabled:
            return 0
        added = 0
        with self._lock:
            for doc in documents:
                text = (doc.text or "").strip()
                if not text or doc.leader_id is None:
                    continue
                tokens = _tokenize(text)
                if not tokens:
                    continue
                token_counts: Dict[str, int] = {}
                for tok in tokens:
                    token_counts[tok] = token_counts.get(tok, 0) + 1
                doc._tokens = token_counts
                for tok in token_counts:
                    self._df[tok] = self._df.get(tok, 0) + 1
                if self._embedder is not None and doc.embedding is None:
                    try:
                        doc.embedding = self._embedder.encode(text, convert_to_numpy=True)
                    except Exception as exc:  # pragma: no cover - defensive
                        logger.warning("knowledge base: embed failed: %s", exc)
                        doc.embedding = None
                self._docs.setdefault(doc.leader_id, []).append(doc)
                added += 1
        return added

    def bootstrap_from_leader(self, leader: Dict) -> int:
        """Populate the store with the obvious fragments of a leader's profile.

        Safe to call multiple times — it tracks which leaders have already been
        bootstrapped via ``leader["id"]`` and is a no-op afterwards.
        """
        if not self._enabled:
            return 0
        leader_id = leader.get("id")
        if leader_id is None:
            return 0
        with self._lock:
            if leader_id in self._bootstrapped:
                return 0
            self._bootstrapped.add(leader_id)

        documents: List[KnowledgeDocument] = []
        for field_name, title in (
            ("biography", "Биография"),
            ("achievements", "Главные достижения"),
            ("legacy", "Историческое наследие"),
            ("short_description", "Краткое описание"),
        ):
            value = leader.get(field_name)
            if not value:
                continue
            for chunk in _chunk_text(str(value)):
                documents.append(
                    KnowledgeDocument(
                        leader_id=leader_id,
                        text=chunk,
                        source="leader_profile",
                        title=title,
                        metadata={"field": field_name},
                    )
                )
        meta_bits = []
        if leader.get("position"):
            meta_bits.append(f"Должность: {leader['position']}.")
        if leader.get("birth_year"):
            meta_bits.append(f"Год рождения: {leader['birth_year']}.")
        if leader.get("death_year"):
            meta_bits.append(f"Год смерти: {leader['death_year']}.")
        if leader.get("birth_place"):
            meta_bits.append(f"Место рождения: {leader['birth_place']}.")
        if meta_bits:
            documents.append(
                KnowledgeDocument(
                    leader_id=leader_id,
                    text=" ".join(meta_bits),
                    source="leader_profile",
                    title="Биографические сведения",
                    metadata={"field": "meta"},
                )
            )
        return self.add_documents(documents)

    def bootstrap_all(self) -> int:
        """Bootstrap from every leader returned by ``leader_loader``."""
        if not self._enabled or self._leader_loader is None or self._all_leaders_loaded:
            return 0
        added = 0
        for leader in self._leader_loader() or []:
            added += self.bootstrap_from_leader(leader)
        self._all_leaders_loaded = True
        return added

    def retrieve(
        self,
        leader_id: int,
        query: str,
        top_k: int = 3,
    ) -> List[KnowledgeDocument]:
        """Return the top ``top_k`` documents for ``leader_id`` matching ``query``."""
        if not self._enabled:
            return []
        query = (query or "").strip()
        if not query:
            return []
        candidates = list(self._docs.get(leader_id, ()))
        if not candidates:
            return []

        ranked: List[Tuple[float, KnowledgeDocument]]
        if self._embedder is not None and any(d.embedding is not None for d in candidates):
            ranked = self._rank_with_embeddings(query, candidates)
        else:
            ranked = self._rank_with_tfidf(query, candidates)

        ranked.sort(key=lambda x: x[0], reverse=True)
        relevant = [doc for score, doc in ranked if score > 0]
        return relevant[:top_k] if relevant else [doc for _, doc in ranked[:top_k]]

    def stats(self) -> Dict[str, int]:
        """Operational stats useful for /health and debugging."""
        return {
            "enabled": int(self._enabled),
            "leaders": len(self._docs),
            "documents": sum(len(v) for v in self._docs.values()),
            "unique_tokens": len(self._df),
        }

    # ------------------------------------------------------------------
    # Internal ranking

    def _rank_with_embeddings(
        self, query: str, docs: List[KnowledgeDocument]
    ) -> List[Tuple[float, KnowledgeDocument]]:
        try:
            import numpy as np  # noqa: F401
        except Exception:  # pragma: no cover
            return self._rank_with_tfidf(query, docs)

        try:
            query_vec = self._embedder.encode(query, convert_to_numpy=True)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("knowledge base: query embed failed: %s", exc)
            return self._rank_with_tfidf(query, docs)

        ranked: List[Tuple[float, KnowledgeDocument]] = []
        for doc in docs:
            if doc.embedding is None:
                ranked.append((0.0, doc))
                continue
            ranked.append((_cosine(query_vec, doc.embedding), doc))
        return ranked

    def _rank_with_tfidf(
        self, query: str, docs: List[KnowledgeDocument]
    ) -> List[Tuple[float, KnowledgeDocument]]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return [(0.0, d) for d in docs]
        total_docs = max(sum(len(v) for v in self._docs.values()), 1)

        # Pre-compute query term frequencies.
        query_tf: Dict[str, int] = {}
        for tok in query_tokens:
            query_tf[tok] = query_tf.get(tok, 0) + 1

        ranked: List[Tuple[float, KnowledgeDocument]] = []
        for doc in docs:
            if not doc._tokens:
                ranked.append((0.0, doc))
                continue
            score = 0.0
            doc_len = sum(doc._tokens.values()) or 1
            for tok, q_count in query_tf.items():
                if tok not in doc._tokens:
                    continue
                tf = doc._tokens[tok] / doc_len
                df = self._df.get(tok, 1)
                idf = math.log((total_docs + 1) / (df + 1)) + 1.0
                score += q_count * tf * idf
            ranked.append((score, doc))
        return ranked


def _cosine(a, b) -> float:
    import numpy as np

    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def format_context_block(documents: Sequence[KnowledgeDocument]) -> str:
    """Render retrieved documents as a clean block for the LLM system prompt."""
    if not documents:
        return ""
    lines = ["Дополнительные сведения из базы знаний (можешь опираться на них):"]
    for idx, doc in enumerate(documents, start=1):
        prefix = f"[{idx}]"
        if doc.title:
            prefix = f"{prefix} {doc.title}:"
        lines.append(f"{prefix} {doc.as_snippet()}")
    return "\n".join(lines)
