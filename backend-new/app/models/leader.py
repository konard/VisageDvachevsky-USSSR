"""
Leader database model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Leader(Base):
    """Leader model"""
    __tablename__ = "leaders"

    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=False)
    birth_year = Column(Integer, nullable=False)
    birth_place = Column(String(255), nullable=False)
    death_year = Column(Integer, nullable=True)
    death_place = Column(String(255), nullable=True)
    position = Column(String(500), nullable=False)
    achievements = Column(Text, nullable=False)
    biography = Column(Text, nullable=True)
    video_id = Column(Integer, nullable=False)
    portrait_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    facts = relationship("Fact", back_populates="leader", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Leader {self.name_en} ({self.birth_year}-{self.death_year or 'present'})>"


class Fact(Base):
    """Fact model for AI-generated facts"""
    __tablename__ = "facts"

    id = Column(Integer, primary_key=True, index=True)
    leader_id = Column(Integer, ForeignKey("leaders.id", ondelete="CASCADE"), nullable=False)
    fact_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    is_verified = Column(Integer, default=0, nullable=False)  # Using Integer as boolean
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    leader = relationship("Leader", back_populates="facts")

    def __repr__(self) -> str:
        return f"<Fact for Leader {self.leader_id}>"
