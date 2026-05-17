"""
Core ingredient analysis engine.

Pipeline (text input path):
  raw_text → tokenize → validate → code-detect → DB fuzzy-match → score/grade

Pipeline (OCR path):
  raw OCR text → extract_ingredient_section → clean_ocr_noise
              → tokenize → validate → code-detect → DB fuzzy-match → score/grade
"""

import re
from ingredient_extractor import (
    extract_ingredient_section,
    clean_ocr_noise,
    tokenize_cleaned,
    is_valid_ingredient_token,
    fuzzy_match_token,
    build_db_index,
    _normalise,
)
from database import get_all_ingredients, increment_match_stat

# ── Additive code lookup table ────────────────────────────────────────────────

CODE_ENTRIES: dict[str, dict] = {
    "E100":  {"name": "Curcumin",              "category": "Colorant",          "risk_level": "low",    "description": "Natural yellow from turmeric. Generally safe.", "child_warning": None},
    "E101":  {"name": "Riboflavin (B2)",        "category": "Colorant",          "risk_level": "low",    "description": "Natural yellow color. Also a beneficial nutrient.", "child_warning": None},
    "E102":  {"name": "Tartrazine",             "category": "Colorant",          "risk_level": "high",   "description": "Synthetic yellow dye linked to hyperactivity.", "child_warning": "Linked to hyperactivity and ADHD in children. Avoid."},
    "E104":  {"name": "Quinoline Yellow",       "category": "Colorant",          "risk_level": "medium", "description": "Synthetic dye. May cause hyperactivity.", "child_warning": "May worsen hyperactivity in children."},
    "E110":  {"name": "Sunset Yellow FCF",      "category": "Colorant",          "risk_level": "high",   "description": "Synthetic orange dye linked to hyperactivity and allergic reactions.", "child_warning": "Strongly associated with hyperactivity. Avoid in children."},
    "E120":  {"name": "Carmine (Cochineal)",    "category": "Colorant",          "risk_level": "medium", "description": "Red dye from insects. Can cause severe allergic reactions.", "child_warning": None},
    "E122":  {"name": "Carmoisine",             "category": "Colorant",          "risk_level": "high",   "description": "Synthetic red dye. Linked to hyperactivity and allergic reactions.", "child_warning": "Linked to hyperactivity. Not suitable for children."},
    "E123":  {"name": "Amaranth",              "category": "Colorant",          "risk_level": "high",   "description": "Banned in US. Potential carcinogen.", "child_warning": "Banned in US. Avoid for children."},
    "E124":  {"name": "Ponceau 4R",            "category": "Colorant",          "risk_level": "high",   "description": "Synthetic red dye linked to hyperactivity.", "child_warning": "Linked to hyperactivity and attention problems in children."},
    "E127":  {"name": "Erythrosine",           "category": "Colorant",          "risk_level": "high",   "description": "Synthetic red dye. Potential thyroid disruptor.", "child_warning": "Potential thyroid disruptor. Avoid in children."},
    "E129":  {"name": "Allura Red AC",         "category": "Colorant",          "risk_level": "high",   "description": "Synthetic red dye linked to hyperactivity in children.", "child_warning": "Directly linked to hyperactivity in children. Avoid."},
    "E131":  {"name": "Patent Blue V",         "category": "Colorant",          "risk_level": "medium", "description": "Synthetic blue dye. May cause allergic reactions.", "child_warning": None},
    "E132":  {"name": "Indigotine",            "category": "Colorant",          "risk_level": "medium", "description": "Synthetic blue dye. Can cause nausea.", "child_warning": None},
    "E133":  {"name": "Brilliant Blue FCF",    "category": "Colorant",          "risk_level": "medium", "description": "Synthetic blue dye. May cause allergic reactions.", "child_warning": None},
    "E150a": {"name": "Caramel Color I",       "category": "Colorant",          "risk_level": "low",    "description": "Plain caramel color. Generally safe.", "child_warning": None},
    "E150d": {"name": "Caramel Color IV",      "category": "Colorant",          "risk_level": "medium", "description": "Contains 4-MEI, a possible carcinogen.", "child_warning": "Contains 4-MEI (possible carcinogen). Limit in children's diet."},
    "E151":  {"name": "Brilliant Black BN",    "category": "Colorant",          "risk_level": "medium", "description": "Synthetic black dye. May cause hyperactivity.", "child_warning": "May cause hyperactivity."},
    "E160a": {"name": "Beta-carotene",         "category": "Colorant",          "risk_level": "low",    "description": "Natural orange from carrots. Safe and nutritious.", "child_warning": None},
    "E171":  {"name": "Titanium Dioxide",      "category": "Colorant",          "risk_level": "high",   "description": "Possible carcinogen. Banned in France.", "child_warning": "Possible carcinogen. Avoid in children's food."},
    "E200":  {"name": "Sorbic Acid",           "category": "Preservative",      "risk_level": "low",    "description": "Natural preservative. Generally safe.", "child_warning": None},
    "E202":  {"name": "Potassium Sorbate",     "category": "Preservative",      "risk_level": "low",    "description": "Common preservative. Generally safe.", "child_warning": None},
    "E210":  {"name": "Benzoic Acid",          "category": "Preservative",      "risk_level": "medium", "description": "Can form carcinogenic benzene with Vitamin C.", "child_warning": "Avoid combining with Vitamin C-rich drinks in children."},
    "E211":  {"name": "Sodium Benzoate",       "category": "Preservative",      "risk_level": "high",   "description": "Linked to hyperactivity. Can form carcinogenic benzene.", "child_warning": "Strongly linked to hyperactivity in children. Avoid."},
    "E212":  {"name": "Potassium Benzoate",    "category": "Preservative",      "risk_level": "high",   "description": "Similar to E211. Hyperactivity risk.", "child_warning": "Hyperactivity risk in children. Avoid."},
    "E220":  {"name": "Sulphur Dioxide",       "category": "Preservative",      "risk_level": "high",   "description": "Can trigger asthma attacks.", "child_warning": "Can trigger asthma in susceptible children."},
    "E221":  {"name": "Sodium Sulphite",       "category": "Preservative",      "risk_level": "high",   "description": "Severe allergic reactions in sulfite-sensitive individuals.", "child_warning": "Allergic reactions possible. Check for sulfite sensitivity."},
    "E250":  {"name": "Sodium Nitrite",        "category": "Preservative",      "risk_level": "high",   "description": "Can form carcinogenic nitrosamines.", "child_warning": "Potential carcinogen. Strongly limit in children's diet."},
    "E251":  {"name": "Sodium Nitrate",        "category": "Preservative",      "risk_level": "high",   "description": "Potential carcinogen via nitrosamine formation.", "child_warning": "Limit processed meats in children's diet."},
    "E260":  {"name": "Acetic Acid",           "category": "Acidity Regulator", "risk_level": "low",    "description": "Common vinegar acid. Safe.", "child_warning": None},
    "E270":  {"name": "Lactic Acid",           "category": "Acidity Regulator", "risk_level": "low",    "description": "Natural fermentation product. Safe.", "child_warning": None},
    "E300":  {"name": "Ascorbic Acid (Vit C)", "category": "Antioxidant",       "risk_level": "low",    "description": "Vitamin C. Beneficial antioxidant.", "child_warning": None},
    "E320":  {"name": "BHA",                   "category": "Antioxidant",       "risk_level": "high",   "description": "Probable carcinogen. Avoid.", "child_warning": "Probable carcinogen. Avoid in children's food."},
    "E321":  {"name": "BHT",                   "category": "Antioxidant",       "risk_level": "high",   "description": "Potential endocrine disruptor and carcinogen.", "child_warning": "Endocrine disruptor. Avoid in children."},
    "E330":  {"name": "Citric Acid",           "category": "Acidity Regulator", "risk_level": "low",    "description": "Natural acid. Generally safe.", "child_warning": None},
    "E407":  {"name": "Carrageenan",           "category": "Thickener",         "risk_level": "medium", "description": "May cause digestive inflammation.", "child_warning": "May cause gut inflammation. Use caution."},
    "E420":  {"name": "Sorbitol",              "category": "Sweetener",         "risk_level": "medium", "description": "Sugar alcohol. Digestive issues at high intake.", "child_warning": "Can cause diarrhoea in children at high doses."},
    "E450":  {"name": "Diphosphates",          "category": "Emulsifier",        "risk_level": "medium", "description": "Excess linked to kidney issues.", "child_warning": None},
    "E471":  {"name": "Mono- and Diglycerides","category": "Emulsifier",        "risk_level": "low",    "description": "Common emulsifier. Generally safe.", "child_warning": None},
    "E621":  {"name": "MSG",                   "category": "Flavor Enhancer",   "risk_level": "medium", "description": "May cause headaches in sensitive individuals.", "child_warning": "Some children are sensitive. Limit intake."},
    "E627":  {"name": "Disodium Guanylate",    "category": "Flavor Enhancer",   "risk_level": "medium", "description": "Avoid with gout.", "child_warning": None},
    "E631":  {"name": "Disodium Inosinate",    "category": "Flavor Enhancer",   "risk_level": "medium", "description": "Avoid with gout.", "child_warning": None},
    "E951":  {"name": "Aspartame",             "category": "Sweetener",         "risk_level": "high",   "description": "Possible carcinogen (WHO Group 2B). Contraindicated with PKU.", "child_warning": "Dangerous for children with PKU. Controversial safety profile."},
    "E952":  {"name": "Cyclamate",             "category": "Sweetener",         "risk_level": "high",   "description": "Banned in US. Possible carcinogen.", "child_warning": "Banned in US. Avoid in children's food."},
    "E954":  {"name": "Saccharin",             "category": "Sweetener",         "risk_level": "medium", "description": "Artificial sweetener.", "child_warning": "Avoid for very young children."},
    "E955":  {"name": "Sucralose",             "category": "Sweetener",         "risk_level": "medium", "description": "May alter gut microbiome.", "child_warning": "Long-term effects on children's gut microbiome unclear."},
    # CI colour codes
    "CI 77891": {"name": "Titanium Dioxide",   "category": "Colorant",          "risk_level": "high",   "description": "Possible carcinogen in nano form.", "child_warning": "Nano-TiO2 may be carcinogenic. Avoid."},
    "CI 77491": {"name": "Iron Oxide Red",     "category": "Colorant",          "risk_level": "low",    "description": "Natural iron oxide. Safe.", "child_warning": None},
    "CI 77492": {"name": "Iron Oxide Yellow",  "category": "Colorant",          "risk_level": "low",    "description": "Natural iron oxide. Safe.", "child_warning": None},
    "CI 77499": {"name": "Iron Oxide Black",   "category": "Colorant",          "risk_level": "low",    "description": "Natural iron oxide. Safe.", "child_warning": None},
    "CI 16035": {"name": "Allura Red",         "category": "Colorant",          "risk_level": "high",   "description": "Synthetic red dye linked to hyperactivity.", "child_warning": "Linked to hyperactivity. Avoid in children."},
    "CI 19140": {"name": "Tartrazine",         "category": "Colorant",          "risk_level": "high",   "description": "Synthetic yellow dye linked to hyperactivity.", "child_warning": "Linked to hyperactivity. Avoid in children."},
    "CI 42090": {"name": "Brilliant Blue FCF", "category": "Colorant",          "risk_level": "medium", "description": "Synthetic blue dye.", "child_warning": None},
    "CI 45430": {"name": "Erythrosine",        "category": "Colorant",          "risk_level": "high",   "description": "Thyroid disruptor.", "child_warning": "Potential thyroid disruptor. Avoid."},
}

