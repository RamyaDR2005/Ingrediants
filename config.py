"""
Configuration file for SafeScan application
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ingredient_scanner.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_TITLE = "SafeScan - Ingredient Scanner API"
API_VERSION = "1.0.0"

# Streamlit
STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "0.0.0.0")
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

# OCR
PADDLE_OCR_LANG = os.getenv("PADDLE_OCR_LANG", "en")
OCR_USE_ANGLE_CLS = True
OCR_THRESHOLD = float(os.getenv("OCR_THRESHOLD", "0.7"))

# Ingredient Matching
INGREDIENT_MATCH_THRESHOLD = int(os.getenv("INGREDIENT_MATCH_THRESHOLD", "70"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Profiles
PROFILES = ["general", "children", "pregnant", "elderly", "allergen"]

# Risk Levels
RISK_LEVELS = {
    "low": 1,
    "medium": 5,
    "high": 10
}

# Grades
GRADE_MAPPING = {
    0: "A",
    2: "B",
    4: "C",
    6: "D",
    8: "F"
}
