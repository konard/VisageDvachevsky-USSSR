"""
Content routes shared across simple and enhanced stacks.

Exposes /api/timeline, /api/connections and /api/quiz built from the
curated `timeline_data` and `connections_data` modules.
"""
import random

from flask import Blueprint, jsonify

from models.leader import Leader
from middleware.decorators import rate_limit, cache_response

from timeline_data import get_timeline
from connections_data import get_connections


content_bp = Blueprint('content', __name__, url_prefix='/api')


def _published_leaders_by_id():
    return {leader.id: leader for leader in Leader.get_published()}


@content_bp.route('/timeline', methods=['GET'])
@rate_limit("60 per minute")
@cache_response(timeout=600)
def timeline():
    """Return canonical chronology of events 1917-1991."""
    return jsonify({'success': True, 'events': get_timeline()}), 200


@content_bp.route('/connections', methods=['GET'])
@rate_limit("60 per minute")
@cache_response(timeout=600)
def connections():
    """Return relationship graph enriched with leader metadata."""
    payload = get_connections()
    leaders = _published_leaders_by_id()
    nodes = []
    for lid in payload['node_ids']:
        leader = leaders.get(lid)
        if not leader:
            continue
        nodes.append({
            'id': leader.id,
            'name_ru': leader.name_ru,
            'category': leader.category,
            'portrait_url': leader.portrait_url,
        })
    return jsonify({
        'success': True,
        'nodes': nodes,
        'edges': payload['edges'],
        'link_types': payload['link_types'],
    }), 200


@content_bp.route('/quiz', methods=['GET'])
@rate_limit("60 per minute")
def quiz():
    """Build a single 'who is in the portrait?' question."""
    leaders = [l for l in Leader.get_published() if l.portrait_url]
    if len(leaders) < 4:
        return jsonify({
            'success': False,
            'error': 'Недостаточно личностей с портретами для квиза',
        }), 503

    answer = random.choice(leaders)
    distractor_pool = [l for l in leaders if l.id != answer.id]
    distractors = random.sample(distractor_pool, 3)
    options = [
        {'id': l.id, 'name_ru': l.name_ru}
        for l in distractors + [answer]
    ]
    random.shuffle(options)

    return jsonify({
        'success': True,
        'question': {
            'leader_id': answer.id,
            'portrait_url': answer.portrait_url,
            'birth_year': answer.birth_year,
            'death_year': answer.death_year,
            'category': answer.category,
            'achievements_hint': (answer.short_description or '')[:160],
        },
        'options': options,
        'answer_id': answer.id,
    }), 200
