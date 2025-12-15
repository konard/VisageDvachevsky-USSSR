"""
Analytics API routes
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.activity import ActivityLog
from ..models.leader import Leader
from ..services.auth_service import AuthService
from ..middleware.decorators import rate_limit
import logging

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/popular', methods=['GET'])
@rate_limit("20 per minute")
def get_popular_leaders():
    """Get most popular leaders by view count"""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # Max 50

        leaders = Leader.query.filter_by(is_published=True)\
            .order_by(Leader.view_count.desc())\
            .limit(limit).all()

        return jsonify({
            'success': True,
            'data': [leader.to_dict() for leader in leaders]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching popular leaders: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch popular leaders'
        }), 500


@analytics_bp.route('/recent-activity', methods=['GET'])
@jwt_required()
@rate_limit("10 per minute")
def get_recent_activity():
    """Get recent activity logs (admin only)"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)

        if not user or not user.has_permission('view_analytics'):
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403

        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 500)

        activities = ActivityLog.get_recent_activities(limit=limit)

        return jsonify({
            'success': True,
            'count': len(activities),
            'data': [activity.to_dict() for activity in activities]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch activity'
        }), 500
