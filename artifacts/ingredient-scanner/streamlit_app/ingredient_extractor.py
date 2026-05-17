"""
Ingredient section extractor + OCR noise cleaner + fuzzy validator.

Pipeline:
  full OCR text
    → extract_ingredient_section()   – isolate just the ingredient list
    → clean_ocr_noise()              – strip phone/email/weight/nutrition noise
    → tokenize_and_validate()        – split on delimiters, reject garbage tokens
    → fuzzy_match_token()            – match each token against DB
"""

import re
import unicodedata
from difflib import SequenceMatcher

# ── Section boundary keywords ─────────────────────────────────────────────────

INGREDIENT_START = [
    "ingredients", "ingredient list", "contains", "composition",
    "ingr.", "ingr:", "ingredients:", "contents", "made with",
    "made from", "formulated with",
]

INGREDIENT_STOP = [
    "nutrition facts", "nutrition information", "nutritional information",
    "nutritional value", "nutritional values", "nutritional content",
    "serving size", "servings per container", "amount per serving",
    "calories", "total fat", "saturated fat", "trans fat",
    "cholesterol", "total carbohydrate", "dietary fiber", "total sugars",
    "added sugars", "protein", "vitamin d", "calcium", "iron", "potassium",
    "% daily value", "daily value",
    "storage", "store in", "how to store", "keep refrigerated",
    "manufactured by", "manufactured in", "packed by", "packed in",
    "distributed by", "imported by", "marketed by",
    "fssai", "fssai no", "lic. no", "license no",
    "best before", "use before", "expiry", "mfg date", "mfg. date",
    "net wt", "net weight", "net content", "net vol",
    "customer care", "consumer care", "helpline", "toll free",
    "barcode", "batch no", "batch number", "lot no",
    "directions", "usage", "how to use", "allergen warning",
    "warning:", "caution:",
    "address:", "registered office", "corporate office",
    "website:", "www.", "email:", "contact us",
    "country of origin", "product of",
]

# ── Noise regex patterns ──────────────────────────────────────────────────────

_EMAIL     = re.compile(r'\b[\w.+\-]+@[\w\-]+\.\w{2,}\b', re.I)
_PHONE     = re.compile(r'(\+?\d[\d\s\-().]{7,}\d)')
_BARCODE   = re.compile(r'\b\d{8,}\b')
_KCAL      = re.compile(r'\b\d+\.?\d*\s*(kcal|cal|kj|calories?)\b', re.I)
_WEIGHT_V  = re.compile(r'\b\d+\.?\d*\s*(g|mg|mcg|ml|kg|oz|lb|iu|%)\b', re.I)
_FRACTION  = re.compile(r'\b\d+\.?\d*/\d+\b')
_PURE_NUM  = re.compile(r'^\s*[\d\s.,]+\s*$')
_URL       = re.compile(r'https?://\S+|www\.\S+', re.I)
_PIN_CODE  = re.compile(r'\b\d{6}\b')

ADDRESS_WORDS = {
    "street", "road", "avenue", "lane", "nagar", "colony",
    "floor", "building", "plot", "survey", "village", "district",
    "pin", "state", "phase", "sector", "block", "industrial",
    "estate", "area", "layout", "cross", "main", "near",
}

# Nutrition label column headers / values to reject outright
NUTRITION_NOISE = {
    "energy", "fat", "carbohydrate", "carbohydrates", "fibre", "fiber",
    "sugars", "sugar", "protein", "sodium", "calcium", "iron",
    "vitamin", "potassium", "cholesterol", "magnesium", "phosphorus",
    "per 100g", "per serving", "per 100 ml",
    "daily value", "dv", "rda",
}

# Words that appear in addresses, not ingredient lists
FSSAI_LIKE = {"fssai", "lic", "license", "no.", "reg", "registration"}


def _normalise(s: str) -> str:
    """Unicode-normalise, lowercase, strip extra whitespace."""
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", " ", s).strip().lower()


# ── 1. Extract ingredient section ────────────────────────────────────────────

