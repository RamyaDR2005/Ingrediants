"""
SafeScan — Scan engine (v3)

Risk tiers (4-level):
  safe              – no significant concern at normal intake
  low_concern       – generally safe; minor concerns for some populations
  moderate_concern  – notable health concerns; limit intake
  high_concern      – significant risk; avoid or minimise

Anti-hallucination: single-word tokens never expand to multi-word DB entries.
"""

import re
from ingredient_extractor import (
    extract_ingredient_section,
    clean_ocr_noise,
    tokenize_ingredient_section,
    is_valid_ingredient_token,
    fuzzy_match_strict,
    build_db_index,
    _norm,
)
from database import get_all_ingredients, increment_match_stat

# ── 4-tier config ──────────────────────────────────────────────────────────────
TIERS = {
    "safe":             {"label": "Safe",             "icon": "🟢", "streamlit_color": "success"},
    "low_concern":      {"label": "Low Concern",      "icon": "🟡", "streamlit_color": "info"},
    "moderate_concern": {"label": "Moderate Concern", "icon": "🟠", "streamlit_color": "warning"},
    "high_concern":     {"label": "High Concern",     "icon": "🔴", "streamlit_color": "error"},
    "unknown":          {"label": "Unknown",          "icon": "⚪", "streamlit_color": "info"},
}

# ── Additive code lookup ───────────────────────────────────────────────────────
# tier is one of: safe / low_concern / moderate_concern / high_concern

