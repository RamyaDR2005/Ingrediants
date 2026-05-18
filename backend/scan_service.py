"""Ingredient scanning service using PaddleOCR and image processing."""
import json
import os
from PIL import Image
from paddleocr import PaddleOCR
from rapidfuzz import fuzz
import logging

logger = logging.getLogger(__name__)

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang=['en'])

# Ingredient database (in production, load from database)
INGREDIENT_DATABASE = {
    "low_risk": [
        {"name": "water", "code": "E601", "category": "solvent"},
        {"name": "salt", "code": "E536", "category": "preservative"},
        {"name": "sugar", "code": "E621", "category": "sweetener"},
        {"name": "wheat", "code": "W001", "category": "grain"},
        {"name": "milk", "code": "M001", "category": "dairy"},
    ],
    "medium_risk": [
        {"name": "sodium benzoate", "code": "E211", "category": "preservative"},
        {"name": "potassium sorbate", "code": "E202", "category": "preservative"},
        {"name": "tartrazine", "code": "E110", "category": "colorant"},
        {"name": "allura red", "code": "E129", "category": "colorant"},
        {"name": "soy", "code": "S001", "category": "allergen"},
    ],
    "high_risk": [
        {"name": "bisphenol a", "code": "BPA", "category": "chemical"},
        {"name": "lead", "code": "PB", "category": "heavy metal"},
        {"name": "mercury", "code": "HG", "category": "heavy metal"},
        {"name": "arsenic", "code": "AS", "category": "heavy metal"},
        {"name": "GMO", "code": "GMO", "category": "genetic"},
    ]
}

RISK_TIERS = {
    "low_risk": {"score": 1, "grade": "A"},
    "medium_risk": {"score": 5, "grade": "C"},
    "high_risk": {"score": 10, "grade": "F"}
}

PROFILE_FLAGS = {
    "children": ["high sugar", "artificial colors", "artificial flavors"],
    "pregnant": ["alcohol", "high sodium", "soft cheeses"],
    "elderly": ["high sodium", "hard to chew", "high fat"],
    "allergen": ["nuts", "shellfish", "peanuts", "soy", "wheat", "milk"]
}


def enhance_for_ocr(image_path: str) -> Image.Image:
    """Enhance image for OCR using PIL."""
    try:
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Increase contrast and brightness
        from PIL import ImageEnhance
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        # Enhance brightness
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)
        
        return img
    except Exception as e:
        logger.error(f"Error enhancing image: {str(e)}")
        return Image.open(image_path)


def extract_text_from_image(image_path: str) -> str:
    """Extract text from image using PaddleOCR."""
    try:
        # Enhance image first
        enhanced_img = enhance_for_ocr(image_path)
        
        # Save enhanced image temporarily
        temp_path = "/tmp/enhanced_image.jpg"
        enhanced_img.save(temp_path)
        
        # Run OCR
        result = ocr.ocr(temp_path, cls=True)
        
        # Extract text
        extracted_text = ""
        for line in result:
            for word_info in line:
                text = word_info[1]
                extracted_text += text + " "
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        return ""


def match_ingredients(text: str, threshold: float = 70) -> dict:
    """Match extracted text against ingredient database."""
    matched_ingredients = {
        "low_risk": [],
        "medium_risk": [],
        "high_risk": []
    }
    
    words = text.lower().split()
    
    for risk_level, ingredients in INGREDIENT_DATABASE.items():
        for ingredient in ingredients:
            ingredient_name = ingredient["name"].lower()
            
            # Fuzzy matching
            for word in words:
                if fuzz.ratio(word, ingredient_name) >= threshold or \
                   fuzz.partial_ratio(word, ingredient_name) >= 80:
                    if ingredient not in matched_ingredients[risk_level]:
                        matched_ingredients[risk_level].append(ingredient)
                    break
    
    return matched_ingredients


def calculate_risk_score(matched_ingredients: dict, profile: str = "general") -> tuple[float, str]:
    """Calculate overall risk score based on matched ingredients."""
    total_score = 0
    ingredient_count = 0
    
    for risk_level, ingredients in matched_ingredients.items():
        level_score = RISK_TIERS[risk_level]["score"]
        for ingredient in ingredients:
            total_score += level_score
            ingredient_count += 1
    
    # Check profile-specific flags
    if profile in PROFILE_FLAGS:
        # Add additional scoring based on profile
        pass
    
    # Normalize score (0-10 scale)
    if ingredient_count == 0:
        normalized_score = 0.0
        grade = "A"
    else:
        normalized_score = min(10.0, (total_score / ingredient_count))
        
        if normalized_score <= 2:
            grade = "A"
        elif normalized_score <= 4:
            grade = "B"
        elif normalized_score <= 6:
            grade = "C"
        elif normalized_score <= 8:
            grade = "D"
        else:
            grade = "F"
    
    return normalized_score, grade


def analyze_ingredients_from_image(image_path: str, profile: str = "general") -> dict:
    """Main analysis function: extract and analyze ingredients from image."""
    try:
        # Extract text from image
        extracted_text = extract_text_from_image(image_path)
        logger.info(f"Extracted text: {extracted_text[:100]}...")
        
        # Match against ingredient database
        matched_ingredients = match_ingredients(extracted_text)
        
        # Calculate risk score
        risk_score, grade = calculate_risk_score(matched_ingredients, profile)
        
        # Prepare result
        result = {
            "raw_text": extracted_text,
            "matched_ingredients": matched_ingredients,
            "risk_score": risk_score,
            "grade": grade,
            "profile": profile
        }
        
        logger.info(f"Analysis complete: Grade {grade}, Risk Score {risk_score}")
        return result
    except Exception as e:
        logger.error(f"Error in ingredient analysis: {str(e)}")
        return {
            "raw_text": "",
            "matched_ingredients": {"low_risk": [], "medium_risk": [], "high_risk": []},
            "risk_score": 0.0,
            "grade": "F",
            "error": str(e)
        }


def get_ingredient_database() -> dict:
    """Get the ingredient database."""
    return INGREDIENT_DATABASE
