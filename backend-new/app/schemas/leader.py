"""
Leader Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class LeaderBase(BaseModel):
    """Base leader schema"""
    name_ru: str = Field(..., min_length=1, max_length=255)
    name_en: str = Field(..., min_length=1, max_length=255)
    birth_year: int = Field(..., ge=1800, le=2100)
    birth_place: str = Field(..., min_length=1, max_length=255)
    death_year: Optional[int] = Field(None, ge=1800, le=2100)
    death_place: Optional[str] = Field(None, max_length=255)
    position: str = Field(..., min_length=1, max_length=500)
    achievements: str = Field(..., min_length=1)
    biography: Optional[str] = None
    video_id: int = Field(..., ge=1)
    portrait_url: Optional[str] = Field(None, max_length=500)


class LeaderCreate(LeaderBase):
    """Schema for creating a leader"""
    pass


class LeaderUpdate(BaseModel):
    """Schema for updating a leader"""
    name_ru: Optional[str] = Field(None, min_length=1, max_length=255)
    name_en: Optional[str] = Field(None, min_length=1, max_length=255)
    birth_year: Optional[int] = Field(None, ge=1800, le=2100)
    birth_place: Optional[str] = Field(None, min_length=1, max_length=255)
    death_year: Optional[int] = Field(None, ge=1800, le=2100)
    death_place: Optional[str] = Field(None, max_length=255)
    position: Optional[str] = Field(None, min_length=1, max_length=500)
    achievements: Optional[str] = Field(None, min_length=1)
    biography: Optional[str] = None
    video_id: Optional[int] = Field(None, ge=1)
    portrait_url: Optional[str] = Field(None, max_length=500)


class LeaderResponse(LeaderBase):
    """Schema for leader response"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FactBase(BaseModel):
    """Base fact schema"""
    fact_text: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=100)


class FactCreate(FactBase):
    """Schema for creating a fact"""
    leader_id: int


class FactResponse(FactBase):
    """Schema for fact response"""
    id: int
    leader_id: int
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeaderWithFactsResponse(LeaderResponse):
    """Schema for leader with facts"""
    facts: list[FactResponse] = []

    model_config = ConfigDict(from_attributes=True)


class LeaderSearchResponse(BaseModel):
    """Schema for search results"""
    results: list[LeaderResponse]
    total: int