CODE_ENTRIES: dict[str, dict] = {
    # Colorants
    "E100":  {"name": "Curcumin",              "category": "Colorant",          "tier": "safe",             "description": "Natural yellow from turmeric. Safe.",                                    "child_warning": None},
    "E101":  {"name": "Riboflavin (Vit B2)",   "category": "Colorant",          "tier": "safe",             "description": "Natural yellow; beneficial nutrient.",                                  "child_warning": None},
    "E102":  {"name": "Tartrazine",             "category": "Colorant",          "tier": "high_concern",     "description": "Synthetic yellow dye. Linked to hyperactivity and allergic reactions.", "child_warning": "Linked to hyperactivity/ADHD in children. Avoid."},
    "E104":  {"name": "Quinoline Yellow",       "category": "Colorant",          "tier": "moderate_concern", "description": "Synthetic dye. May cause hyperactivity; banned in some countries.",     "child_warning": "May worsen hyperactivity."},
    "E110":  {"name": "Sunset Yellow FCF",      "category": "Colorant",          "tier": "high_concern",     "description": "Synthetic orange dye. Linked to hyperactivity and allergic reactions.", "child_warning": "Strongly associated with hyperactivity. Avoid."},
    "E120":  {"name": "Carmine (Cochineal)",    "category": "Colorant",          "tier": "moderate_concern", "description": "Red dye from insects. Can cause severe allergic reactions.",            "child_warning": None},
    "E122":  {"name": "Carmoisine",             "category": "Colorant",          "tier": "high_concern",     "description": "Synthetic red dye. Hyperactivity and allergic reactions.",              "child_warning": "Not suitable for children."},
    "E123":  {"name": "Amaranth",              "category": "Colorant",          "tier": "high_concern",     "description": "Banned in US. Potential carcinogen.",                                   "child_warning": "Banned in US. Avoid."},
    "E124":  {"name": "Ponceau 4R",            "category": "Colorant",          "tier": "high_concern",     "description": "Synthetic red dye. Hyperactivity and attention problems.",              "child_warning": "Linked to hyperactivity."},
    "E127":  {"name": "Erythrosine",           "category": "Colorant",          "tier": "high_concern",     "description": "Potential thyroid disruptor.",                                          "child_warning": "Thyroid disruptor. Avoid."},
    "E129":  {"name": "Allura Red AC",         "category": "Colorant",          "tier": "high_concern",     "description": "Synthetic red dye. Directly linked to hyperactivity in children.",     "child_warning": "Directly linked to hyperactivity. Avoid."},
    "E131":  {"name": "Patent Blue V",         "category": "Colorant",          "tier": "moderate_concern", "description": "Synthetic blue dye. May cause allergic reactions.",                    "child_warning": None},
    "E132":  {"name": "Indigotine",            "category": "Colorant",          "tier": "moderate_concern", "description": "Synthetic blue dye. Can cause nausea.",                                "child_warning": None},
    "E133":  {"name": "Brilliant Blue FCF",    "category": "Colorant",          "tier": "moderate_concern", "description": "Synthetic blue dye. Allergic reactions possible.",                     "child_warning": None},
    "E150a": {"name": "Caramel Color I",       "category": "Colorant",          "tier": "safe",             "description": "Plain caramel color. Generally safe.",                                 "child_warning": None},
    "E150d": {"name": "Caramel Color IV",      "category": "Colorant",          "tier": "moderate_concern", "description": "Contains 4-MEI, a possible carcinogen.",                               "child_warning": "Contains possible carcinogen 4-MEI. Limit."},
    "E151":  {"name": "Brilliant Black BN",    "category": "Colorant",          "tier": "moderate_concern", "description": "Synthetic black dye. May cause hyperactivity.",                        "child_warning": "May cause hyperactivity."},
    "E160a": {"name": "Beta-carotene",         "category": "Colorant",          "tier": "safe",             "description": "Natural orange from carrots. Nutritious.",                             "child_warning": None},
    "E171":  {"name": "Titanium Dioxide",      "category": "Colorant",          "tier": "high_concern",     "description": "Possible carcinogen. Banned in France.",                               "child_warning": "Possible carcinogen. Avoid in children's food."},
    # Preservatives
    "E200":  {"name": "Sorbic Acid",           "category": "Preservative",      "tier": "safe",             "description": "Natural preservative from berries. Safe.",                             "child_warning": None},
    "E202":  {"name": "Potassium Sorbate",     "category": "Preservative",      "tier": "safe",             "description": "Common preservative. Generally safe.",                                 "child_warning": None},
    "E210":  {"name": "Benzoic Acid",          "category": "Preservative",      "tier": "moderate_concern", "description": "Can form benzene (carcinogen) when combined with Vitamin C.",          "child_warning": "Avoid mixing with Vit-C drinks."},
    "E211":  {"name": "Sodium Benzoate",       "category": "Preservative",      "tier": "high_concern",     "description": "Linked to hyperactivity. Can form carcinogenic benzene.",               "child_warning": "Strongly linked to hyperactivity. Avoid."},
    "E212":  {"name": "Potassium Benzoate",    "category": "Preservative",      "tier": "high_concern",     "description": "Similar to E211. Hyperactivity and benzene risk.",                     "child_warning": "Hyperactivity risk. Avoid."},
    "E220":  {"name": "Sulphur Dioxide",       "category": "Preservative",      "tier": "high_concern",     "description": "Can trigger asthma attacks.",                                          "child_warning": "Can trigger asthma."},
    "E221":  {"name": "Sodium Sulphite",       "category": "Preservative",      "tier": "high_concern",     "description": "Severe allergic reactions in sulfite-sensitive individuals.",           "child_warning": "Check for sulfite sensitivity."},
    "E250":  {"name": "Sodium Nitrite",        "category": "Preservative",      "tier": "high_concern",     "description": "Can form carcinogenic nitrosamines.",                                  "child_warning": "Potential carcinogen. Strongly limit."},
    "E251":  {"name": "Sodium Nitrate",        "category": "Preservative",      "tier": "high_concern",     "description": "Potential carcinogen via nitrosamine formation.",                       "child_warning": "Limit processed meats."},
    # Acids / Antioxidants
    "E260":  {"name": "Acetic Acid",           "category": "Acidity Regulator", "tier": "safe",             "description": "Common vinegar acid. Safe.",                                           "child_warning": None},
    "E270":  {"name": "Lactic Acid",           "category": "Acidity Regulator", "tier": "safe",             "description": "Natural fermentation product. Safe.",                                  "child_warning": None},
    "E300":  {"name": "Ascorbic Acid (Vit C)", "category": "Antioxidant",       "tier": "safe",             "description": "Vitamin C. Beneficial antioxidant.",                                   "child_warning": None},
    "E320":  {"name": "BHA",                   "category": "Antioxidant",       "tier": "high_concern",     "description": "Probable carcinogen. Avoid if possible.",                              "child_warning": "Probable carcinogen. Avoid in children's food."},
    "E321":  {"name": "BHT",                   "category": "Antioxidant",       "tier": "high_concern",     "description": "Potential endocrine disruptor and carcinogen.",                        "child_warning": "Endocrine disruptor. Avoid."},
    "E330":  {"name": "Citric Acid",           "category": "Acidity Regulator", "tier": "safe",             "description": "Natural acid found in citrus. Safe.",                                  "child_warning": None},
    # Thickeners / Emulsifiers
    "E407":  {"name": "Carrageenan",           "category": "Thickener",         "tier": "moderate_concern", "description": "May cause digestive inflammation.",                                    "child_warning": "May cause gut inflammation."},
    "E420":  {"name": "Sorbitol",              "category": "Sweetener",         "tier": "low_concern",      "description": "Sugar alcohol. Digestive issues at high intake.",                      "child_warning": "Can cause diarrhoea at high doses."},
    "E421":  {"name": "Mannitol",              "category": "Sweetener",         "tier": "low_concern",      "description": "Sugar alcohol. Digestive issues at high intake.",                      "child_warning": None},
    "E450":  {"name": "Diphosphates",          "category": "Emulsifier",        "tier": "low_concern",      "description": "Excess phosphate linked to kidney issues.",                            "child_warning": None},
    "E471":  {"name": "Mono- and Diglycerides","category": "Emulsifier",        "tier": "safe",             "description": "Common emulsifier. Generally safe.",                                   "child_warning": None},
    # Flavor enhancers / Sweeteners
    "E621":  {"name": "MSG",                   "category": "Flavor Enhancer",   "tier": "low_concern",      "description": "May cause headaches in sensitive individuals.",                        "child_warning": "Some children are sensitive."},
    "E627":  {"name": "Disodium Guanylate",    "category": "Flavor Enhancer",   "tier": "low_concern",      "description": "Avoid with gout.",                                                     "child_warning": None},
    "E631":  {"name": "Disodium Inosinate",    "category": "Flavor Enhancer",   "tier": "low_concern",      "description": "Avoid with gout.",                                                     "child_warning": None},
    "E951":  {"name": "Aspartame",             "category": "Sweetener",         "tier": "high_concern",     "description": "Possible carcinogen (WHO Group 2B). Contraindicated with PKU.",        "child_warning": "Dangerous for children with PKU. Controversial."},
    "E952":  {"name": "Cyclamate",             "category": "Sweetener",         "tier": "high_concern",     "description": "Banned in US. Possible carcinogen.",                                   "child_warning": "Avoid in children's food."},
    "E954":  {"name": "Saccharin",             "category": "Sweetener",         "tier": "moderate_concern", "description": "Artificial sweetener. Avoid for very young children.",                 "child_warning": "Avoid for infants/toddlers."},
    "E955":  {"name": "Sucralose",             "category": "Sweetener",         "tier": "moderate_concern", "description": "May alter gut microbiome. Long-term effects unclear.",                 "child_warning": "Long-term gut effects in children unclear."},
    # CI colour codes
    "CI 77891": {"name": "Titanium Dioxide",   "category": "Colorant",          "tier": "high_concern",     "description": "Possible carcinogen in nano form.",                                    "child_warning": "Nano-TiO2 may be carcinogenic. Avoid."},
    "CI 77491": {"name": "Iron Oxide Red",     "category": "Colorant",          "tier": "safe",             "description": "Natural iron oxide. Safe.",                                            "child_warning": None},
    "CI 77492": {"name": "Iron Oxide Yellow",  "category": "Colorant",          "tier": "safe",             "description": "Natural iron oxide. Safe.",                                            "child_warning": None},
    "CI 77499": {"name": "Iron Oxide Black",   "category": "Colorant",          "tier": "safe",             "description": "Natural iron oxide. Safe.",                                            "child_warning": None},
    "CI 16035": {"name": "Allura Red",         "category": "Colorant",          "tier": "high_concern",     "description": "Synthetic red dye. Linked to hyperactivity.",                          "child_warning": "Linked to hyperactivity. Avoid."},
    "CI 19140": {"name": "Tartrazine",         "category": "Colorant",          "tier": "high_concern",     "description": "Synthetic yellow dye. Linked to hyperactivity.",                       "child_warning": "Linked to hyperactivity. Avoid."},
    "CI 42090": {"name": "Brilliant Blue FCF", "category": "Colorant",          "tier": "moderate_concern", "description": "Synthetic blue dye.",                                                  "child_warning": None},
    "CI 45430": {"name": "Erythrosine",        "category": "Colorant",          "tier": "high_concern",     "description": "Thyroid disruptor.",                                                   "child_warning": "Thyroid disruptor. Avoid."},
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
            code  = normalizer(m)
            entry = CODE_ENTRIES.get(code)
            if entry:
                return code, entry
    return None, None


# ── DB risk → tier mapping ─────────────────────────────────────────────────────

def _db_risk_to_tier(risk_level: str, profile_flags: str = "") -> str:
    """Map DB risk_level + profile_flags to the 4-tier system."""
    rl = (risk_level or "unknown").lower()
    flags = {f.strip().lower() for f in (profile_flags or "").split(",") if f.strip()}

    if rl == "high":
        return "high_concern"
    if rl == "medium":
        return "moderate_concern"
    if rl == "low":
        # Upgrade to low_concern if any profile flag is set
        if flags - {""}:
            return "low_concern"
        return "safe"
    return "unknown"


# ── Profile-specific warning ───────────────────────────────────────────────────

def _profile_warning(flags_str: str | None, profile: str) -> str | None:
    if not flags_str:
        return None
    flags = {f.strip().lower() for f in flags_str.split(",") if f.strip()}
    msgs  = []
    if profile == "children" and "children"  in flags: msgs.append("Not recommended for children")
    if profile == "pregnant" and "pregnant"  in flags: msgs.append("Use caution during pregnancy")
    if profile == "elderly"  and "elderly"   in flags: msgs.append("Use caution for elderly")
    if "allergen" in flags: msgs.append("Potential allergen — check sensitivity")
    return ". ".join(msgs) if msgs else None


# ── Grade calculation ──────────────────────────────────────────────────────────

_TIER_SCORE = {"high_concern": 10, "moderate_concern": 4,
               "low_concern": 2, "safe": 1, "unknown": 3}

def _compute_grade(ingredients: list[dict]) -> tuple[str, float]:
    if not ingredients:
        return "A", 0.0
    total   = sum(_TIER_SCORE.get(r["tier"], 3) for r in ingredients)
    norm    = min(100.0, (total / len(ingredients)) * 10)
    if   norm <= 10: grade = "A"
    elif norm <= 25: grade = "B"
    elif norm <= 45: grade = "C"
    elif norm <= 65: grade = "D"
    else:            grade = "F"
    return grade, round(norm, 1)


# ── Main analysis ──────────────────────────────────────────────────────────────

def analyze_ingredients(
    raw_text:  str,
    profile:   str  = "general",
    is_ocr:    bool = False,
) -> dict:
    """
    Full pipeline.

    Args:
        raw_text – pasted ingredient text OR raw OCR dump
        profile  – general | children | pregnant | elderly
        is_ocr   – True ⟹ run section extraction + noise removal first
    """
    extraction_meta: dict = {}

    if is_ocr and raw_text.strip():
        sec             = extract_ingredient_section(raw_text)
        extraction_meta["section"] = sec
        cleaned         = clean_ocr_noise(sec["section"])
        extraction_meta["cleaning"] = cleaned
        work_text       = cleaned["cleaned"]
    else:
        work_text = raw_text

    # Load DB + build split index (single vs multi-word)
    all_db, _ = get_all_ingredients(limit=3000)
    db_single, db_multi, db_map = build_db_index(all_db)

    # Tokenise (depth-aware, preserves parenthetical phrases)
    tokens = tokenize_ingredient_section(work_text)

    results:   list[dict] = []
    rejected:  list[dict] = []
    seen:      set[str]   = set()

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        # ── Validate ──────────────────────────────────────────────────────────
        valid, reason = is_valid_ingredient_token(token)
        if not valid:
            rejected.append({"token": token, "reason": reason})
            continue

        # ── Code detection (E-numbers, INS, CI) ──────────────────────────────
        code, ce = _detect_code(token)
        if ce:
            key = code
            if key in seen:
                continue
            seen.add(key)

            tier = ce["tier"]
            cw   = ce.get("child_warning")
            prof_warn = None
            if profile == "children" and tier in ("high_concern", "moderate_concern"):
                prof_warn = cw or f"{ce['name']} carries a {tier.replace('_',' ')} risk."
            if profile == "pregnant" and tier in ("high_concern", "moderate_concern"):
                prof_warn = (prof_warn or "") + " Use caution during pregnancy."
            if profile == "elderly"  and tier == "high_concern":
                prof_warn = (prof_warn or "") + " Use caution for elderly."

            results.append({
                "raw":           token,
                "name":          ce["name"],
                "code":          code,
                "category":      ce["category"],
                "tier":          tier,
                "risk_level":    _tier_to_risk_level(tier),
                "description":   ce["description"],
                "safety_notes":  ce.get("description", ""),
                "warning":       prof_warn,
                "child_warning": cw,
                "matched":       True,
                "match_source":  "code_table",
                "confidence":    1.0,
            })
            continue

        # ── Fuzzy DB match (strict, anti-hallucination) ───────────────────────
        t_norm   = _norm(token)
        t_words  = [w for w in t_norm.split() if len(w) > 2]
        primary  = " ".join(t_words[:4])     # use up to 4 significant words
        if not primary:
            rejected.append({"token": token, "reason": "normalised to empty string"})
            continue

        fm = fuzzy_match_strict(primary, db_single, db_multi, db_map)

        if fm["matched"]:
            row  = fm["ingredient"]
            key  = _norm(row["name"])
            if key in seen:
                continue
            seen.add(key)

            tier        = _db_risk_to_tier(row["risk_level"], row.get("profile_flags", ""))
            safety_notes= row.get("safety_notes") or ""
            prof_warn   = _profile_warning(row.get("profile_flags"), profile)
            warning     = ". ".join(filter(None, [safety_notes, prof_warn])) or None

            # Child-specific warning
            flags   = {f.strip().lower() for f in (row.get("profile_flags") or "").split(",") if f.strip()}
            cw      = f"{row['name']} is flagged as not recommended for children." if "children" in flags else None

            try:
                increment_match_stat(row["id"])
            except Exception:
                pass

            results.append({
                "raw":           token,
                "name":          row["name"],
                "code":          row.get("code", ""),
                "category":      row.get("category", ""),
                "tier":          tier,
                "risk_level":    row["risk_level"],
                "description":   row.get("description", ""),
                "safety_notes":  safety_notes,
                "warning":       warning,
                "child_warning": cw,
                "matched":       True,
                "match_source":  "db_fuzzy",
                "confidence":    fm["confidence"],
            })
        else:
            # Unknown: include as-is, no hallucinated name
            key = t_norm
            if key in seen:
                continue
            seen.add(key)

            rejected_reason = fm.get("rejected_reason", "")
            if rejected_reason:
                rejected.append({"token": token, "reason": rejected_reason})
                continue

            results.append({
                "raw":           token,
                "name":          token,
                "code":          "",
                "category":      "",
                "tier":          "unknown",
                "risk_level":    "unknown",
                "description":   "",
                "safety_notes":  "",
                "warning":       None,
                "child_warning": None,
                "matched":       False,
                "match_source":  "none",
                "confidence":    0.0,
            })

    # ── Score and grade ────────────────────────────────────────────────────────
    grade, risk_score = _compute_grade(results)

    # Counts (backward-compat: also expose old risk_level keys)
    tier_counts = {t: 0 for t in TIERS}
    counts      = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    for r in results:
        tier_counts[r["tier"]] = tier_counts.get(r["tier"], 0) + 1
        rl = r["risk_level"]
        counts[rl] = counts.get(rl, 0) + 1

    # Grouped output
    groups: dict[str, list] = {t: [] for t in TIERS}
    for r in results:
        groups[r["tier"]].append(r)

    # Child warnings
    child_warnings = [{"name": r["name"], "warning": r["child_warning"]}
                      for r in results if r.get("child_warning")]

    # OCR extraction stats
    ocr_stats = None
    if is_ocr and extraction_meta:
        sec   = extraction_meta.get("section", {})
        clean = extraction_meta.get("cleaning", {})
        ocr_stats = {
            "start_keyword":       sec.get("start_keyword"),
            "stop_keyword":        sec.get("stop_keyword"),
            "section_found":       sec.get("start_found", False),
            "section_confidence":  sec.get("ocr_confidence", 0.0),
            "full_text_used":      sec.get("full_text_used", True),
            "noise_removed":       clean.get("noise_count", 0),
            "removal_stats":       clean.get("removal_stats", {}),
            "noise_items":         clean.get("removed", [])[:25],
            "cleaned_text":        clean.get("cleaned", ""),
        }

    avg_conf = (
        sum(r["confidence"] for r in results if r["matched"]) /
        max(1, sum(1 for r in results if r["matched"]))
    )

    return {
        "ingredients":    results,
        "groups":         groups,
        "grade":          grade,
        "risk_score":     risk_score,
        "profile":        profile,
        "counts":         counts,
        "tier_counts":    tier_counts,
        "total":          len(results),
        "rejected":       rejected,
        "child_warnings": child_warnings,
        "avg_confidence": round(avg_conf, 3),
        "ocr_stats":      ocr_stats,
    }


def _tier_to_risk_level(tier: str) -> str:
    return {
        "safe":             "low",
        "low_concern":      "low",
        "moderate_concern": "medium",
        "high_concern":     "high",
    }.get(tier, "unknown")
