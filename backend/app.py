"""
Main Flask application for USSR Leaders Platform
"""
import os
import json
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from database import Database
from ai_service import AIService
from chat_service import ChatService, OllamaUnavailableError
from timeline_data import get_timeline
from connections_data import get_connections

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Initialize database and services
db = Database()
ai_service = AIService()
chat_service = ChatService()

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/leaders')
def get_leaders():
    """Get all USSR leaders"""
    leaders = db.get_all_leaders()
    return jsonify(leaders)

@app.route('/api/leaders/<int:leader_id>')
def get_leader(leader_id):
    """Get specific leader by ID"""
    leader = db.get_leader_by_id(leader_id)
    if leader:
        return jsonify(leader)
    return jsonify({'error': 'Leader not found'}), 404

@app.route('/api/leaders/<int:leader_id>/facts')
def get_leader_facts(leader_id):
    """Get AI-generated facts about a leader"""
    leader = db.get_leader_by_id(leader_id)
    if not leader:
        return jsonify({'error': 'Leader not found'}), 404

    facts = ai_service.generate_facts(leader)
    return jsonify({'facts': facts})

@app.route('/api/search')
def search():
    """Search leaders using semantic search"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400

    results = ai_service.semantic_search(query, db.get_all_leaders())
    return jsonify({'results': results})

@app.route('/api/chat/health')
def chat_health():
    """Report whether the configured Ollama backend is reachable."""
    return jsonify(chat_service.health())


@app.route('/api/leaders/<int:leader_id>/chat', methods=['POST'])
def chat_with_leader(leader_id):
    """Have a constrained dialogue with a historical figure via Ollama."""
    leader = db.get_leader_by_id(leader_id)
    if not leader:
        return jsonify({'error': 'Leader not found'}), 404

    payload = request.get_json(silent=True) or {}
    message = payload.get('message', '')
    history = payload.get('history', [])

    if not isinstance(message, str) or not message.strip():
        return jsonify({'error': 'Поле "message" обязательно'}), 400
    if not isinstance(history, list):
        return jsonify({'error': 'Поле "history" должно быть массивом'}), 400

    try:
        result = chat_service.chat(leader, message, history)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except OllamaUnavailableError as exc:
        return jsonify({
            'error': str(exc),
            'available': False,
        }), 503

    return jsonify({
        'reply': result['reply'],
        'history': result['history'],
        'model': result['model'],
        'off_topic': result.get('off_topic', False),
        'leader': {
            'id': leader['id'],
            'name_ru': leader['name_ru'],
        },
    })


@app.route('/api/timeline')
def get_timeline_events():
    """Return chronology of significant events 1917-1991."""
    return jsonify({'events': get_timeline()})


@app.route('/api/connections')
def get_connections_graph():
    """Return the connections graph between historical figures."""
    payload = get_connections()
    leaders = {l['id']: l for l in db.get_all_leaders()}
    nodes = [
        {
            'id': lid,
            'name_ru': leaders[lid]['name_ru'],
            'category': leaders[lid].get('category'),
            'portrait_url': leaders[lid].get('portrait_url'),
        }
        for lid in payload['node_ids']
        if lid in leaders
    ]
    return jsonify({
        'nodes': nodes,
        'edges': payload['edges'],
        'link_types': payload['link_types'],
    })


@app.route('/api/quiz')
def get_quiz_question():
    """Build a single 'who is in the portrait' question from the leader roster."""
    import random
    leaders = [l for l in db.get_all_leaders() if l.get('portrait_url')]
    if len(leaders) < 4:
        return jsonify({'error': 'Недостаточно личностей для квиза'}), 503

    answer = random.choice(leaders)
    distractor_pool = [l for l in leaders if l['id'] != answer['id']]
    distractors = random.sample(distractor_pool, 3)
    options = [
        {'id': l['id'], 'name_ru': l['name_ru']}
        for l in distractors + [answer]
    ]
    random.shuffle(options)

    return jsonify({
        'question': {
            'leader_id': answer['id'],
            'portrait_url': answer['portrait_url'],
            'birth_year': answer.get('birth_year'),
            'death_year': answer.get('death_year'),
            'category': answer.get('category'),
            'achievements_hint': (answer.get('short_description') or '')[:160],
        },
        'options': options,
        'answer_id': answer['id'],
    })


@app.route('/api/videos/available')
def get_available_videos():
    """Return list of video IDs that have a corresponding mp4 file in the videos/ directory."""
    videos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'videos')
    available = []
    if os.path.isdir(videos_dir):
        for entry in os.listdir(videos_dir):
            if entry.lower().endswith('.mp4'):
                stem = entry[:-4]
                try:
                    available.append(int(stem))
                except ValueError:
                    pass
    return jsonify({'available': sorted(available)})


@app.route('/videos/<path:filename>')
def serve_video(filename):
    """Serve video files"""
    videos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'videos')
    return send_from_directory(videos_dir, filename)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize database with leaders data
    db.initialize_data()

    # Run the application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
