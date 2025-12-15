"""
Leader business logic service
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leader import Leader, Fact
from app.schemas.leader import LeaderCreate, LeaderUpdate, FactResponse
from app.db.repositories.leader_repository import LeaderRepository
from app.core.exceptions import LeaderNotFoundError
from app.services.ai_service import AIService


class LeaderService:
    """Service for leader business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = LeaderRepository(db)
        self.ai_service = AIService()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Leader]:
        """Get all leaders"""
        return await self.repository.get_all(skip=skip, limit=limit)

    async def get_by_id(self, leader_id: int) -> Leader:
        """Get leader by ID"""
        leader = await self.repository.get_by_id(leader_id)
        if not leader:
            raise LeaderNotFoundError(leader_id)
        return leader

    async def search(self, query: str) -> List[Leader]:
        """Search leaders"""
        return await self.repository.search(query)

    async def create(self, leader_data: LeaderCreate) -> Leader:
        """Create a new leader"""
        leader = Leader(**leader_data.model_dump())
        return await self.repository.create(leader)

    async def update(self, leader_id: int, leader_data: LeaderUpdate) -> Leader:
        """Update a leader"""
        leader = await self.repository.get_by_id(leader_id)
        if not leader:
            raise LeaderNotFoundError(leader_id)

        # Update only provided fields
        update_data = leader_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(leader, field, value)

        return await self.repository.update(leader)

    async def delete(self, leader_id: int) -> None:
        """Delete a leader"""
        leader = await self.repository.get_by_id(leader_id)
        if not leader:
            raise LeaderNotFoundError(leader_id)
        await self.repository.delete(leader)

    async def get_facts(self, leader_id: int) -> List[str]:
        """Get or generate facts for a leader"""
        # Check if leader exists
        leader = await self.repository.get_by_id(leader_id)
        if not leader:
            raise LeaderNotFoundError(leader_id)

        # Get existing facts from database
        facts = await self.repository.get_facts(leader_id)

        # If no facts exist, generate them using AI
        if not facts:
            generated_facts = await self.ai_service.generate_facts(leader)

            # Save generated facts to database
            for fact_text in generated_facts:
                fact = Fact(
                    leader_id=leader_id,
                    fact_text=fact_text,
                    is_verified=False,
                )
                await self.repository.create_fact(fact)

            return generated_facts

        # Return existing facts
        return [fact.fact_text for fact in facts]
