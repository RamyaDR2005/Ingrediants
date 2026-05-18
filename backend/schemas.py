"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IngredientBase(BaseModel):
    """Base ingredient schema."""
    name: str
    code: Optional[str] = None
    category: Optional[str] = None
    risk_level: str = "low"
    description: Optional[str] = None
    safety_notes: Optional[str] = None
    profile_flags: Optional[str] = None
    source: Optional[str] = None


class IngredientCreate(IngredientBase):
    """Schema for creating ingredients."""
    pass


class IngredientResponse(IngredientBase):
    """Schema for ingredient responses."""
    id: int
    
    class Config:
        from_attributes = True


class ScanHistoryBase(BaseModel):
    """Base scan history schema."""
    product_name: str
    raw_text: str
    grade: str
    risk_score: float
    profile: Optional[str] = None
    result_json: Optional[str] = None


class ScanHistoryCreate(ScanHistoryBase):
    """Schema for creating scan history."""
    pass


class ScanHistoryResponse(ScanHistoryBase):
    """Schema for scan history responses."""
    id: int
    created_at: str
    
    class Config:
        from_attributes = True


class IngredientMatchStatsBase(BaseModel):
    """Base ingredient match stats schema."""
    ingredient_id: int
    match_count: int = 0


class IngredientMatchStatsCreate(IngredientMatchStatsBase):
    """Schema for creating match stats."""
    pass


class IngredientMatchStatsResponse(IngredientMatchStatsBase):
    """Schema for match stats responses."""
    id: int
    
    class Config:
        from_attributes = True


class ScanRequest(BaseModel):
    """Request schema for scanning ingredients."""
    image_path: str
    product_name: Optional[str] = None
    profile: Optional[str] = None


class ScanResponse(BaseModel):
    """Response schema for scan results."""
    grade: str
    risk_score: float
    ingredients: List[IngredientResponse]
    result_json: Optional[str] = None
