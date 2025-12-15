"""
Leader model for USSR historical figures
"""
from .base import db, BaseModel, TimestampMixin


class Leader(BaseModel, TimestampMixin):
    """Model representing a USSR leader"""

    __tablename__ = 'leaders'

    id = db.Column(db.Integer, primary_key=True)
    name_ru = db.Column(db.String(200), nullable=False, index=True)
    name_en = db.Column(db.String(200), nullable=False, index=True)
    birth_year = db.Column(db.Integer)
    birth_place = db.Column(db.String(200))
    death_year = db.Column(db.Integer)
    death_place = db.Column(db.String(200))
    position = db.Column(db.Text)
    achievements = db.Column(db.Text)
    biography = db.Column(db.Text)
    video_id = db.Column(db.Integer)
    portrait_url = db.Column(db.String(500))

    # New fields for enhanced platform
    slug = db.Column(db.String(200), unique=True, index=True)
    short_description = db.Column(db.Text)
    years_in_power_start = db.Column(db.Integer)
    years_in_power_end = db.Column(db.Integer)
    legacy = db.Column(db.Text)
    historical_significance = db.Column(db.Integer, default=5)  # 1-10 scale
    is_published = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)

    # Embeddings for semantic search (store as JSON)
    embedding = db.Column(db.JSON)

    # Relationships
    activity_logs = db.relationship('ActivityLog', back_populates='leader', lazy='dynamic')

    def __repr__(self):
        return f'<Leader {self.name_ru}>'

    def to_dict(self, include_relations=False):
        """Convert to dictionary with optional relations"""
        data = {
            'id': self.id,
            'name_ru': self.name_ru,
            'name_en': self.name_en,
            'slug': self.slug,
            'birth_year': self.birth_year,
            'birth_place': self.birth_place,
            'death_year': self.death_year,
            'death_place': self.death_place,
            'position': self.position,
            'achievements': self.achievements,
            'biography': self.biography,
            'short_description': self.short_description,
            'years_in_power': {
                'start': self.years_in_power_start,
                'end': self.years_in_power_end
            } if self.years_in_power_start else None,
            'legacy': self.legacy,
            'historical_significance': self.historical_significance,
            'video_id': self.video_id,
            'portrait_url': self.portrait_url,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        return data

    def increment_view_count(self):
        """Increment view counter"""
        self.view_count += 1
        db.session.commit()

    @classmethod
    def get_by_slug(cls, slug):
        """Get leader by slug"""
        return cls.query.filter_by(slug=slug).first()

    @classmethod
    def get_published(cls):
        """Get all published leaders"""
        return cls.query.filter_by(is_published=True).order_by(cls.birth_year).all()

    @classmethod
    def search(cls, query):
        """Simple text search"""
        search_pattern = f'%{query}%'
        return cls.query.filter(
            db.or_(
                cls.name_ru.like(search_pattern),
                cls.name_en.like(search_pattern),
                cls.position.like(search_pattern),
                cls.achievements.like(search_pattern)
            )
        ).filter_by(is_published=True).all()