def extract_ingredient_section(full_ocr_text: str) -> dict:
    """
    Find the ingredient block inside a raw OCR dump.

    Returns:
        section          – the isolated ingredient text (best guess)
        start_found      – whether a start keyword was detected
        start_keyword    – which keyword triggered the start
        stop_keyword     – which keyword triggered the stop (or None)
        ocr_confidence   – rough confidence 0–1 based on how cleanly we bounded it
        full_text_used   – True if no boundaries found (fallback to full text)
    """
    lines = full_ocr_text.splitlines()
    norm_lines = [_normalise(l) for l in lines]

    start_idx = None
    start_kw  = None
    stop_idx  = None
    stop_kw   = None

    for i, nl in enumerate(norm_lines):
        if start_idx is None:
            for kw in INGREDIENT_START:
                if kw in nl:
                    start_idx = i
                    start_kw  = kw
                    break
        else:
            for kw in INGREDIENT_STOP:
                if kw in nl:
                    stop_idx = i
                    stop_kw  = kw
                    break
            if stop_idx is not None:
                break

    start_found = start_idx is not None

    if start_found and stop_idx is not None:
        section_lines = lines[start_idx : stop_idx]
        confidence = 0.95
    elif start_found:
        section_lines = lines[start_idx:]
        confidence = 0.75
    else:
        section_lines = lines
        confidence = 0.40

    # Strip the start-keyword line itself if it contains ONLY the keyword
    if section_lines and start_kw:
        first = _normalise(section_lines[0])
        if first.strip(": ") in INGREDIENT_START:
            section_lines = section_lines[1:]
        elif first.startswith(start_kw):
            # Remove the keyword prefix and keep the rest of the line
            section_lines[0] = re.sub(
                re.escape(start_kw) + r"[:\s]*", "", section_lines[0], count=1, flags=re.I
            )

    section = "\n".join(section_lines).strip()

    return {
        "section": section,
        "start_found": start_found,
        "start_keyword": start_kw,
        "stop_keyword": stop_kw,
        "ocr_confidence": round(confidence, 2),
        "full_text_used": not start_found,
    }


# ── 2. Noise removal ──────────────────────────────────────────────────────────

def clean_ocr_noise(raw_section: str) -> dict:
    """
    Remove non-ingredient noise from the extracted section.

    Returns:
        cleaned       – cleaned text
        removed       – list of (token, reason) pairs for transparency
        removal_stats – count per category
    """
    removed = []
    stats   = {
        "emails": 0, "phones": 0, "barcodes": 0,
        "weights": 0, "pure_numbers": 0, "urls": 0,
        "nutrition_values": 0, "addresses": 0, "misc": 0,
    }

    text = raw_section

    # Strip emails
    for m in _EMAIL.finditer(text):
        removed.append((m.group(), "email"))
        stats["emails"] += 1
    text = _EMAIL.sub(" ", text)

    # Strip URLs
    for m in _URL.finditer(text):
        removed.append((m.group(), "url"))
        stats["urls"] += 1
    text = _URL.sub(" ", text)

    # Strip barcodes (8+ digit runs)
    for m in _BARCODE.finditer(text):
        removed.append((m.group(), "barcode/number"))
        stats["barcodes"] += 1
    text = _BARCODE.sub(" ", text)

    # Strip phone numbers
    for m in _PHONE.finditer(text):
        removed.append((m.group(), "phone number"))
        stats["phones"] += 1
    text = _PHONE.sub(" ", text)

    # Strip kcal/calorie values
    for m in _KCAL.finditer(text):
        removed.append((m.group(), "calorie/energy value"))
        stats["nutrition_values"] += 1
    text = _KCAL.sub(" ", text)

    # Strip weight/volume quantities attached to numbers
    for m in _WEIGHT_V.finditer(text):
        removed.append((m.group(), "weight/volume quantity"))
        stats["weights"] += 1
    text = _WEIGHT_V.sub(" ", text)

    # Strip fractions (3/4, 1/2 etc.)
    text = _FRACTION.sub(" ", text)

    # Strip pin codes
    text = _PIN_CODE.sub(" ", text)

    # Normalise whitespace
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Line-level filter: drop lines that look like addresses or nutrition rows
    filtered_lines = []
    for line in text.splitlines():
        nl = _normalise(line)
        word_set = set(nl.split())
        # Address check: ≥2 address indicator words on same line
        addr_hits = word_set & ADDRESS_WORDS
        if len(addr_hits) >= 2:
            removed.append((line.strip(), "address line"))
            stats["addresses"] += 1
            continue
        # Nutrition table row: pure number or known nutrition column header
        if _PURE_NUM.match(nl):
            removed.append((line.strip(), "pure number row"))
            stats["pure_numbers"] += 1
            continue
        if nl.strip() in NUTRITION_NOISE:
            removed.append((line.strip(), "nutrition header"))
            stats["nutrition_values"] += 1
            continue
        filtered_lines.append(line)

    cleaned = "\n".join(filtered_lines).strip()

    return {
        "cleaned": cleaned,
        "removed": removed,
        "removal_stats": stats,
        "noise_count": len(removed),
    }


# ── 3. Token validation ───────────────────────────────────────────────────────

_BROKEN_WORD = re.compile(r'^[^a-zA-Z]*$')   # entirely non-alpha
_TOO_SHORT   = re.compile(r'^.{1,2}$')

