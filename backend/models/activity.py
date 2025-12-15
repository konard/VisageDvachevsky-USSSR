"""
Activity logging model for tracking user actions
"""
from datetime import datetime
from .base import db, BaseModel


class ActivityLog(BaseModel):
    """Model for logging user activity"""

    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    leader_id = db.Column(db.Integer, db.ForeignKey('leaders.id'), nullable=True)

    action = db.Column(db.String(100), nullable=False, index=True)  # view, search, etc.
    details = db.Column(db.JSON)  # Additional details as JSON
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = db.relationship('User', back_populates='activity_logs')
    leader = db.relationship('Leader', back_populates='activity_logs')

    def __repr__(self):
        return f'<ActivityLog {self.action} at {self.timestamp}>'

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'leader_id': self.leader_id,
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def log_activity(cls, action, user_id=None, leader_id=None, details=None, ip_address=None, user_agent=None):
        """Create an activity log entry"""
        log = cls(
            action=action,
            user_id=user_id,
            leader_id=leader_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return log.save()

    @classmethod
    def get_recent_activities(cls, limit=100):
        """Get recent activity logs"""
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()

    @classmethod
    def get_user_activities(cls, user_id, limit=50):
        """Get activities for a specific user"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.timestamp.desc()).limit(limit).all()
