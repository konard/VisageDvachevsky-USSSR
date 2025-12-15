"""
User and Role models for authentication and authorization
"""
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import datetime
from .base import db, BaseModel, TimestampMixin


class Role(BaseModel):
    """User roles for access control"""

    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.JSON)  # Store permissions as JSON array

    users = db.relationship('User', back_populates='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'

    def has_permission(self, permission):
        """Check if role has specific permission"""
        if not self.permissions:
            return False
        return permission in self.permissions

    @classmethod
    def get_by_name(cls, name):
        """Get role by name"""
        return cls.query.filter_by(name=name).first()


class User(UserMixin, BaseModel, TimestampMixin):
    """User model for authentication"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(200))

    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)

    # Role relationship
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    role = db.relationship('Role', back_populates='users')

    # Activity tracking
    activity_logs = db.relationship('ActivityLog', back_populates='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if password is correct"""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def has_permission(self, permission):
        """Check if user has specific permission"""
        return self.role and self.role.has_permission(permission)

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email if include_sensitive else None,
            'full_name': self.full_name,
            'role': self.role.name if self.role else None,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        return cls.query.filter_by(email=email).first()

    @classmethod
    def create_user(cls, username, email, password, role_name='user', full_name=None):
        """Create a new user"""
        role = Role.get_by_name(role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        user = cls(
            username=username,
            email=email,
            full_name=full_name,
            role=role
        )
        user.set_password(password)
        return user.save()
