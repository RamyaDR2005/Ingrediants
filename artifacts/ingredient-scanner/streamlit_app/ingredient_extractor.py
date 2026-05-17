"""
SafeScan — Ingredient extraction pipeline (v3)

Stages:
  1. reconstruct_lines_from_bbox()   – merge OCR tokens into spatial lines
  2. extract_ingredient_section()    – keyword boundary detection on lines
  3. clean_ocr_noise()               – strip phones/emails/barcodes/weights
  4. tokenize_ingredient_section()   – depth-aware comma splitting
  5. is_valid_ingredient_token()     – reject garbage tokens
  6. fuzzy_match_strict()            – DB lookup with anti-hallucination guard
"""

import re
import unicodedata
from difflib import SequenceMatcher

# ── Unicode normaliser ────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", " ", s).strip().lower()


# ══════════════════════════════════════════════════════════════════════════════
# 1. Reconstruct spatial lines from OCR bounding boxes
# ══════════════════════════════════════════════════════════════════════════════

def _bbox_ycenter(bbox) -> float:
    ys = [p[1] for p in bbox]
    return sum(ys) / len(ys)

def _bbox_xcenter(bbox) -> float:
    xs = [p[0] for p in bbox]
    return sum(xs) / len(xs)

def _bbox_height(bbox) -> float:
    ys = [p[1] for p in bbox]
    return max(ys) - min(ys)


