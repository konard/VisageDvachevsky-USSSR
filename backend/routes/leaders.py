"""
Leaders API routes
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_required
from ..models.leader import Leader
from ..models.activity import ActivityLog
from ..services.ai_service import EnhancedAIService
from ..middleware.decorators import rate_limit, cache_response
import logging

logger = logging.getLogger(__name__)

leaders_bp = Blueprint('leaders', __name__, url_prefix='/api/leaders')


@leaders_bp.route('/', methods=['GET'])
@rate_limit("30 per minute")
@cache_response(timeout=300)
def get_leaders():
    """Get all published leaders"""
    try:
        leaders = Leader.get_published()
        return jsonify({
            'success': True,
            'count': len(leaders),
            'data': [leader.to_dict() for leader in leaders]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching leaders: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch leaders'
        }), 500


@leaders_bp.route('/<int:leader_id>', methods=['GET'])
@rate_limit("60 per minute")
@cache_response(timeout=300)
def get_leader(leader_id):
    """Get specific leader by ID"""
    try:
        leader = Leader.get_by_id(leader_id)

        if not leader or not leader.is_published:
            return jsonify({
                'success': False,
                'error': 'Leader not found'
            }), 404

        # Increment view count
        leader.increment_view_count()

        # Log activity
        try:
            user_id = get_jwt_identity() if request.headers.get('Authorization') else None
            ActivityLog.log_activity(
                action='view_leader',
                user_id=user_id,
                leader_id=leader_id,
                details={'name': leader.name_ru},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        except:
            pass  # Don't fail if activity logging fails

        return jsonify({
            'success': True,
            'data': leader.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error fetching leader {leader_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch leader'
        }), 500


@leaders_bp.route('/<int:leader_id>/facts', methods=['GET'])
@rate_limit("20 per minute")
@cache_response(timeout=600)
def get_leader_facts(leader_id):
    """Get AI-generated facts about a leader"""
    try:
        leader = Leader.get_by_id(leader_id)

        if not leader or not leader.is_published:
            return jsonify({
                'success': False,
                'error': 'Leader not found'
            }), 404

        # Get number of facts from query params
        count = request.args.get('count', 3, type=int)
        count = min(count, 10)  # Max 10 facts

        # Generate facts using AI service
        ai_service = EnhancedAIService(current_app.config)
        facts = ai_service.generate_facts(leader.to_dict(), count=count)

        return jsonify({
            'success': True,
            'data': {
                'leader_id': leader_id,
                'leader_name': leader.name_ru,
                'facts': facts
            }
        }), 200

    except Exception as e:
        logger.error(f"Error generating facts for leader {leader_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate facts'
        }), 500


@leaders_bp.route('/search', methods=['GET'])
@rate_limit("30 per minute")
def search_leaders():
    """Search leaders using semantic search"""
    try:
        query = request.args.get('q', '').strip()

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter required'
            }), 400

        if len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Query must be at least 2 characters'
            }), 400

        # Log search activity
        try:
            user_id = get_jwt_identity() if request.headers.get('Authorization') else None
            ActivityLog.log_activity(
                action='search',
                user_id=user_id,
                details={'query': query},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        except:
            pass

        # Perform search
        leaders = Leader.get_published()
        ai_service = EnhancedAIService(current_app.config)

        leaders_dict = [leader.to_dict() for leader in leaders]
        results = ai_service.semantic_search(query, leaders_dict)

        return jsonify({
            'success': True,
            'query': query,
            'count': len(results),
            'data': results
        }), 200

    except Exception as e:
        logger.error(f"Error searching leaders: {e}")
        return jsonify({
            'success': False,
            'error': 'Search failed'
        }), 500


@leaders_bp.route('/<int:leader_id>/recommendations', methods=['GET'])
@rate_limit("20 per minute")
@cache_response(timeout=600)
def get_recommendations(leader_id):
    """Get recommended similar leaders"""
    try:
        leader = Leader.get_by_id(leader_id)

        if not leader or not leader.is_published:
            return jsonify({
                'success': False,
                'error': 'Leader not found'
            }), 404

        count = request.args.get('count', 3, type=int)
        count = min(count, 5)  # Max 5 recommendations

        all_leaders = Leader.get_published()
        ai_service = EnhancedAIService(current_app.config)

        leaders_dict = [l.to_dict() for l in all_leaders]
        recommendations = ai_service.get_recommendations(
            leader.to_dict(),
            leaders_dict,
            count=count
        )

        return jsonify({
            'success': True,
            'data': recommendations
        }), 200

    except Exception as e:
        logger.error(f"Error getting recommendations for leader {leader_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get recommendations'
        }), 500


@leaders_bp.route('/', methods=['POST'])
@jwt_required()
@rate_limit("10 per hour")
def create_leader():
    """Create a new leader (admin only)"""
    from ..middleware.permissions import admin_required

    try:
        # Check admin permission
        current_user_id = get_jwt_identity()
        from ..services.auth_service import AuthService
        user = AuthService.get_user_by_id(current_user_id)

        if not user or not user.has_permission('create_leaders'):
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403

        data = request.get_json()

        # Validate required fields
        required_fields = ['name_ru', 'name_en']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Create leader
        leader = Leader(
            name_ru=data['name_ru'],
            name_en=data['name_en'],
            slug=data.get('slug'),
            birth_year=data.get('birth_year'),
            birth_place=data.get('birth_place'),
            death_year=data.get('death_year'),
            death_place=data.get('death_place'),
            position=data.get('position'),
            achievements=data.get('achievements'),
            biography=data.get('biography'),
            short_description=data.get('short_description'),
            years_in_power_start=data.get('years_in_power_start'),
            years_in_power_end=data.get('years_in_power_end'),
            legacy=data.get('legacy'),
            historical_significance=data.get('historical_significance', 5),
            video_id=data.get('video_id'),
            portrait_url=data.get('portrait_url'),
            is_published=data.get('is_published', False)
        )

        leader.save()

        logger.info(f"Leader created: {leader.name_ru} by user {user.username}")

        return jsonify({
            'success': True,
            'data': leader.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Error creating leader: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create leader'
        }), 500
