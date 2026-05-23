# LLM-чат: фильтры, интенты и подготовленная RAG-база

Этот документ описывает архитектуру обновлённого LLM-чата (issue #24) и то,
как добавить собственные источники знаний в будущем.

## Компоненты

```
backend/
├── chat_service.py        # Сборка системного промпта + вызов Ollama
├── intent_classifier.py   # Понимает, относится ли вопрос к личности/эпохе
└── knowledge_base.py      # In-memory RAG (per-leader корпус + retriever)
```

### `IntentClassifier`

Решает, что делать с пользовательским сообщением, и возвращает
`IntentResult(intent, confidence, reason, scores)`. Возможные значения
`intent`:

| Значение     | Поведение чата                                          |
|--------------|---------------------------------------------------------|
| `on_topic`   | Передать LLM, добавить RAG-контекст                     |
| `uncertain`  | То же самое, что `on_topic`, но менее уверенно          |
| `off_topic`  | Короткий вежливый отказ, LLM не дёргается               |
| `jailbreak`  | Отказ с напоминанием о роли                             |

Классификатор работает в три прохода:

1. Регулярки для очевидных jailbreak'ов (например, «забудь все
   инструкции»).
2. Регулярки для очевидных off-topic'ов (программирование, погода,
   рецепты, курс доллара).
3. Семантическая близость к двум наборам якорей (если доступны
   эмбеддинги через `sentence-transformers`) либо мягкая эвристика на
   ключевых словах (если нет).

### `KnowledgeBase`

In-memory хранилище фрагментов знаний, разбитое по `leader_id`. Ранжирует
документы либо по эмбеддингам (если передан `embedder`), либо по
лёгкому собственному TF-IDF. Главное API:

```python
from knowledge_base import KnowledgeBase, KnowledgeDocument

kb = KnowledgeBase()
kb.bootstrap_from_leader(leader_row)   # биография/достижения/наследие → чанки
kb.add_documents([KnowledgeDocument(   # ваши кастомные источники
    leader_id=1,
    text="...",
    source="wiki_dump",
    title="Апрельские тезисы",
)])
docs = kb.retrieve(leader_id=1, query="апрельские тезисы", top_k=3)
```

`KnowledgeDocument.metadata` — произвольный словарь; используйте его
для ссылки на URL, даты, теги и т. д.

### Куда подключать собственный корпус

`build_default_chat_service(leader_loader)` принимает функцию,
возвращающую список деятелей. RAG-база сама автоматически индексирует
их биографические поля при первом обращении к чату.

Чтобы подгрузить ваш собственный корпус (например, дамп статей с
исторических порталов), сделайте так:

```python
from chat_service import build_default_chat_service
from knowledge_base import KnowledgeDocument

chat_service = build_default_chat_service(leader_loader=db.get_all_leaders)
chat_service.knowledge_base.add_documents([
    KnowledgeDocument(
        leader_id=1,
        text=open("data/lenin/april_theses.txt", encoding="utf-8").read(),
        source="archive",
        title="Апрельские тезисы",
    ),
])
```

## Тумблеры через переменные окружения

| Переменная               | Что делает                                                   |
|--------------------------|--------------------------------------------------------------|
| `CHAT_INTENT_DISABLED`   | Если `1`/`true`/`yes` — классификатор всегда возвращает `uncertain` (и не блокирует) |
| `CHAT_RAG_DISABLED`      | Полностью выключает RAG: контекст не добавляется, документы не индексируются |
| `CHAT_RAG_TOP_K`         | Сколько чанков подтягивать (по умолчанию 3)                  |
| `CHAT_MAX_HISTORY`       | Хранилище истории внутри одного сеанса                       |
| `OLLAMA_BASE_URL`        | URL Ollama (по умолчанию `http://localhost:11434`)           |
| `OLLAMA_MODEL`           | Модель LLM (по умолчанию `llama3.1:8b`)                      |

## Регрессия из issue #24

Сообщение «Почему вы выбрали марксизм?» теперь:

* Классифицируется как `on_topic` (см. `tests/test_intent_classifier.py::test_marxism_question_is_on_topic`).
* Проходит до LLM, получает RAG-контекст из биографии (`tests/test_chat_service.py::test_chat_lets_marxism_question_reach_the_llm`).
* Системный промпт прямо разрешает обсуждение идеологии, мотивов и личных взглядов.
