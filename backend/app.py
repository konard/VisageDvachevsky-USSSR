"""
Main Flask application for USSR Leaders Platform
"""
import os
import json
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from database import Database
from ai_service import AIService

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Initialize database and AI service
db = Database()
ai_service = AIService()

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