COMMON_NOISE_TOKENS = {
    "and", "the", "of", "in", "to", "a", "an", "by", "as",
    "for", "is", "are", "was", "be", "at", "or", "no",
    "per", "see", "use", "may", "not", "with",
    # OCR artefacts
    "|", "—", "–", "·", "•", "*", "#", "@", "~",
    "n/a", "na", "nil", "none",
}


def is_valid_ingredient_token(token: str) -> tuple[bool, str]:
    """
    Return (True, '') if the token looks like a real ingredient name,
    or (False, reason) if it should be rejected.
    """
    t = token.strip()
    if not t:
        return False, "empty"
    if len(t) < 3:
        return False, "too short"
    if _BROKEN_WORD.match(t):
        return False, "no alphabetic characters"
    if _PURE_NUM.match(t):
        return False, "pure number"
    if _KCAL.search(t):
        return False, "calorie/energy value"
    if _BARCODE.search(t):
        return False, "barcode"
    if _EMAIL.search(t):
        return False, "email"
    if _PHONE.search(t):
        return False, "phone number"

    # Reject if less than 2 alpha chars
    alpha_count = sum(1 for c in t if c.isalpha())
    if alpha_count < 2:
        return False, "fewer than 2 alphabetic characters"

    # Reject if >70% of characters are digits/symbols
    non_alpha = sum(1 for c in t if not c.isalpha())
    if len(t) > 3 and non_alpha / len(t) > 0.70:
        return False, "mostly non-alphabetic"

    # Reject known noise tokens
    if _normalise(t) in COMMON_NOISE_TOKENS:
        return False, "common noise word"

    # Reject tokens that match nutrition noise exactly
    if _normalise(t).strip(":% ") in NUTRITION_NOISE:
        return False, "nutrition table header"

    return True, ""


# ── 4. Fuzzy match ────────────────────────────────────────────────────────────

def fuzzy_match_token(
    token: str,
    db_names: list[str],          # list of known ingredient names (lowercase)
    db_map:  dict[str, dict],     # name → ingredient dict
    threshold: int = 72,
) -> dict:
    """
    Match a cleaned token against the ingredient database using
    sequence matching (no external library required, but rapidfuzz
    is used if available for speed).
    """
    t_lower = _normalise(token)
    best_name  = None
    best_score = 0.0

    try:
        from rapidfuzz import process, fuzz
        result = process.extractOne(
            t_lower, db_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=threshold,
        )
        if result:
            best_name  = result[0]
            best_score = result[1] / 100.0
    except ImportError:
        # Fall back to difflib
        for name in db_names:
            score = SequenceMatcher(None, t_lower, name).ratio() * 100
            if score > best_score:
                best_score = score
                best_name  = name
        if best_score < threshold:
            best_name  = None
            best_score = 0.0
        else:
            best_score /= 100.0

    if best_name and best_name in db_map:
        return {
            "matched": True,
            "ingredient": db_map[best_name],
            "match_name": best_name,
            "confidence": round(best_score, 3),
        }
    return {
        "matched": False,
        "ingredient": None,
        "match_name": None,
        "confidence": 0.0,
    }


# ── 5. Full tokeniser ─────────────────────────────────────────────────────────

_DELIMITERS = re.compile(r'[,;\n•·|/\\]+')


def tokenize_cleaned(cleaned_text: str) -> list[str]:
    """Split cleaned text on ingredient-list delimiters."""
    parts = _DELIMITERS.split(cleaned_text)
    tokens = []
    for p in parts:
        t = p.strip().strip("()[]{}\"' \t")
        # Handle parenthetical sub-ingredients: "Wheat Flour (contains Gluten)"
        # Keep the parent, add the sub-items too
        t = re.sub(r"\(([^)]+)\)", lambda m: ", " + m.group(1), t)
        sub = _DELIMITERS.split(t)
        for s in sub:
            s = s.strip().strip("()[]{}\"' \t")
            if s:
                tokens.append(s)
    return tokens


# ── 6. Build DB lookup structures ─────────────────────────────────────────────

def build_db_index(all_ingredients: list[dict]) -> tuple[list[str], dict]:
    """
    Given rows from the DB, return:
      db_names – lowercase name list for fuzzy search
      db_map   – lowercase name → row dict
    """
    db_names = []
    db_map   = {}
    for ing in all_ingredients:
        key = _normalise(ing["name"])
        db_names.append(key)
        db_map[key] = ing
        # Also index by code if present
        if ing.get("code"):
            code_key = _normalise(ing["code"])
            if code_key not in db_map:
                db_names.append(code_key)
                db_map[code_key] = ing
    return db_names, db_map
