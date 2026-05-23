"""Tests for the lightweight RAG layer that backs the leader chat."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from knowledge_base import (  # noqa: E402
    KnowledgeBase,
    KnowledgeDocument,
    format_context_block,
)


LEADER = {
    "id": 1,
    "name_ru": "Владимир Ильич Ленин",
    "position": "Председатель Совета народных комиссаров",
    "biography": (
        "Родился в Симбирске. После казни старшего брата Александра в 1887 году "
        "встал на путь революционной борьбы. Окончил юридический факультет "
        "Казанского университета. Создал партию большевиков и в 1917 году "
        "возглавил Октябрьскую революцию."
    ),
    "achievements": (
        "Организовал Октябрьскую революцию и создал первое в мире социалистическое "
        "государство. Провёл национализацию промышленности. Заключил Брестский мир."
    ),
    "legacy": "Ленинизм как политическая идеология определял курс СССР.",
    "short_description": "Основатель советского государства.",
    "birth_year": 1870,
    "death_year": 1924,
    "birth_place": "Симбирск",
}


def test_bootstrap_indexes_leader_documents():
    kb = KnowledgeBase()
    added = kb.bootstrap_from_leader(LEADER)
    assert added > 0

    stats = kb.stats()
    assert stats["leaders"] == 1
    assert stats["documents"] >= added


def test_bootstrap_is_idempotent():
    kb = KnowledgeBase()
    first = kb.bootstrap_from_leader(LEADER)
    assert first > 0
    second = kb.bootstrap_from_leader(LEADER)
    assert second == 0


def test_retrieve_returns_relevant_snippets():
    kb = KnowledgeBase()
    kb.bootstrap_from_leader(LEADER)

    docs = kb.retrieve(LEADER["id"], "Расскажите о казни вашего брата", top_k=2)
    assert docs, "expected at least one matching document"
    joined = " ".join(d.text for d in docs).lower()
    # The biography mentions Aleksandr's execution; verifies relevance ranking.
    assert "брата" in joined or "александра" in joined


def test_retrieve_ignores_other_leaders():
    kb = KnowledgeBase()
    kb.bootstrap_from_leader(LEADER)
    other = dict(LEADER, id=2, biography="Сталин руководил индустриализацией.")
    kb.bootstrap_from_leader(other)

    docs = kb.retrieve(2, "индустриализация", top_k=3)
    assert all(d.leader_id == 2 for d in docs)
    assert any("индустриализаци" in d.text.lower() for d in docs)


def test_retrieve_returns_empty_when_disabled(monkeypatch):
    monkeypatch.setenv("CHAT_RAG_DISABLED", "1")
    kb = KnowledgeBase()
    added = kb.bootstrap_from_leader(LEADER)
    assert added == 0
    assert kb.retrieve(LEADER["id"], "марксизм", top_k=3) == []


def test_add_documents_supports_custom_sources():
    kb = KnowledgeBase()
    kb.add_documents([
        KnowledgeDocument(
            leader_id=1,
            text="В апрельских тезисах 1917 года Ленин сформулировал идею перехода ко второму этапу революции.",
            source="custom_archive",
            title="Апрельские тезисы",
        )
    ])
    docs = kb.retrieve(1, "апрельские тезисы", top_k=1)
    assert docs and docs[0].source == "custom_archive"


def test_format_context_block_renders_titles_and_indices():
    docs = [
        KnowledgeDocument(leader_id=1, text="Первый факт.", title="Биография"),
        KnowledgeDocument(leader_id=1, text="Второй факт.", title="Наследие"),
    ]
    block = format_context_block(docs)
    assert "[1]" in block and "[2]" in block
    assert "Биография" in block and "Наследие" in block


def test_format_context_block_empty_returns_empty_string():
    assert format_context_block([]) == ""


def test_bootstrap_all_walks_leader_loader():
    def loader():
        yield LEADER
        yield dict(LEADER, id=2, biography="Сталин и индустриализация.")

    kb = KnowledgeBase(leader_loader=loader)
    added = kb.bootstrap_all()
    assert added > 0
    # Second call should be a no-op.
    assert kb.bootstrap_all() == 0


def test_uses_embedder_when_provided():
    """If an embedder is supplied, retrieval should compute embeddings."""
    np = pytest.importorskip("numpy")

    class FakeEmbedder:
        def __init__(self):
            self.calls = 0

        def encode(self, text, convert_to_numpy=True):
            self.calls += 1
            rng = np.random.default_rng(abs(hash(text)) % (2**32))
            return rng.standard_normal(8).astype(np.float32)

    embedder = FakeEmbedder()
    kb = KnowledgeBase(embedder=embedder)
    kb.bootstrap_from_leader(LEADER)
    assert embedder.calls > 0

    docs = kb.retrieve(LEADER["id"], "марксизм", top_k=2)
    # Just sanity-check that retrieval ran without crashing.
    assert isinstance(docs, list)
