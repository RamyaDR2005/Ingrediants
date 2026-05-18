"""FastAPI backend for ingredient scanner."""
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.database import init_db, get_db
from backend import models
from backend import schemas
from backend.scan_service import analyze_ingredients_from_image, get_ingredient_database
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(title="Ingredient Scanner API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
    logger.info("Database initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/scan", response_model=schemas.ScanResponse)
async def scan_product(
    request: schemas.ScanRequest,
    db: Session = Depends(get_db)
):
    """Scan product image and extract ingredients."""
    try:
        # Analyze image using OCR
        result = analyze_ingredients_from_image(
            request.image_path,
            request.profile or "general"
        )
        
        # Save to database
        scan_history = models.ScanHistory(
            product_name=request.product_name or "Unknown Product",
            raw_text=result.get("raw_text", ""),
            grade=result.get("grade", "F"),
            risk_score=result.get("risk_score", 0.0),
            profile=request.profile or "general",
            result_json=json.dumps(result)
        )
        db.add(scan_history)
        db.commit()
        db.refresh(scan_history)
        
        # Return response
        return schemas.ScanResponse(
            grade=result.get("grade", "F"),
            risk_score=result.get("risk_score", 0.0),
            ingredients=[],
            result_json=json.dumps(result)
        )
    except Exception as e:
        logger.error(f"Error scanning product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ingredients", response_model=list[schemas.IngredientResponse])
async def get_ingredients(db: Session = Depends(get_db)):
    """Get all ingredients from database."""
    ingredients = db.query(models.Ingredient).all()
    return ingredients


@app.get("/api/ingredients/{ingredient_id}", response_model=schemas.IngredientResponse)
async def get_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """Get specific ingredient by ID."""
    ingredient = db.query(models.Ingredient).filter(
        models.Ingredient.id == ingredient_id
    ).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ingredient


@app.post("/api/ingredients", response_model=schemas.IngredientResponse)
async def create_ingredient(
    ingredient: schemas.IngredientCreate,
    db: Session = Depends(get_db)
):
    """Create new ingredient."""
    db_ingredient = models.Ingredient(**ingredient.dict())
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient


@app.get("/api/scan-history", response_model=list[schemas.ScanHistoryResponse])
async def get_scan_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get scan history."""
    history = db.query(models.ScanHistory).offset(skip).limit(limit).all()
    return history


@app.get("/api/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get application statistics."""
    ingredient_count = db.query(models.Ingredient).count()
    scan_count = db.query(models.ScanHistory).count()
    avg_risk_score = db.query(models.ScanHistory).avg(models.ScanHistory.risk_score)
    
    return {
        "total_ingredients": ingredient_count,
        "total_scans": scan_count,
        "average_risk_score": avg_risk_score or 0.0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
