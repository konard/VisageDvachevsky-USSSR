"""Intent classifier for the leader chat.

The previous version of the chat service refused too eagerly: a perfectly
on-topic question like "почему ты выбрал марксизм?" was rejected by overly
aggressive keyword filters.  This module replaces the regex-only short-circuit
with a structured classifier that combines:

* A small, high-precision set of jailbreak/off-topic regex patterns.
* Hand-curated topic anchors (works for any historical figure).
* Per-leader topic anchors built from the leader's database row.
* Optional semantic embeddings (sentence-transformers) for the heavy lifting.

The output is an :class:`IntentResult` that callers can use to decide whether
to short-circuit the request, hand it to the LLM, or attach extra context.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hand-curated anchors


# Generic statements that describe what kind of conversation belongs in the
# chat with a historical Soviet figure.  Embedding similarity against these
# anchors is what catches questions like "почему ты выбрал марксизм?" — the
# anchors mention ideology, motivation and personal reflection.
TOPIC_ANCHORS: Tuple[str, ...] = (
    "биография советского политического деятеля, его жизнь и эпоха",
    "идеология, философия, политические и личные взгляды",
    "почему вы приняли это решение и какие мотивы стояли за вашими действиями",
    "ваше отношение к марксизму, коммунизму, социализму и капитализму",
    "ключевые реформы, политические шаги, экономические преобразования",
    "детство, семья, образование, формирование мировоззрения",
    "революция, гражданская война, Великая Отечественная война, холодная война",
    "ваши соратники, оппоненты, отношения внутри партии и государства",
    "память о вас, ваше историческое наследие и оценки потомков",
    "будни главы государства, повседневная работа, привычки и характер",
)


# Examples of questions that have nothing to do with a Soviet leader.  Used as
# negative anchors when embeddings are available.
OFF_TOPIC_ANCHORS: Tuple[str, ...] = (
    "напиши код на python для парсинга json",
    "какая сегодня погода в москве и завтра в санкт-петербурге",
    "как приготовить борщ или другое блюдо",
    "какой сейчас курс доллара, евро и биткоина",
    "посоветуй современный смартфон или ноутбук",
    "помоги решить квадратное уравнение",
    "расскажи анекдот про животных",
    "напиши пост для социальных сетей",
    "что такое искусственный интеллект и нейросети",
    "найди мне рецепт пирога",
    "как настроить wi-fi роутер",
    "переведи этот текст на английский",
)


# Strong jailbreak triggers.  These remain regex so we never let them through
# regardless of what the embedding model thinks.
JAILBREAK_PATTERNS: Tuple[str, ...] = (
    r"\bignore\s+(?:all|previous|prior)\b.*\binstructions?\b",
    r"забудь(?:те)?\s+(?:все\s+)?(?:предыдущ\w+|прошл\w+|свои)\s+(?:инструкц\w+|правил\w+|указан\w+)",
    r"игнорируй(?:те)?\s+(?:все\s+)?(?:предыдущ\w+|прошл\w+|свои|инструкц\w+|правил\w+|указан\w+)",
    r"раскрой(?:те)?\s+(?:свой\s+)?(?:системн\w+\s+промпт|system\s+prompt|инструкц\w+)",
    r"покажи(?:те)?\s+(?:свой\s+)?(?:системн\w+\s+промпт|system\s+prompt)",
    r"\bsystem\s+prompt\b",
    r"\bdo\s+anything\s+now\b|\bdan\b",
    r"\bjailbreak\b",
    r"ты\s+(?:теперь|больше\s+не)\s+(?:не\s+)?(?:ленин|сталин|хрущ|брежнев|андропов|черненко|горбач|деятел\w+|человек)",
)


# Hard off-topic triggers.  Kept small, only patterns that are unambiguous.
HARD_OFF_TOPIC_PATTERNS: Tuple[str, ...] = (
    r"напиши\s+(?:мне\s+)?(?:код|программ\w+|скрипт|функци\w+|класс)\b",
    r"\b(?:python|javascript|typescript|java|kotlin|swift|golang|rust|php|sql)\b",
    r"\bреши\s+(?:уравнение|задач\w+|пример)\b",
    r"курс\s+(?:доллара|евро|валюты|биткоин\w*|крипт\w+)",
    r"погод[аеу]\s+(?:в|на)\s+\S+",
    r"какая\s+погода",
    r"\biphone\b|\bandroid\b|\bблокчейн\b|\bnft\b",
    r"\bgpt\b|\bopenai\b|\bchatgpt\b|\bclaude\b|\bgemini\b",
)


# Tokens that boost on-topic confidence even without embeddings.  Mostly used
# by the heuristic fallback to recognise "марксизм", "октябрь" и т.п. как
# чёткие признаки исторического разговора.
HISTORICAL_TOPIC_TOKENS: Tuple[str, ...] = (
    "маркс", "ленин", "сталин", "хрущ", "брежнев", "андропов", "черненко",
    "горбач", "коммунизм", "социализм", "капитализм", "большевик", "меньшевик",
    "царь", "цар", "революци", "октябр", "февральск", "буржу", "пролетар",
    "партия", "цк", "кпсс", "ркпб", "вкпб", "совнарком", "политбюро",
    "ссср", "союз", "советск", "коллективизац", "индустриализац", "нэп",
    "перестройк", "гласност", "оттепел", "застой", "репресси", "гулаг",
    "война", "великая отечественная", "холодная война", "карибск",
    "космос", "спутник", "гагарин", "сталинград", "ленинград", "москва",
    "идеолог", "философ", "мировоззрен", "мотив", "решен", "выбор",
    "вера", "убежден", "взгляд", "почему", "зачем", "как вы", "что вы",
    "ваш", "вы ", "тебе ", "тебя ", "тво", "себе", "себя",
    "детств", "юност", "семь", "брат", "сестр", "родител", "образован",
    "ссылк", "арест", "тюрьм", "эмигра", "женев", "цюрих", "лондон",
)


# Tokens that confidently mark off-topic.
HARD_OFF_TOPIC_TOKENS: Tuple[str, ...] = (
    "python", "javascript", "sql", "html", "css", "react",
    "погода", "курс доллара", "биткоин", "блокчейн",
    "рецепт", "приготовь", "сваря", "испеч",
    "iphone", "android", "роутер", "wi-fi",
    "chatgpt", "openai", "gpt", "нейросет", "большая языковая",
    "анекдот", "шутк",
)


@dataclass
class IntentResult:
    """Outcome of intent classification.

    ``intent`` is one of:

    * ``"jailbreak"`` — attempts to break out of role, refuse hard.
    * ``"off_topic"`` — clearly unrelated to the leader, polite redirect.
    * ``"on_topic"`` — confidently about the leader / era, let LLM answer.
    * ``"uncertain"`` — pass through to LLM; treat as on-topic by default.
    """

    intent: str
    confidence: float
    reason: str = ""
    scores: Dict[str, float] = field(default_factory=dict)

    @property
    def is_blocking(self) -> bool:
        """Whether the chat service should refuse without calling the LLM."""
        return self.intent in {"off_topic", "jailbreak"}


class IntentClassifier:
    """Classify a chat message as on/off-topic for a given leader."""

    # Tunable thresholds.  Kept generous so we err on the side of letting
    # questions through — the previous behaviour was the opposite.
    SEMANTIC_ON_TOPIC_THRESHOLD = 0.42
    SEMANTIC_OFF_TOPIC_THRESHOLD = 0.55
    SEMANTIC_OFF_TOPIC_MARGIN = 0.08

    def __init__(self, embedder=None) -> None:
        """Construct the classifier.

        ``embedder`` is any object exposing an ``encode(text)`` method that
        returns a numpy array (i.e. a ``sentence_transformers.SentenceTransformer``
        instance).  When omitted the classifier uses purely heuristic rules.
        """
        self._embedder = embedder
        self._anchor_cache: Dict[str, "Sequence[float]"] = {}
        self._enabled = os.environ.get("CHAT_INTENT_DISABLED", "").lower() not in {"1", "true", "yes"}

    # ------------------------------------------------------------------
    # Public API

    def classify(self, message: str, leader: Optional[Dict] = None) -> IntentResult:
        """Classify ``message`` against the supplied ``leader``."""
        text = (message or "").strip()
        if not text:
            return IntentResult("off_topic", 1.0, "empty message")

        if not self._enabled:
            return IntentResult("uncertain", 0.0, "intent classifier disabled via env")

        lowered = text.lower()

        if self._matches_any(JAILBREAK_PATTERNS, lowered):
            return IntentResult("jailbreak", 0.95, "jailbreak pattern matched")

        if self._matches_any(HARD_OFF_TOPIC_PATTERNS, lowered):
            return IntentResult("off_topic", 0.9, "hard off-topic pattern matched")

        semantic = self._semantic_classify(text, leader)
        if semantic is not None:
            return semantic

        return self._heuristic_classify(lowered, leader)

    # ------------------------------------------------------------------
    # Embedding-based path

    def _semantic_classify(
        self, text: str, leader: Optional[Dict]
    ) -> Optional[IntentResult]:
        if self._embedder is None:
            return None

        try:
            import numpy as np  # local import keeps the module import-light
        except Exception:  # pragma: no cover - numpy is always installed alongside ST
            return None

        try:
            query = self._encode(text)
        except Exception as exc:  # pragma: no cover - depends on backend
            logger.warning("intent classifier: failed to embed message: %s", exc)
            return None

        topic_anchors = list(TOPIC_ANCHORS) + self._leader_anchors(leader)
        try:
            topic_vectors = [self._encode(a) for a in topic_anchors]
            off_topic_vectors = [self._encode(a) for a in OFF_TOPIC_ANCHORS]
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("intent classifier: failed to embed anchors: %s", exc)
            return None

        on_score = max((_cosine(query, v) for v in topic_vectors), default=0.0)
        off_score = max((_cosine(query, v) for v in off_topic_vectors), default=0.0)
        scores = {"on_topic": float(on_score), "off_topic": float(off_score)}

        if off_score >= self.SEMANTIC_OFF_TOPIC_THRESHOLD and off_score - on_score >= self.SEMANTIC_OFF_TOPIC_MARGIN:
            return IntentResult(
                "off_topic",
                float(off_score),
                f"semantic off-topic (on={on_score:.2f}, off={off_score:.2f})",
                scores,
            )

        if on_score >= self.SEMANTIC_ON_TOPIC_THRESHOLD and on_score >= off_score - 0.05:
            return IntentResult(
                "on_topic",
                float(on_score),
                f"semantic on-topic (on={on_score:.2f}, off={off_score:.2f})",
                scores,
            )

        # Fall through to heuristics if the model is unsure.
        heuristic = self._heuristic_classify(text.lower(), leader)
        heuristic.scores = {**scores, **heuristic.scores}
        if not heuristic.reason:
            heuristic.reason = f"semantic uncertain (on={on_score:.2f}, off={off_score:.2f})"
        return heuristic

    def _encode(self, text: str):
        cached = self._anchor_cache.get(text)
        if cached is not None:
            return cached
        vector = self._embedder.encode(text, convert_to_numpy=True)
        self._anchor_cache[text] = vector
        return vector

    # ------------------------------------------------------------------
    # Heuristic fallback

    def _heuristic_classify(self, lowered: str, leader: Optional[Dict]) -> IntentResult:
        topic_hits = self._token_hits(lowered, HISTORICAL_TOPIC_TOKENS)
        topic_hits += self._token_hits(lowered, self._leader_keywords(leader))
        off_hits = self._token_hits(lowered, HARD_OFF_TOPIC_TOKENS)

        if off_hits and off_hits >= topic_hits:
            return IntentResult(
                "off_topic",
                0.7,
                f"heuristic off-topic (topic={topic_hits}, off={off_hits})",
                {"topic_hits": float(topic_hits), "off_hits": float(off_hits)},
            )

        if topic_hits:
            confidence = min(0.5 + 0.1 * topic_hits, 0.9)
            return IntentResult(
                "on_topic",
                confidence,
                f"heuristic on-topic (topic={topic_hits})",
                {"topic_hits": float(topic_hits), "off_hits": float(off_hits)},
            )

        return IntentResult(
            "uncertain",
            0.0,
            "no strong signals — defer to LLM",
            {"topic_hits": float(topic_hits), "off_hits": float(off_hits)},
        )

    # ------------------------------------------------------------------
    # Helpers

    @staticmethod
    def _matches_any(patterns: Iterable[str], text: str) -> bool:
        return any(re.search(pattern, text) for pattern in patterns)

    @staticmethod
    def _token_hits(text: str, tokens: Iterable[str]) -> int:
        hits = 0
        for token in tokens:
            if token and token in text:
                hits += 1
        return hits

    @staticmethod
    def _leader_keywords(leader: Optional[Dict]) -> List[str]:
        if not leader:
            return []
        keywords: List[str] = []
        for field_name in ("name_ru", "name_en", "position", "birth_place", "death_place"):
            value = leader.get(field_name)
            if not value:
                continue
            for part in re.split(r"[\s,.()\-]+", str(value).lower()):
                if len(part) >= 4:
                    keywords.append(part)
        return keywords

    @staticmethod
    def _leader_anchors(leader: Optional[Dict]) -> List[str]:
        if not leader:
            return []
        anchors: List[str] = []
        name = leader.get("name_ru") or leader.get("name_en")
        if name:
            anchors.append(f"вопросы о жизни и деятельности {name}")
        position = leader.get("position")
        if position:
            anchors.append(f"работа и решения на посту {position}")
        for source in ("short_description", "biography", "achievements", "legacy"):
            value = leader.get(source)
            if value:
                anchors.append(str(value)[:400])
        return anchors


def _cosine(a, b) -> float:
    """Cosine similarity for two numpy vectors with a safe fallback."""
    import numpy as np

    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)
