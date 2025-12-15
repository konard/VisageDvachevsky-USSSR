"""
Leader repository for database operations
"""
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.leader import Leader, Fact


class LeaderRepository:
    """Repository for leader database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Leader]:
        """Get all leaders with pagination"""
        result = await self.db.execute(
            select(Leader)
            .offset(skip)
            .limit(limit)
            .order_by(Leader.birth_year)
        )
        return list(result.scalars().all())

    async def get_by_id(self, leader_id: int) -> Optional[Leader]:
        """Get leader by ID"""
        result = await self.db.execute(
            select(Leader).where(Leader.id == leader_id)
        )
        return result.scalar_one_or_none()

    async def get_with_facts(self, leader_id: int) -> Optional[Leader]:
        """Get leader with facts"""
        result = await self.db.execute(
            select(Leader)
            .options(selectinload(Leader.facts))
            .where(Leader.id == leader_id)
        )
        return result.scalar_one_or_none()

    async def search(self, query: str) -> List[Leader]:
        """Search leaders by name or position"""
        search_pattern = f"%{query}%"
        result = await self.db.execute(
            select(Leader).where(
                or_(
                    Leader.name_ru.ilike(search_pattern),
                    Leader.name_en.ilike(search_pattern),
                    Leader.position.ilike(search_pattern),
                    Leader.achievements.ilike(search_pattern),
                )
            )
        )
        return list(result.scalars().all())

    async def create(self, leader: Leader) -> Leader:
        """Create a new leader"""
        self.db.add(leader)
        await self.db.flush()
        await self.db.refresh(leader)
        return leader

    async def update(self, leader: Leader) -> Leader:
        """Update a leader"""
        await self.db.flush()
        await self.db.refresh(leader)
        return leader

    async def delete(self, leader: Leader) -> None:
        """Delete a leader"""
        await self.db.delete(leader)
        await self.db.flush()

    async def get_facts(self, leader_id: int) -> List[Fact]:
        """Get facts for a leader"""
        result = await self.db.execute(
            select(Fact)
            .where(Fact.leader_id == leader_id)
            .order_by(Fact.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_fact(self, fact: Fact) -> Fact:
        """Create a new fact"""
        self.db.add(fact)
        await self.db.flush()
        await self.db.refresh(fact)
        return fact