CODE_PATTERNS = [
    (re.compile(r'\b(E\s*\d{3}[a-dA-D]?)\b'),        lambda m: m.group(1).upper().replace(" ", "")),
    (re.compile(r'\b(INS\s*\d{3}[a-dA-D]?)\b', re.I),lambda m: "E" + re.sub(r'[^0-9]', '', m.group(1))),
    (re.compile(r'\b(CI\s*\d{5})\b', re.I),           lambda m: "CI " + re.sub(r'[^0-9]', '', m.group(1))),
]


def _detect_code(token: str):
    for pattern, normalizer in CODE_PATTERNS:
        m = pattern.search(token)
        if m:
            code = normalizer(m)
            entry = CODE_ENTRIES.get(code)
            if entry:
                return code, entry
    return None, None


# ── Risk grouping ─────────────────────────────────────────────────────────────

def _risk_to_group(risk_level: str) -> str:
    return {
        "high":    "harmful",
        "medium":  "moderate",
        "low":     "safe",
        "unknown": "unknown",
    }.get(risk_level, "unknown")


# ── Profile warnings ──────────────────────────────────────────────────────────

def _profile_warning(flags_str: str | None, profile: str) -> str | None:
    if not flags_str:
        return None
    flags = {f.strip().lower() for f in flags_str.split(",")}
    msgs = []
    if profile == "children"  and "children"  in flags: msgs.append("Not recommended for children")
    if profile == "pregnant"  and "pregnant"  in flags: msgs.append("Caution during pregnancy")
    if profile == "elderly"   and "elderly"   in flags: msgs.append("Caution for elderly individuals")
    if "allergen" in flags: msgs.append("Potential allergen — check sensitivity")
    return ". ".join(msgs) if msgs else None


