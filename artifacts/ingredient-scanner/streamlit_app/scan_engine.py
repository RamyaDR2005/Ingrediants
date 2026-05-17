import re
from database import search_ingredient, increment_match_stat

CODE_ENTRIES = {
    "E100": {"name": "Curcumin", "category": "Colorant", "risk_level": "low", "description": "Natural yellow color from turmeric. Generally safe."},
    "E102": {"name": "Tartrazine", "category": "Colorant", "risk_level": "high", "description": "Synthetic yellow dye linked to hyperactivity in children."},
    "E104": {"name": "Quinoline Yellow", "category": "Colorant", "risk_level": "medium", "description": "Synthetic dye. May cause hyperactivity."},
    "E110": {"name": "Sunset Yellow FCF", "category": "Colorant", "risk_level": "high", "description": "Synthetic orange dye linked to hyperactivity and allergic reactions."},
    "E120": {"name": "Carmine", "category": "Colorant", "risk_level": "medium", "description": "Red dye from insects. Can cause allergic reactions."},
    "E122": {"name": "Carmoisine", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye. Linked to hyperactivity."},
    "E123": {"name": "Amaranth", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye. Potential carcinogen. Banned in US."},
    "E124": {"name": "Ponceau 4R", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye linked to hyperactivity."},
    "E127": {"name": "Erythrosine", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye. Potential thyroid disruptor."},
    "E129": {"name": "Allura Red AC", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye linked to hyperactivity in children."},
    "E131": {"name": "Patent Blue V", "category": "Colorant", "risk_level": "medium", "description": "Synthetic blue dye. May cause allergic reactions."},
    "E132": {"name": "Indigotine", "category": "Colorant", "risk_level": "medium", "description": "Synthetic blue dye. Can cause nausea."},
    "E133": {"name": "Brilliant Blue FCF", "category": "Colorant", "risk_level": "medium", "description": "Synthetic blue dye. May cause allergic reactions."},
    "E150a": {"name": "Caramel Color I", "category": "Colorant", "risk_level": "low", "description": "Plain caramel color, generally safe."},
    "E150d": {"name": "Caramel Color IV", "category": "Colorant", "risk_level": "medium", "description": "Contains 4-MEI, a possible carcinogen."},
    "E160a": {"name": "Beta-carotene", "category": "Colorant", "risk_level": "low", "description": "Natural orange color from carrots."},
    "E171": {"name": "Titanium Dioxide", "category": "Colorant", "risk_level": "high", "description": "White colorant. Possible carcinogen. Banned in France."},
    "E200": {"name": "Sorbic Acid", "category": "Preservative", "risk_level": "low", "description": "Preservative from berries. Generally safe."},
    "E202": {"name": "Potassium Sorbate", "category": "Preservative", "risk_level": "low", "description": "Common preservative. Generally safe."},
    "E210": {"name": "Benzoic Acid", "category": "Preservative", "risk_level": "medium", "description": "Can form carcinogenic benzene with Vitamin C."},
    "E211": {"name": "Sodium Benzoate", "category": "Preservative", "risk_level": "high", "description": "Linked to hyperactivity in children. Can form carcinogenic benzene."},
    "E220": {"name": "Sulphur Dioxide", "category": "Preservative", "risk_level": "high", "description": "Can trigger asthma attacks."},
    "E250": {"name": "Sodium Nitrite", "category": "Preservative", "risk_level": "high", "description": "Can form carcinogenic nitrosamines."},
    "E251": {"name": "Sodium Nitrate", "category": "Preservative", "risk_level": "high", "description": "Potential carcinogen."},
    "E300": {"name": "Ascorbic Acid (Vitamin C)", "category": "Antioxidant", "risk_level": "low", "description": "Antioxidant and vitamin. Beneficial."},
    "E320": {"name": "BHA", "category": "Antioxidant", "risk_level": "high", "description": "Probable carcinogen. Avoid if possible."},
    "E321": {"name": "BHT", "category": "Antioxidant", "risk_level": "high", "description": "Potential endocrine disruptor and carcinogen."},
    "E330": {"name": "Citric Acid", "category": "Acidity Regulator", "risk_level": "low", "description": "Common natural acid. Generally safe."},
    "E407": {"name": "Carrageenan", "category": "Thickener", "risk_level": "medium", "description": "May cause digestive inflammation."},
    "E621": {"name": "MSG", "category": "Flavor Enhancer", "risk_level": "medium", "description": "May cause headaches in sensitive individuals."},
    "E951": {"name": "Aspartame", "category": "Sweetener", "risk_level": "high", "description": "Possible carcinogen (WHO Group 2B). Avoid with PKU."},
    "E954": {"name": "Saccharin", "category": "Sweetener", "risk_level": "medium", "description": "Artificial sweetener."},
    "E955": {"name": "Sucralose", "category": "Sweetener", "risk_level": "medium", "description": "May alter gut microbiome."},
    "CI 77891": {"name": "Titanium Dioxide", "category": "Colorant", "risk_level": "high", "description": "Possible carcinogen in nano form."},
    "CI 77491": {"name": "Iron Oxide Red", "category": "Colorant", "risk_level": "low", "description": "Natural iron oxide. Safe."},
    "CI 16035": {"name": "Allura Red", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye linked to hyperactivity."},
    "CI 19140": {"name": "Tartrazine", "category": "Colorant", "risk_level": "high", "description": "Synthetic yellow dye linked to hyperactivity."},
}

CODE_PATTERNS = [
    (re.compile(r'\b(E\s*\d{3}[a-d]?)\b', re.IGNORECASE), lambda m: m.group(1).upper().replace(" ", "")),
    (re.compile(r'\b(INS\s*\d{3}[a-d]?)\b', re.IGNORECASE), lambda m: "E" + re.sub(r'[^0-9]', '', m.group(1))),
    (re.compile(r'\b(CI\s*\d{5})\b', re.IGNORECASE), lambda m: m.group(1).upper().replace("  ", " ")),
]


def detect_code(token: str):
    for pattern, normalizer in CODE_PATTERNS:
        m = pattern.search(token)
        if m:
            code = normalizer(m)
            entry = CODE_ENTRIES.get(code)
            if entry:
                return code, entry
    return None, None


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'\(.*?\)', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(raw_text: str):
    parts = re.split(r'[,;\n•|]+', raw_text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def compute_grade(risk_score: float) -> str:
    if risk_score <= 10:
        return "A"
    elif risk_score <= 25:
        return "B"
    elif risk_score <= 45:
        return "C"
    elif risk_score <= 65:
        return "D"
    return "F"


PROFILE_FLAG_MAP = {
    "children": "children",
    "pregnant": "pregnant",
    "elderly": "elderly",
    "allergen": "allergen",
}


def get_profile_warning(profile_flags: str, profile: str) -> str | None:
    if not profile_flags:
        return None
    flags = [f.strip() for f in profile_flags.split(",")]
    warnings = []
    if profile == "children" and "children" in flags:
        warnings.append("Not recommended for children")
    if profile == "pregnant" and "pregnant" in flags:
        warnings.append("Caution during pregnancy")
    if profile == "elderly" and "elderly" in flags:
        warnings.append("Use caution for elderly individuals")
    if "allergen" in flags:
        warnings.append("Potential allergen")
    return ". ".join(warnings) if warnings else None


def analyze_ingredients(raw_text: str, profile: str = "general"):
    tokens = tokenize(raw_text)
    results = []

    for token in tokens:
        code, code_entry = detect_code(token)
        if code_entry:
            warning = code_entry["description"]
            if profile == "children" and code_entry["risk_level"] == "high":
                warning += " Not recommended for children."
            if profile == "pregnant" and code_entry["risk_level"] != "low":
                warning += " Use caution during pregnancy."
            results.append({
                "raw": token,
                "name": code_entry["name"],
                "code": code,
                "category": code_entry["category"],
                "risk_level": code_entry["risk_level"],
                "description": code_entry["description"],
                "warning": warning,
                "matched": True,
            })
            continue

        normalized = normalize_text(token)
        if not normalized:
            continue

        words = [w for w in normalized.split() if len(w) > 2]
        primary = " ".join(words[:3])

        matched = search_ingredient(primary) if primary else None

        risk_level = "unknown"
        warning = None

        if matched:
            risk_level = matched["risk_level"]
            warning = matched.get("safety_notes") or None
            profile_warning = get_profile_warning(matched.get("profile_flags", ""), profile)
            if profile_warning:
                warning = f"{warning}. {profile_warning}" if warning else profile_warning
            increment_match_stat(matched["id"])

        results.append({
            "raw": token,
            "name": matched["name"] if matched else token,
            "code": matched.get("code", "") if matched else "",
            "category": matched.get("category", "") if matched else "",
            "risk_level": risk_level,
            "description": matched.get("description", "") if matched else "",
            "warning": warning,
            "matched": matched is not None,
        })

    # Score calculation
    total_score = 0
    counts = {"low": 0, "medium": 0, "high": 0, "unknown": 0}

    for item in results:
        rl = item["risk_level"]
        if rl == "high":
            total_score += 10
            counts["high"] += 1
        elif rl == "medium":
            total_score += 4
            counts["medium"] += 1
        elif rl == "low":
            total_score += 1
            counts["low"] += 1
        else:
            total_score += 2
            counts["unknown"] += 1

    total = len(results) or 1
    normalized_score = min(100, (total_score / total) * 10)
    grade = compute_grade(normalized_score)

    return {
        "ingredients": results,
        "grade": grade,
        "risk_score": round(normalized_score, 1),
        "profile": profile,
        "counts": counts,
        "total": len(results),
    }
