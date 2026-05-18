"""SQLAlchemy models for the ingredient scanner database."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Ingredient(Base):
    """Ingredient model storing ingredient information and risk levels."""
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=True)
    category = Column(String, nullable=True)
    risk_level = Column(String, default="low", nullable=False)  # low, medium, high
    description = Column(String, nullable=True)
    safety_notes = Column(String, nullable=True)
    profile_flags = Column(String, nullable=True)  # comma-separated: children,pregnant,elderly,allergen
    source = Column(String, nullable=True)
    
    # Relationships
    match_stats = relationship("IngredientMatchStats", back_populates="ingredient")
    scan_results = relationship("ScanHistory", back_populates="ingredients")


class ScanHistory(Base):
    """Scan history model storing past scan results."""
    __tablename__ = "scan_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)
    grade = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False)
    profile = Column(String, nullable=True)
    result_json = Column(String, nullable=True)
    created_at = Column(String, default=datetime.utcnow().isoformat(), nullable=False)
    
    # Relationships
    ingredients = relationship("Ingredient", back_populates="scan_results")


class IngredientMatchStats(Base):
    """Statistics for ingredient matches."""
    __tablename__ = "ingredient_match_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), unique=True, nullable=False)
    match_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    ingredient = relationship("Ingredient", back_populates="match_stats")