def _child_safety_warning(item: dict, code_entry: dict | None) -> str | None:
    """Return a child-specific warning string or None."""
    if code_entry and code_entry.get("child_warning"):
        return code_entry["child_warning"]
    db_row = item.get("_db_row")
    if db_row:
        flags = {f.strip().lower() for f in (db_row.get("profile_flags") or "").split(",")}
        if "children" in flags:
            return f"{db_row['name']} is flagged as not recommended for children."
    return None


# ── Grade calculation ─────────────────────────────────────────────────────────

def _compute_grade(score: float) -> str:
    if score <= 10: return "A"
    if score <= 25: return "B"
    if score <= 45: return "C"
    if score <= 65: return "D"
    return "F"


# ── Main analysis function ────────────────────────────────────────────────────

def analyze_ingredients(
    raw_text: str,
    profile: str = "general",
    is_ocr: bool = False,
) -> dict:
    """
    Full ingredient analysis pipeline.

    Args:
        raw_text  – either a pasted ingredient list or raw OCR dump
        profile   – safety profile: general | children | pregnant | elderly
        is_ocr    – if True, run section extraction + noise removal first

    Returns a rich result dict.
    """
    extraction_meta: dict = {}

    if is_ocr:
        # Step 1 – isolate the ingredient section
        sec = extract_ingredient_section(raw_text)
        extraction_meta["section"] = sec
        section_text = sec["section"]

        # Step 2 – clean noise
        cleaned = clean_ocr_noise(section_text)
        extraction_meta["cleaning"] = cleaned
        work_text = cleaned["cleaned"]
    else:
        work_text = raw_text
        extraction_meta = {}

    # Load DB + build fuzzy index
    all_db, _ = get_all_ingredients(limit=2000)
    db_names, db_map = build_db_index(all_db)

    # Step 3 – tokenise
    tokens = tokenize_cleaned(work_text)

    results       = []
    rejected      = []
    seen_names    = set()   # deduplicate

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        # ── Validate token ──
        valid, reason = is_valid_ingredient_token(token)
        if not valid:
            rejected.append({"token": token, "reason": reason})
            continue

        # ── Code detection (E-numbers, INS, CI) ──
        code, code_entry = _detect_code(token)
        if code_entry:
            dedup_key = code
            if dedup_key in seen_names:
                continue
            seen_names.add(dedup_key)

            child_warn = code_entry.get("child_warning")
            profile_warn = None
            if profile == "children" and code_entry["risk_level"] in ("high", "medium"):
                profile_warn = child_warn or f"{code_entry['name']} carries a {code_entry['risk_level']} risk."
            if profile == "pregnant" and code_entry["risk_level"] != "low":
                profile_warn = (profile_warn or "") + " Use caution during pregnancy."
            if profile == "elderly" and code_entry["risk_level"] == "high":
                profile_warn = (profile_warn or "") + " Use caution for elderly individuals."

            results.append({
                "raw":           token,
                "name":          code_entry["name"],
                "code":          code,
                "category":      code_entry["category"],
                "risk_level":    code_entry["risk_level"],
                "group":         _risk_to_group(code_entry["risk_level"]),
                "description":   code_entry["description"],
                "safety_notes":  code_entry.get("description", ""),
                "warning":       profile_warn,
                "child_warning": child_warn,
                "matched":       True,
                "match_source":  "code_table",
                "confidence":    1.0,
                "_db_row":       None,
            })
            continue

        # ── Fuzzy DB match ──
        norm = _normalise(token)
        words = [w for w in norm.split() if len(w) > 2]
        primary = " ".join(words[:3])
        if not primary:
            rejected.append({"token": token, "reason": "normalised to empty"})
            continue

        fm = fuzzy_match_token(primary, db_names, db_map, threshold=72)

        if fm["matched"]:
            row = fm["ingredient"]
            dedup_key = _normalise(row["name"])
            if dedup_key in seen_names:
                continue
            seen_names.add(dedup_key)

            risk_level   = row["risk_level"]
            safety_notes = row.get("safety_notes") or ""
            prof_warn    = _profile_warning(row.get("profile_flags"), profile)
            warning      = ". ".join(filter(None, [safety_notes, prof_warn])) or None
            child_warn   = _child_safety_warning({"_db_row": row}, None)

            try:
                increment_match_stat(row["id"])
            except Exception:
                pass

            results.append({
                "raw":           token,
                "name":          row["name"],
                "code":          row.get("code", ""),
                "category":      row.get("category", ""),
                "risk_level":    risk_level,
                "group":         _risk_to_group(risk_level),
                "description":   row.get("description", ""),
                "safety_notes":  safety_notes,
                "warning":       warning,
                "child_warning": child_warn,
                "matched":       True,
                "match_source":  "db_fuzzy",
                "confidence":    fm["confidence"],
                "_db_row":       row,
            })
        else:
            # Unknown — include but flag as unvalidated
            dedup_key = norm
            if dedup_key in seen_names:
                continue
            seen_names.add(dedup_key)

            results.append({
                "raw":           token,
                "name":          token,
                "code":          "",
                "category":      "",
                "risk_level":    "unknown",
                "group":         "unknown",
                "description":   "",
                "safety_notes":  "",
                "warning":       None,
                "child_warning": None,
                "matched":       False,
                "match_source":  "none",
                "confidence":    0.0,
                "_db_row":       None,
            })

    # ── Scoring ───────────────────────────────────────────────────────────────
    SCORE_MAP = {"high": 10, "medium": 4, "low": 1, "unknown": 2}
    total_score = sum(SCORE_MAP.get(r["risk_level"], 2) for r in results)
    total       = len(results) or 1
    norm_score  = min(100.0, (total_score / total) * 10)
    grade       = _compute_grade(norm_score)

    counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    for r in results:
        counts[r["risk_level"]] = counts.get(r["risk_level"], 0) + 1

    # ── Grouped output ────────────────────────────────────────────────────────
    groups = {"harmful": [], "moderate": [], "safe": [], "unknown": []}
    for r in results:
        groups[r["group"]].append(r)

    # ── Child safety summary ──────────────────────────────────────────────────
    child_warnings = [
        {"name": r["name"], "warning": r["child_warning"]}
        for r in results if r.get("child_warning")
    ]

    # ── OCR-specific stats ────────────────────────────────────────────────────
    ocr_stats = None
    if is_ocr and extraction_meta:
        sec   = extraction_meta.get("section", {})
        clean = extraction_meta.get("cleaning", {})
        ocr_stats = {
            "start_keyword":    sec.get("start_keyword"),
            "stop_keyword":     sec.get("stop_keyword"),
            "section_found":    sec.get("start_found", False),
            "section_confidence": sec.get("ocr_confidence", 0.0),
            "full_text_used":   sec.get("full_text_used", True),
            "noise_removed":    clean.get("noise_count", 0),
            "removal_stats":    clean.get("removal_stats", {}),
            "noise_items":      clean.get("removed", [])[:20],
            "cleaned_text":     clean.get("cleaned", ""),
        }

    # Strip internal _db_row before returning
    for r in results:
        r.pop("_db_row", None)

    avg_confidence = (
        sum(r["confidence"] for r in results if r["matched"]) /
        max(1, sum(1 for r in results if r["matched"]))
    )

    return {
        "ingredients": results,
        "groups":      groups,
        "grade":       grade,
        "risk_score":  round(norm_score, 1),
        "profile":     profile,
        "counts":      counts,
        "total":       len(results),
        "rejected":    rejected,
        "child_warnings": child_warnings,
        "avg_confidence": round(avg_confidence, 3),
        "ocr_stats":   ocr_stats,
    }