def reconstruct_lines_from_bbox(
    ocr_results: list,
    min_confidence: float = 0.35,
    line_merge_ratio: float = 0.55,
) -> dict:
    """
    Group OCR (bbox, text, confidence) triples by vertical position into lines.

    Tokens on the same horizontal band are sorted left-to-right and joined with
    spaces, preserving multi-word phrases ("natural flavors", "palm oil" etc.).

    Returns:
      full_text   – newline-separated lines (correct input for section extraction)
      lines       – list of {"text", "y_center", "mean_conf", "token_count"}
      mean_conf   – overall mean OCR confidence
      total_tokens, rejected_low_conf
    """
    if not ocr_results:
        return {"full_text": "", "lines": [], "mean_conf": 0.0,
                "total_tokens": 0, "rejected_low_conf": 0}

    filtered = [
        (bbox, text.strip(), conf)
        for bbox, text, conf in ocr_results
        if conf >= min_confidence and text.strip()
    ]
    rejected = len(ocr_results) - len(filtered)

    if not filtered:
        return {"full_text": "", "lines": [], "mean_conf": 0.0,
                "total_tokens": 0, "rejected_low_conf": rejected}

    # Adaptive line-band threshold based on median text height
    heights = sorted(_bbox_height(b) for b, _, _ in filtered)
    median_h = heights[len(heights) // 2] if heights else 20
    threshold = max(median_h * line_merge_ratio, 6)

    # Sort top-to-bottom
    items = sorted(filtered, key=lambda r: _bbox_ycenter(r[0]))

    # Group into line bands
    bands: list[list] = []
    current: list = [items[0]]
    current_y = _bbox_ycenter(items[0][0])

    for item in items[1:]:
        yc = _bbox_ycenter(item[0])
        if abs(yc - current_y) <= threshold:
            current.append(item)
            current_y = sum(_bbox_ycenter(r[0]) for r in current) / len(current)
        else:
            bands.append(current)
            current = [item]
            current_y = yc
    bands.append(current)

    # Build line dicts
    result_lines = []
    for band in bands:
        band_sorted = sorted(band, key=lambda r: _bbox_xcenter(r[0]))
        text     = " ".join(t for _, t, _ in band_sorted)
        mean_c   = sum(c for _, _, c in band_sorted) / len(band_sorted)
        yc       = sum(_bbox_ycenter(r[0]) for r in band_sorted) / len(band_sorted)
        result_lines.append({
            "text":        text,
            "y_center":    round(yc, 1),
            "mean_conf":   round(mean_c, 3),
            "token_count": len(band_sorted),
        })

    full_text = "\n".join(l["text"] for l in result_lines)
    all_confs = [r[2] for r in filtered]
    mean_conf = sum(all_confs) / len(all_confs)

    return {
        "full_text":         full_text,
        "lines":             result_lines,
        "mean_conf":         round(mean_conf, 3),
        "total_tokens":      len(filtered),
        "rejected_low_conf": rejected,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. Section boundary extraction
# ══════════════════════════════════════════════════════════════════════════════

_START_KW = [
    "ingredients", "ingredient list", "ingredients:", "contains:",
    "composition", "ingr.", "ingr:", "contents:", "made with",
    "made from", "formulated with", "formulated from",
]

_STOP_KW = [
    # Nutrition table
    "nutrition facts", "nutrition information", "nutritional information",
    "nutritional value", "nutritional values", "supplement facts",
    "serving size", "servings per container", "amount per serving",
    "calories", "total fat", "saturated fat", "trans fat",
    "cholesterol", "total carbohydrate", "dietary fiber", "total sugars",
    "added sugars", "vitamin d", "% daily value", "daily value",
    # Regulatory / company
    "manufactured by", "manufactured in", "packed by", "packed in",
    "distributed by", "imported by", "marketed by", "sold by",
    "fssai", "fssai no", "lic. no", "license no", "reg. no",
    # Storage / batch
    "storage", "store in", "keep refrigerated", "keep cool",
    "best before", "use before", "expiry", "mfg date", "mfg. date",
    "net wt", "net weight", "net content", "net vol",
    "batch no", "batch number", "lot no", "lot number",
    # Contact
    "customer care", "consumer care", "helpline", "toll free",
    "website:", "www.", "email:", "contact us",
    "address:", "registered office", "corporate office",
    # Misc
    "barcode", "directions", "how to use", "usage",
    "allergen warning", "warning:", "caution:",
    "country of origin", "product of",
]


def extract_ingredient_section(full_text: str) -> dict:
    """
    Scan OCR lines for ingredient start/stop keywords.

    Returns section text, boundary keywords found, and a confidence score.
    """
    lines = full_text.splitlines()
    nlines = [_norm(l) for l in lines]

    start_idx = start_kw = stop_idx = stop_kw = None

    for i, nl in enumerate(nlines):
        if start_idx is None:
            for kw in _START_KW:
                if kw in nl:
                    start_idx = i
                    start_kw  = kw
                    break
        else:
            for kw in _STOP_KW:
                if kw in nl:
                    stop_idx = i
                    stop_kw  = kw
                    break
            if stop_idx is not None:
                break

    start_found = start_idx is not None

    if start_found and stop_idx is not None:
        section_lines = lines[start_idx:stop_idx]
        confidence    = 0.95
    elif start_found:
        section_lines = lines[start_idx:]
        confidence    = 0.75
    else:
        section_lines = lines
        confidence    = 0.40

    # Strip bare start-keyword header line
    if section_lines and start_kw:
        first_n = _norm(section_lines[0])
        if first_n.strip(": ") in _START_KW:
            section_lines = section_lines[1:]
        elif first_n.startswith(start_kw):
            section_lines[0] = re.sub(
                re.escape(start_kw) + r"[:\s]*", "", section_lines[0],
                count=1, flags=re.I,
            )

    section = "\n".join(section_lines).strip()

    return {
        "section":          section,
        "start_found":      start_found,
        "start_keyword":    start_kw,
        "stop_keyword":     stop_kw,
        "ocr_confidence":   round(confidence, 2),
        "full_text_used":   not start_found,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. OCR noise removal
# ══════════════════════════════════════════════════════════════════════════════

_EMAIL    = re.compile(r'\b[\w.+\-]+@[\w\-]+\.\w{2,}\b', re.I)
_URL      = re.compile(r'https?://\S+|www\.\S+', re.I)
_BARCODE  = re.compile(r'\b\d{8,}\b')
_PHONE    = re.compile(r'(\+?\d[\d\s\-().]{7,}\d)')
_KCAL     = re.compile(r'\b\d+\.?\d*\s*(kcal|cal|kj|calories?)\b', re.I)
_WEIGHT   = re.compile(r'\b\d+\.?\d*\s*(g|mg|mcg|ml|kg|oz|lb|iu|%)\b', re.I)
_FRACTION = re.compile(r'\b\d+\.?\d*/\d+\b')
_PINCODE  = re.compile(r'\b\d{6}\b')
_PURE_NUM = re.compile(r'^\s*[\d\s.,]+\s*$')

_ADDR_WORDS = {
    "street", "road", "avenue", "lane", "nagar", "colony", "floor",
    "building", "plot", "survey", "village", "district", "state",
    "phase", "sector", "block", "industrial", "estate", "area",
    "layout", "cross", "main", "near",
}

_NUTRITION_HEADERS = {
    "energy", "fat", "carbohydrate", "carbohydrates", "fibre", "fiber",
    "sugars", "protein", "sodium", "calcium", "iron", "vitamin",
    "potassium", "cholesterol", "magnesium", "phosphorus",
    "per 100g", "per serving", "per 100 ml", "daily value", "dv", "rda",
}


def clean_ocr_noise(raw: str) -> dict:
    removed, stats = [], {k: 0 for k in (
        "emails", "urls", "barcodes", "phones", "kcal",
        "weights", "pure_numbers", "addresses", "nutrition_headers",
    )}

    def strip_pattern(pattern, label, stat_key, text):
        for m in pattern.finditer(text):
            removed.append((m.group(), label))
            stats[stat_key] += 1
        return pattern.sub(" ", text)

    text = raw
    text = strip_pattern(_EMAIL,   "email",         "emails",   text)
    text = strip_pattern(_URL,     "url",           "urls",     text)
    text = strip_pattern(_BARCODE, "barcode",       "barcodes", text)
    text = strip_pattern(_PHONE,   "phone number",  "phones",   text)
    text = strip_pattern(_KCAL,    "calorie value", "kcal",     text)
    text = strip_pattern(_WEIGHT,  "weight/volume", "weights",  text)
    text = _FRACTION.sub(" ", text)
    text = _PINCODE.sub(" ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Line-level filters
    clean_lines = []
    for line in text.splitlines():
        nl = _norm(line)
        words = set(nl.split())
        if len(words & _ADDR_WORDS) >= 2:
            removed.append((line.strip(), "address line"))
            stats["addresses"] += 1
            continue
        if _PURE_NUM.match(nl):
            removed.append((line.strip(), "pure number row"))
            stats["pure_numbers"] += 1
            continue
        if nl.strip().rstrip(":% ") in _NUTRITION_HEADERS:
            removed.append((line.strip(), "nutrition header"))
            stats["nutrition_headers"] += 1
            continue
        clean_lines.append(line)

    return {
        "cleaned":       "\n".join(clean_lines).strip(),
        "removed":       removed,
        "removal_stats": stats,
        "noise_count":   len(removed),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. Depth-aware tokeniser  (comma-splits outside parentheses only)
# ══════════════════════════════════════════════════════════════════════════════

def tokenize_ingredient_section(text: str) -> list[str]:
    """
    Split ingredient list text on commas/semicolons/pipes at the TOP level,
    respecting parenthetical nesting so "Wheat Flour (contains Gluten, Wheat)"
    stays as one token (with sub-list still inside parentheses).
    """
    tokens  = []
    current = []
    depth   = 0

    for ch in text:
        if ch in "([":
            depth += 1
            current.append(ch)
        elif ch in ")]":
            if depth > 0:
                depth -= 1
            current.append(ch)
        elif ch in ",;|" and depth == 0:
            tok = "".join(current).strip()
            if tok:
                tokens.append(tok)
            current = []
        elif ch == "\n" and depth == 0:
            current.append(" ")
        else:
            current.append(ch)

    remaining = "".join(current).strip()
    if remaining:
        tokens.append(remaining)

    # Normalise whitespace, strip bullets/quotes
    result = []
    for t in tokens:
        t = t.strip().strip('•·*"\'— \t')
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            result.append(t)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# 5. Token validation
# ══════════════════════════════════════════════════════════════════════════════

_NO_ALPHA  = re.compile(r'^[^a-zA-Z]+$')
_ONLY_NUMS = re.compile(r'^\s*[\d\s.,]+\s*$')

_NOISE_WORDS = {
    "and", "the", "of", "in", "to", "a", "an", "by", "as", "for",
    "is", "are", "was", "be", "at", "or", "no", "per", "see", "use",
    "may", "not", "with", "also", "from", "each", "made",
    "|", "—", "–", "·", "•", "*", "#", "@", "~", "n/a", "na",
}


def is_valid_ingredient_token(token: str) -> tuple[bool, str]:
    t = token.strip()
    if not t:
        return False, "empty"
    if len(t) < 3:
        return False, "too short (< 3 chars)"
    if _NO_ALPHA.match(t):
        return False, "no alphabetic characters"
    if _ONLY_NUMS.match(t):
        return False, "pure number"
    if _KCAL.search(t):
        return False, "calorie/energy value"
    if _BARCODE.search(t):
        return False, "barcode number"
    if _EMAIL.search(t):
        return False, "email address"
    if _PHONE.search(t):
        return False, "phone number"

    alpha_count = sum(1 for c in t if c.isalpha())
    if alpha_count < 2:
        return False, "fewer than 2 alpha chars"

    non_alpha_ratio = sum(1 for c in t if not c.isalpha()) / max(1, len(t))
    if len(t) > 4 and non_alpha_ratio > 0.70:
        return False, "mostly non-alphabetic"

    if _norm(t) in _NOISE_WORDS:
        return False, "common noise word"

    if _norm(t).strip(":% ") in _NUTRITION_HEADERS:
        return False, "nutrition table header"

    return True, ""


# ══════════════════════════════════════════════════════════════════════════════
# 6. Anti-hallucination guard
# ══════════════════════════════════════════════════════════════════════════════

def _would_hallucinate(token_norm: str, match_name_norm: str) -> bool:
    """
    Return True if accepting this match would 'invent' words not present
    in the original token — i.e. expand a short token to a longer DB entry.

    Examples that return True (hallucination):
      "protein"   →  "soy protein"        (single word → multi-word)
      "oil"       →  "palm oil"           (single word → multi-word)
      "starch"    →  "modified starch"    (single word → multi-word)

    Examples that return False (safe to accept):
      "sugar"     →  "sugar"              (exact)
      "wheat flour" → "wheat flour (maida)" (token fully in match)
      "natural flavors" → "natural flavors"  (multi-word exact)
      "sodium benzoate" → "sodium benzoate"  (exact)
    """
    t_sig = [w for w in token_norm.split() if len(w) > 2]
    m_sig = [w for w in match_name_norm.split() if len(w) > 2]

    if not t_sig:
        return True

    # Rule 1: single significant word in token → must not expand to multi-word match
    if len(t_sig) == 1 and len(m_sig) > 1:
        return True

    # Rule 2: token words must appear in match (allow minor OCR variation ≤ 20%)
    t_set = set(t_sig)
    m_set = set(m_sig)
    missing = t_set - m_set
    if missing and len(missing) / len(t_set) > 0.25:
        return True

    return False


# ══════════════════════════════════════════════════════════════════════════════
# 7. Strict fuzzy matcher
# ══════════════════════════════════════════════════════════════════════════════

def fuzzy_match_strict(
    token: str,
    db_names_single: list[str],   # single-word DB names (normalised)
    db_names_multi:  list[str],   # multi-word DB names (normalised)
    db_map:          dict[str, dict],
    threshold_single: int = 92,   # strict for single words (near-exact)
    threshold_multi:  int = 88,   # slightly relaxed for multi-word phrases
) -> dict:
    """
    Match a token against the ingredient DB with anti-hallucination protection.

    Single-word tokens only match single-word DB entries (≥92 % similarity).
    Multi-word tokens match both pools at ≥88 %.
    """
    t_lower = _norm(token)
    t_words = [w for w in t_lower.split() if len(w) > 2]

    is_single = len(t_words) <= 1

    # Choose candidate pool and threshold
    if is_single:
        candidates = db_names_single
        threshold  = threshold_single
    else:
        candidates = db_names_single + db_names_multi
        threshold  = threshold_multi

    best_name  = None
    best_score = 0.0

    try:
        from rapidfuzz import process, fuzz
        result = process.extractOne(
            t_lower, candidates,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=threshold,
        )
        if result:
            best_name  = result[0]
            best_score = result[1] / 100.0
    except ImportError:
        for name in candidates:
            score = SequenceMatcher(None, t_lower, name).ratio() * 100
            if score > best_score:
                best_score = score
                best_name  = name
        if best_score < threshold:
            best_name  = None
        best_score /= 100.0

    if best_name is None or best_name not in db_map:
        return {"matched": False, "ingredient": None,
                "match_name": None, "confidence": 0.0}

    # Anti-hallucination check
    if _would_hallucinate(t_lower, best_name):
        return {"matched": False, "ingredient": None,
                "match_name": None, "confidence": 0.0,
                "rejected_reason": f"hallucination guard: '{token}' would expand to '{best_name}'"}

    return {
        "matched":    True,
        "ingredient": db_map[best_name],
        "match_name": best_name,
        "confidence": round(best_score, 3),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 8. DB index builder (split by word count for anti-hallucination)
# ══════════════════════════════════════════════════════════════════════════════

def build_db_index(all_ingredients: list[dict]) -> tuple[list, list, dict]:
    """
    Returns:
      db_names_single – normalised single-word names
      db_names_multi  – normalised multi-word names (≥2 significant words)
      db_map          – normalised name → row dict
    """
    db_single: list[str] = []
    db_multi:  list[str] = []
    db_map:    dict      = {}

    for ing in all_ingredients:
        key   = _norm(ing["name"])
        words = [w for w in key.split() if len(w) > 2]
        if key not in db_map:
            db_map[key] = ing
            if len(words) <= 1:
                db_single.append(key)
            else:
                db_multi.append(key)
        # Also index the E-number / CI code
        if ing.get("code"):
            code_key = _norm(ing["code"])
            if code_key not in db_map:
                db_map[code_key] = ing
                db_single.append(code_key)

    return db_single, db_multi, db_map
