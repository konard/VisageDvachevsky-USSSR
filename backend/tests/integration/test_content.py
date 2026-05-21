"""
Integration tests for the content endpoints exposed by the enhanced stack:
- /api/timeline   — chronology 1917–1991
- /api/connections — relationships graph
- /api/quiz       — single «Кто на портрете?» question
"""
import json

import pytest


def test_timeline_returns_events_sorted_chronologically(client, seeded_db):
    response = client.get('/api/timeline')

    assert response.status_code == 200
    payload = json.loads(response.data)
    assert payload['success'] is True

    events = payload['events']
    assert isinstance(events, list)
    assert len(events) >= 10

    # Verify chronological order (year then month, treating missing month as 0)
    def sort_key(event):
        return (event.get('year', 0), event.get('month') or 0)

    assert events == sorted(events, key=sort_key)

    sample = events[0]
    for required in ('year', 'title', 'description', 'category', 'leader_ids'):
        assert required in sample


def test_timeline_covers_iconic_events(client, seeded_db):
    response = client.get('/api/timeline')
    payload = json.loads(response.data)
    titles = {event['title'] for event in payload['events']}

    expected_keywords = {
        'Октябрьская революция',
        'Образование СССР',
        'Полёт Гагарина',
        'Распад СССР',
    }
    for needle in expected_keywords:
        assert any(needle in title for title in titles), f'Missing event «{needle}»'


def test_connections_returns_nodes_edges_and_legend(client, seeded_db):
    response = client.get('/api/connections')

    assert response.status_code == 200
    payload = json.loads(response.data)
    assert payload['success'] is True
    assert 'nodes' in payload and 'edges' in payload and 'link_types' in payload

    nodes = payload['nodes']
    edges = payload['edges']
    link_types = payload['link_types']

    assert len(nodes) >= 10
    assert len(edges) >= 10
    assert link_types  # legend dict isn't empty

    # All edge endpoints must resolve to existing nodes
    node_ids = {n['id'] for n in nodes}
    for edge in edges:
        assert edge['source'] in node_ids
        assert edge['target'] in node_ids
        assert edge['type'] in link_types

    # Nodes carry enrichment fields needed by the canvas renderer
    sample_node = nodes[0]
    for required in ('id', 'name_ru', 'category', 'portrait_url'):
        assert required in sample_node


def test_quiz_returns_one_question_with_four_options(client, seeded_db):
    response = client.get('/api/quiz')

    assert response.status_code == 200
    payload = json.loads(response.data)
    assert payload['success'] is True

    question = payload['question']
    options = payload['options']

    assert 'leader_id' in question and 'portrait_url' in question
    assert question['portrait_url']  # the answer always carries a portrait
    assert len(options) == 4

    option_ids = [opt['id'] for opt in options]
    assert len(set(option_ids)) == 4, 'Options must be unique'
    assert payload['answer_id'] in option_ids
    assert question['leader_id'] == payload['answer_id']
