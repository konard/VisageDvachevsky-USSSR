"""
Leader API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.schemas.leader import (
    LeaderResponse,
    LeaderCreate,
    LeaderUpdate,
    FactResponse,
    LeaderSearchResponse,
)
from app.services.leader_service import LeaderService
from app.core.exceptions import LeaderNotFoundError

router = APIRouter()


@router.get("", response_model=List[LeaderResponse])
async def get_leaders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all USSR leaders with pagination
    """
    service = LeaderService(db)
    leaders = await service.get_all(skip=skip, limit=limit)
    return leaders


@router.get("/{leader_id}", response_model=LeaderResponse)
async def get_leader(
    leader_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific leader by ID
    """
    service = LeaderService(db)
    try:
        leader = await service.get_by_id(leader_id)
        return leader
    except LeaderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leader with id {leader_id} not found",
        )


@router.get("/{leader_id}/facts", response_model=dict)
async def get_leader_facts(
    leader_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-generated facts about a leader
    """
    service = LeaderService(db)
    try:
        facts = await service.get_facts(leader_id)
        return {"facts": facts}
    except LeaderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leader with id {leader_id} not found",
        )


@router.get("/search", response_model=LeaderSearchResponse)
async def search_leaders(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Search leaders by query
    """
    service = LeaderService(db)
    results = await service.search(q)
    return {"results": results, "total": len(results)}


@router.post("", response_model=LeaderResponse, status_code=status.HTTP_201_CREATED)
async def create_leader(
    leader_data: LeaderCreate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_admin_user),  # TODO: Add when auth is ready
):
    """
    Create a new leader (Admin only)
    """
    service = LeaderService(db)
    leader = await service.create(leader_data)
    return leader


@router.put("/{leader_id}", response_model=LeaderResponse)
async def update_leader(
    leader_id: int,
    leader_data: LeaderUpdate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_editor_user),  # TODO: Add when auth is ready
):
    """
    Update a leader (Editor/Admin only)
    """
    service = LeaderService(db)
    try:
        leader = await service.update(leader_id, leader_data)
        return leader
    except LeaderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leader with id {leader_id} not found",
        )


@router.delete("/{leader_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_leader(
    leader_id: int,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_admin_user),  # TODO: Add when auth is ready
):
    """
    Delete a leader (Admin only)
    """
    service = LeaderService(db)
    try:
        await service.delete(leader_id)
    except LeaderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leader with id {leader_id} not found",
        )
