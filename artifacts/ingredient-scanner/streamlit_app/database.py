import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "safescan.db"

SEED_INGREDIENTS = [
    # E-numbers / Food Additives
    {"name": "Curcumin", "code": "E100", "category": "Colorant", "risk_level": "low", "description": "Natural yellow color from turmeric. Generally safe.", "safety_notes": "Generally recognized as safe.", "profile_flags": ""},
    {"name": "Riboflavin (Vitamin B2)", "code": "E101", "category": "Colorant", "risk_level": "low", "description": "Natural yellow color, also a nutrient.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Tartrazine", "code": "E102", "category": "Colorant", "risk_level": "high", "description": "Synthetic yellow dye linked to hyperactivity in children and allergic reactions.", "safety_notes": "Avoid for children. May cause allergic reactions.", "profile_flags": "children,allergen"},
    {"name": "Quinoline Yellow", "code": "E104", "category": "Colorant", "risk_level": "medium", "description": "Synthetic dye. May cause hyperactivity; banned in some countries.", "safety_notes": "Use caution.", "profile_flags": "children"},
    {"name": "Sunset Yellow FCF", "code": "E110", "category": "Colorant", "risk_level": "high", "description": "Synthetic orange dye linked to hyperactivity, allergic reactions, and potential carcinogenicity.", "safety_notes": "Avoid for children and sensitive individuals.", "profile_flags": "children,allergen"},
    {"name": "Carmine (Cochineal)", "code": "E120", "category": "Colorant", "risk_level": "medium", "description": "Red dye from insects. Can cause severe allergic reactions.", "safety_notes": "May cause allergic reactions.", "profile_flags": "allergen"},
    {"name": "Carmoisine", "code": "E122", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye. Linked to hyperactivity and allergic reactions.", "safety_notes": "Avoid for children.", "profile_flags": "children,allergen"},
    {"name": "Amaranth", "code": "E123", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye. Banned in the US. Potential carcinogen.", "safety_notes": "Avoid. Banned in some countries.", "profile_flags": "children,pregnant,elderly"},
    {"name": "Ponceau 4R", "code": "E124", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye. Linked to hyperactivity and allergic reactions.", "safety_notes": "Avoid for children.", "profile_flags": "children,allergen"},
    {"name": "Erythrosine", "code": "E127", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye. Potential thyroid disruptor.", "safety_notes": "Potential thyroid disruptor.", "profile_flags": "pregnant,elderly"},
    {"name": "Allura Red AC", "code": "E129", "category": "Colorant", "risk_level": "high", "description": "Synthetic red dye. Linked to hyperactivity in children.", "safety_notes": "Avoid for children.", "profile_flags": "children"},
    {"name": "Patent Blue V", "code": "E131", "category": "Colorant", "risk_level": "medium", "description": "Synthetic blue dye. May cause allergic reactions.", "safety_notes": "May cause allergic reactions.", "profile_flags": "allergen"},
    {"name": "Indigotine", "code": "E132", "category": "Colorant", "risk_level": "medium", "description": "Synthetic blue dye. Can cause nausea and allergic reactions.", "safety_notes": "May cause reactions.", "profile_flags": ""},
    {"name": "Brilliant Blue FCF", "code": "E133", "category": "Colorant", "risk_level": "medium", "description": "Synthetic blue dye. May cause allergic reactions.", "safety_notes": "May cause allergic reactions.", "profile_flags": "allergen"},
    {"name": "Caramel Color I", "code": "E150a", "category": "Colorant", "risk_level": "low", "description": "Plain caramel color, generally safe.", "safety_notes": "Generally safe.", "profile_flags": ""},
    {"name": "Caramel Color IV", "code": "E150d", "category": "Colorant", "risk_level": "medium", "description": "Sulfite-ammonia caramel. Contains 4-MEI, a possible carcinogen.", "safety_notes": "Contains possible carcinogen 4-MEI.", "profile_flags": "pregnant"},
    {"name": "Brilliant Black BN", "code": "E151", "category": "Colorant", "risk_level": "medium", "description": "Synthetic black dye. May cause hyperactivity.", "safety_notes": "May cause hyperactivity.", "profile_flags": "children"},
    {"name": "Beta-carotene", "code": "E160a", "category": "Colorant", "risk_level": "low", "description": "Natural orange color from carrots. Safe and nutritious.", "safety_notes": "Beneficial nutrient.", "profile_flags": ""},
    {"name": "Titanium Dioxide", "code": "E171", "category": "Colorant", "risk_level": "high", "description": "White colorant. Possible carcinogen; banned in France.", "safety_notes": "Avoid if possible. Banned in France.", "profile_flags": "pregnant,children"},
    {"name": "Sorbic Acid", "code": "E200", "category": "Preservative", "risk_level": "low", "description": "Preservative from berries. Generally recognized as safe.", "safety_notes": "Generally safe.", "profile_flags": ""},
    {"name": "Potassium Sorbate", "code": "E202", "category": "Preservative", "risk_level": "low", "description": "Common food preservative. Generally safe in small amounts.", "safety_notes": "Generally safe.", "profile_flags": ""},
    {"name": "Benzoic Acid", "code": "E210", "category": "Preservative", "risk_level": "medium", "description": "Preservative that can form benzene (carcinogen) with Vitamin C.", "safety_notes": "Avoid combining with Vitamin C.", "profile_flags": ""},
    {"name": "Sodium Benzoate", "code": "E211", "category": "Preservative", "risk_level": "high", "description": "Preservative linked to hyperactivity in children. Can form carcinogenic benzene with Vitamin C.", "safety_notes": "Avoid for children.", "profile_flags": "children"},
    {"name": "Potassium Benzoate", "code": "E212", "category": "Preservative", "risk_level": "high", "description": "Similar to sodium benzoate. Linked to hyperactivity and potential carcinogen.", "safety_notes": "Avoid for children.", "profile_flags": "children"},
    {"name": "Sulphur Dioxide", "code": "E220", "category": "Preservative", "risk_level": "high", "description": "Preservative. Can trigger asthma attacks.", "safety_notes": "Avoid if asthmatic.", "profile_flags": "elderly,allergen"},
    {"name": "Sodium Sulphite", "code": "E221", "category": "Preservative", "risk_level": "high", "description": "Can cause severe allergic reactions in sulfite-sensitive individuals.", "safety_notes": "Potential allergen.", "profile_flags": "allergen"},
    {"name": "Sodium Nitrite", "code": "E250", "category": "Preservative", "risk_level": "high", "description": "Preservative in cured meats. Can form carcinogenic nitrosamines.", "safety_notes": "Limit consumption in cured meats.", "profile_flags": "pregnant,children"},
    {"name": "Sodium Nitrate", "code": "E251", "category": "Preservative", "risk_level": "high", "description": "Preservative in cured meats. Potential carcinogen.", "safety_notes": "Limit consumption.", "profile_flags": "pregnant,children"},
    {"name": "Acetic Acid", "code": "E260", "category": "Acidity Regulator", "risk_level": "low", "description": "Common acidity regulator (vinegar). Generally safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Lactic Acid", "code": "E270", "category": "Acidity Regulator", "risk_level": "low", "description": "Natural fermentation product. Safe for most people.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Ascorbic Acid", "code": "E300", "category": "Antioxidant", "risk_level": "low", "description": "Vitamin C antioxidant. Beneficial nutrient.", "safety_notes": "Beneficial nutrient.", "profile_flags": ""},
    {"name": "Butylated Hydroxytoluene (BHT)", "code": "E321", "category": "Antioxidant", "risk_level": "high", "description": "Synthetic antioxidant. Potential endocrine disruptor and carcinogen at high doses.", "safety_notes": "Potential endocrine disruptor.", "profile_flags": "pregnant,children"},
    {"name": "Butylated Hydroxyanisole (BHA)", "code": "E320", "category": "Antioxidant", "risk_level": "high", "description": "Synthetic antioxidant. Probable carcinogen.", "safety_notes": "Avoid if possible.", "profile_flags": "pregnant,children"},
    {"name": "Citric Acid", "code": "E330", "category": "Acidity Regulator", "risk_level": "low", "description": "Common natural acid. Generally safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Carrageenan", "code": "E407", "category": "Thickener", "risk_level": "medium", "description": "Seaweed-derived thickener. May cause inflammation in the digestive system.", "safety_notes": "May cause digestive inflammation.", "profile_flags": "elderly"},
    {"name": "Sorbitol", "code": "E420", "category": "Sweetener", "risk_level": "medium", "description": "Sugar alcohol. Can cause digestive issues in large amounts.", "safety_notes": "Can cause digestive upset.", "profile_flags": ""},
    {"name": "Mannitol", "code": "E421", "category": "Sweetener", "risk_level": "medium", "description": "Sugar alcohol. Can cause digestive issues.", "safety_notes": "Can cause digestive upset.", "profile_flags": ""},
    {"name": "Diphosphates", "code": "E450", "category": "Emulsifier", "risk_level": "medium", "description": "Phosphate additive. Excess phosphate linked to kidney issues.", "safety_notes": "Excess may affect kidney function.", "profile_flags": "elderly"},
    {"name": "Mono- and Diglycerides", "code": "E471", "category": "Emulsifier", "risk_level": "low", "description": "Common emulsifier. Generally safe but may contain trans fats.", "safety_notes": "Generally safe.", "profile_flags": ""},
    {"name": "Monosodium Glutamate (MSG)", "code": "E621", "category": "Flavor Enhancer", "risk_level": "medium", "description": "Flavor enhancer. May cause headaches in sensitive individuals.", "safety_notes": "Sensitivity varies by individual.", "profile_flags": ""},
    {"name": "Disodium Guanylate", "code": "E627", "category": "Flavor Enhancer", "risk_level": "medium", "description": "Flavor enhancer. Avoid if sensitive to purines (gout).", "safety_notes": "Avoid with gout.", "profile_flags": "elderly"},
    {"name": "Disodium Inosinate", "code": "E631", "category": "Flavor Enhancer", "risk_level": "medium", "description": "Flavor enhancer. Avoid if sensitive to purines.", "safety_notes": "Avoid with gout.", "profile_flags": "elderly"},
    {"name": "Aspartame", "code": "E951", "category": "Sweetener", "risk_level": "high", "description": "Artificial sweetener. Possible carcinogen (Group 2B WHO). Avoid for phenylketonuria.", "safety_notes": "Avoid with PKU. Controversial safety profile.", "profile_flags": "pregnant,children"},
    {"name": "Cyclamate", "code": "E952", "category": "Sweetener", "risk_level": "high", "description": "Artificial sweetener. Banned in the US. Possible carcinogen.", "safety_notes": "Banned in USA.", "profile_flags": "pregnant"},
    {"name": "Saccharin", "code": "E954", "category": "Sweetener", "risk_level": "medium", "description": "Artificial sweetener. Previously linked to bladder cancer in animals.", "safety_notes": "Use in moderation.", "profile_flags": "pregnant"},
    {"name": "Sucralose", "code": "E955", "category": "Sweetener", "risk_level": "medium", "description": "Artificial sweetener. May alter gut microbiome.", "safety_notes": "Generally considered safe.", "profile_flags": ""},
    # Common food ingredients
    {"name": "Water", "code": "", "category": "Base", "risk_level": "low", "description": "Pure water. Essential and safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Sugar", "code": "", "category": "Sweetener", "risk_level": "low", "description": "Common sweetener. Safe in moderation.", "safety_notes": "Limit intake for diabetes management.", "profile_flags": ""},
    {"name": "Salt", "code": "", "category": "Seasoning", "risk_level": "low", "description": "Common seasoning. Safe in moderation.", "safety_notes": "High intake linked to hypertension.", "profile_flags": "elderly"},
    {"name": "Sodium Chloride", "code": "", "category": "Seasoning", "risk_level": "low", "description": "Table salt. Safe in moderation.", "safety_notes": "High intake may raise blood pressure.", "profile_flags": "elderly"},
    {"name": "Palm Oil", "code": "", "category": "Fat/Oil", "risk_level": "medium", "description": "Vegetable oil high in saturated fats.", "safety_notes": "High in saturated fat; limit intake.", "profile_flags": "elderly"},
    {"name": "Sunflower Oil", "code": "", "category": "Fat/Oil", "risk_level": "low", "description": "Common vegetable oil. Generally safe.", "safety_notes": "Safe in moderation.", "profile_flags": ""},
    {"name": "Vegetable Oil", "code": "", "category": "Fat/Oil", "risk_level": "low", "description": "Common cooking oil. Generally safe.", "safety_notes": "Safe in moderation.", "profile_flags": ""},
    {"name": "Modified Starch", "code": "", "category": "Thickener", "risk_level": "low", "description": "Chemically modified starch. Generally safe.", "safety_notes": "Safe for most people.", "profile_flags": ""},
    {"name": "Wheat Flour", "code": "", "category": "Grain", "risk_level": "low", "description": "Common flour. Contains gluten.", "safety_notes": "Avoid with celiac disease.", "profile_flags": "allergen"},
    {"name": "Corn Syrup", "code": "", "category": "Sweetener", "risk_level": "medium", "description": "High-fructose corn syrup. Linked to obesity and metabolic disorders.", "safety_notes": "Limit intake.", "profile_flags": ""},
    {"name": "High Fructose Corn Syrup", "code": "", "category": "Sweetener", "risk_level": "high", "description": "Highly processed sweetener. Linked to obesity, diabetes, and metabolic disorders.", "safety_notes": "Limit intake significantly.", "profile_flags": "children,elderly"},
    {"name": "Fructose", "code": "", "category": "Sweetener", "risk_level": "medium", "description": "Fruit sugar. High intake linked to metabolic issues.", "safety_notes": "Limit excessive intake.", "profile_flags": ""},
    {"name": "Glucose", "code": "", "category": "Sweetener", "risk_level": "low", "description": "Simple sugar. Safe in moderation.", "safety_notes": "Monitor with diabetes.", "profile_flags": ""},
    {"name": "Natural Flavors", "code": "", "category": "Flavor", "risk_level": "low", "description": "Derived from natural sources. Generally safe.", "safety_notes": "May contain allergens.", "profile_flags": "allergen"},
    {"name": "Artificial Flavors", "code": "", "category": "Flavor", "risk_level": "medium", "description": "Synthetically produced flavor compounds.", "safety_notes": "May cause reactions in sensitive individuals.", "profile_flags": ""},
    {"name": "Milk", "code": "", "category": "Dairy", "risk_level": "low", "description": "Common dairy ingredient. Contains lactose and milk proteins.", "safety_notes": "Avoid with dairy allergy or lactose intolerance.", "profile_flags": "allergen"},
    {"name": "Soy Lecithin", "code": "", "category": "Emulsifier", "risk_level": "low", "description": "Emulsifier from soybeans. Generally safe.", "safety_notes": "Avoid with soy allergy.", "profile_flags": "allergen"},
    {"name": "Lecithin", "code": "", "category": "Emulsifier", "risk_level": "low", "description": "Common emulsifier. Generally safe.", "safety_notes": "Generally safe.", "profile_flags": ""},
    {"name": "Xanthan Gum", "code": "", "category": "Thickener", "risk_level": "low", "description": "Natural thickener. Generally safe.", "safety_notes": "Safe for most people.", "profile_flags": ""},
    {"name": "Guar Gum", "code": "", "category": "Thickener", "risk_level": "low", "description": "Natural thickener from guar beans. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Sodium Lauryl Sulfate", "code": "SLS", "category": "Surfactant", "risk_level": "medium", "description": "Common surfactant in personal care products. May irritate skin and mucous membranes.", "safety_notes": "May cause skin and oral irritation.", "profile_flags": "children"},
    {"name": "Sodium Laureth Sulfate", "code": "SLES", "category": "Surfactant", "risk_level": "medium", "description": "Common detergent in personal care products.", "safety_notes": "May be contaminated with 1,4-dioxane.", "profile_flags": ""},
    {"name": "Parabens", "code": "", "category": "Preservative", "risk_level": "high", "description": "Synthetic preservatives. Possible endocrine disruptors.", "safety_notes": "Potential hormone disruptors. Avoid in personal care.", "profile_flags": "pregnant,children"},
    {"name": "Methylparaben", "code": "", "category": "Preservative", "risk_level": "high", "description": "Paraben preservative. Possible endocrine disruptor.", "safety_notes": "Possible hormone disruptor.", "profile_flags": "pregnant,children"},
    {"name": "Propylparaben", "code": "", "category": "Preservative", "risk_level": "high", "description": "Paraben preservative. Possible endocrine disruptor.", "safety_notes": "Possible hormone disruptor.", "profile_flags": "pregnant,children"},
    {"name": "Formaldehyde", "code": "", "category": "Preservative", "risk_level": "high", "description": "Known carcinogen used in some cosmetics. Avoid.", "safety_notes": "Known carcinogen. Avoid.", "profile_flags": "pregnant,children,elderly"},
    {"name": "Phthalates", "code": "", "category": "Plasticizer", "risk_level": "high", "description": "Endocrine-disrupting chemicals found in some personal care products.", "safety_notes": "Endocrine disruptors. Avoid.", "profile_flags": "pregnant,children"},
    {"name": "Triclosan", "code": "", "category": "Antimicrobial", "risk_level": "high", "description": "Antimicrobial agent. Endocrine disruptor, banned in some products.", "safety_notes": "Endocrine disruptor. Largely banned.", "profile_flags": "pregnant,children"},
    {"name": "Talc", "code": "", "category": "Filler", "risk_level": "medium", "description": "Mineral powder used in personal care. May be contaminated with asbestos.", "safety_notes": "Risk of asbestos contamination in some sources.", "profile_flags": "pregnant,children"},
    {"name": "Mineral Oil", "code": "", "category": "Emollient", "risk_level": "medium", "description": "Petroleum-derived oil. May clog pores; some forms contain impurities.", "safety_notes": "Use refined cosmetic grade only.", "profile_flags": ""},
    {"name": "Fragrance", "code": "", "category": "Fragrance", "risk_level": "medium", "description": "Undisclosed fragrance blend. May contain allergens.", "safety_notes": "May contain hidden allergens.", "profile_flags": "allergen,pregnant"},
    {"name": "Parfum", "code": "", "category": "Fragrance", "risk_level": "medium", "description": "Undisclosed fragrance blend. May contain allergens.", "safety_notes": "May contain hidden allergens.", "profile_flags": "allergen,pregnant"},
    {"name": "Alcohol Denat", "code": "", "category": "Solvent", "risk_level": "low", "description": "Denatured alcohol used in personal care. Generally safe topically.", "safety_notes": "Can be drying for sensitive skin.", "profile_flags": ""},
    {"name": "Glycerin", "code": "", "category": "Humectant", "risk_level": "low", "description": "Natural humectant. Safe and beneficial for skin.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Propylene Glycol", "code": "", "category": "Humectant", "risk_level": "medium", "description": "Synthetic humectant. May cause skin reactions in sensitive individuals.", "safety_notes": "May irritate sensitive skin.", "profile_flags": ""},
    {"name": "Niacinamide", "code": "", "category": "Active", "risk_level": "low", "description": "Vitamin B3 derivative. Beneficial skin ingredient.", "safety_notes": "Generally safe and beneficial.", "profile_flags": ""},
    {"name": "Retinol", "code": "", "category": "Active", "risk_level": "medium", "description": "Vitamin A derivative. Avoid during pregnancy.", "safety_notes": "Avoid during pregnancy.", "profile_flags": "pregnant"},
    {"name": "Hyaluronic Acid", "code": "", "category": "Humectant", "risk_level": "low", "description": "Natural humectant. Safe and beneficial.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Salicylic Acid", "code": "", "category": "Exfoliant", "risk_level": "medium", "description": "BHA exfoliant. Avoid during pregnancy.", "safety_notes": "Avoid during pregnancy in high concentrations.", "profile_flags": "pregnant"},
    {"name": "Benzoyl Peroxide", "code": "", "category": "Antimicrobial", "risk_level": "medium", "description": "Acne treatment ingredient. Can cause skin irritation.", "safety_notes": "May cause bleaching and irritation.", "profile_flags": "pregnant"},
    {"name": "Hydroquinone", "code": "", "category": "Brightening", "risk_level": "high", "description": "Skin lightening agent. Possible carcinogen; banned in EU cosmetics.", "safety_notes": "Banned in EU. Use with caution.", "profile_flags": "pregnant,children"},
    {"name": "Oxybenzone", "code": "", "category": "UV Filter", "risk_level": "high", "description": "Chemical UV filter. Potential endocrine disruptor.", "safety_notes": "Possible endocrine disruptor. Choose alternatives.", "profile_flags": "pregnant,children"},
    {"name": "Octinoxate", "code": "", "category": "UV Filter", "risk_level": "medium", "description": "Chemical UV filter. Possible endocrine disruptor.", "safety_notes": "Use with caution.", "profile_flags": "pregnant"},
    {"name": "Zinc Oxide", "code": "", "category": "UV Filter", "risk_level": "low", "description": "Mineral UV filter. Generally safe.", "safety_notes": "Safe. Preferred UV filter.", "profile_flags": ""},
    {"name": "Titanium Dioxide (CI 77891)", "code": "CI 77891", "category": "Colorant", "risk_level": "high", "description": "White pigment. Possible carcinogen when inhaled or ingested.", "safety_notes": "Possible carcinogen in nano form.", "profile_flags": "pregnant,children"},
    {"name": "Iron Oxide Red", "code": "CI 77491", "category": "Colorant", "risk_level": "low", "description": "Natural red iron oxide. Generally safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Iron Oxide Yellow", "code": "CI 77492", "category": "Colorant", "risk_level": "low", "description": "Natural yellow iron oxide. Generally safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Iron Oxide Black", "code": "CI 77499", "category": "Colorant", "risk_level": "low", "description": "Natural black iron oxide. Generally safe.", "safety_notes": "Safe.", "profile_flags": ""},
    # Cosmetic-specific
    {"name": "Cetyl Alcohol", "code": "", "category": "Emollient", "risk_level": "low", "description": "Fatty alcohol used as emollient. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Stearic Acid", "code": "", "category": "Emollient", "risk_level": "low", "description": "Fatty acid emollient. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Dimethicone", "code": "", "category": "Silicone", "risk_level": "low", "description": "Silicone-based ingredient. Generally safe.", "safety_notes": "Safe. May clog pores in some formulas.", "profile_flags": ""},
    {"name": "Phenoxyethanol", "code": "", "category": "Preservative", "risk_level": "medium", "description": "Common preservative. Generally safe at low concentrations.", "safety_notes": "Safe at <1% concentration.", "profile_flags": ""},
    {"name": "EDTA", "code": "", "category": "Chelating Agent", "risk_level": "low", "description": "Chelating agent. Generally safe in cosmetics.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Carbomer", "code": "", "category": "Thickener", "risk_level": "low", "description": "Synthetic thickener. Generally safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Kaolin", "code": "", "category": "Absorbent", "risk_level": "low", "description": "Natural clay. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Mica", "code": "", "category": "Colorant", "risk_level": "low", "description": "Natural mineral for shimmer. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Beeswax", "code": "", "category": "Emollient", "risk_level": "low", "description": "Natural wax. Generally safe.", "safety_notes": "Safe. Not vegan.", "profile_flags": ""},
    {"name": "Shea Butter", "code": "", "category": "Emollient", "risk_level": "low", "description": "Natural plant butter. Beneficial and safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Aloe Vera", "code": "", "category": "Botanical", "risk_level": "low", "description": "Natural plant extract. Soothing and safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Tea Tree Oil", "code": "", "category": "Botanical", "risk_level": "medium", "description": "Essential oil with antimicrobial properties. May be irritating.", "safety_notes": "Use diluted. Can irritate.", "profile_flags": ""},
    {"name": "Lavender Oil", "code": "", "category": "Botanical", "risk_level": "low", "description": "Natural essential oil. Generally safe.", "safety_notes": "May cause reactions in sensitive individuals.", "profile_flags": "pregnant"},
    # Food allergens
    {"name": "Peanut Oil", "code": "", "category": "Fat/Oil", "risk_level": "high", "description": "Oil from peanuts. Major allergen.", "safety_notes": "Major allergen. Avoid with peanut allergy.", "profile_flags": "allergen,children"},
    {"name": "Tree Nuts", "code": "", "category": "Nut", "risk_level": "high", "description": "Various tree nuts. Common allergen.", "safety_notes": "Major allergen.", "profile_flags": "allergen,children"},
    {"name": "Shellfish Extract", "code": "", "category": "Seafood", "risk_level": "high", "description": "Shellfish derivative. Major allergen.", "safety_notes": "Major allergen.", "profile_flags": "allergen"},
    {"name": "Egg", "code": "", "category": "Animal Product", "risk_level": "low", "description": "Common food ingredient. Allergen for some.", "safety_notes": "Common allergen.", "profile_flags": "allergen"},
    {"name": "Gluten", "code": "", "category": "Protein", "risk_level": "medium", "description": "Wheat protein. Causes celiac disease in sensitive individuals.", "safety_notes": "Avoid with celiac disease.", "profile_flags": "allergen"},
    {"name": "Lactose", "code": "", "category": "Dairy", "risk_level": "low", "description": "Milk sugar. May cause digestive issues in lactose-intolerant individuals.", "safety_notes": "Avoid with lactose intolerance.", "profile_flags": "allergen"},
    {"name": "Casein", "code": "", "category": "Dairy", "risk_level": "low", "description": "Milk protein. Allergen for some.", "safety_notes": "Dairy allergen.", "profile_flags": "allergen"},
    {"name": "Whey", "code": "", "category": "Dairy", "risk_level": "low", "description": "Milk byproduct. Allergen for some.", "safety_notes": "Dairy allergen.", "profile_flags": "allergen"},
    # Additional common additives
    {"name": "Sodium Bicarbonate", "code": "", "category": "Leavening Agent", "risk_level": "low", "description": "Baking soda. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Baking Powder", "code": "", "category": "Leavening Agent", "risk_level": "low", "description": "Leavening agent. Generally safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Yeast", "code": "", "category": "Leavening Agent", "risk_level": "low", "description": "Natural leavening agent. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Vinegar", "code": "", "category": "Acidity Regulator", "risk_level": "low", "description": "Natural acidity regulator. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Cocoa", "code": "", "category": "Flavoring", "risk_level": "low", "description": "Natural cocoa. Generally safe.", "safety_notes": "Contains caffeine.", "profile_flags": "pregnant"},
    {"name": "Caffeine", "code": "", "category": "Stimulant", "risk_level": "medium", "description": "Stimulant. Limit intake during pregnancy.", "safety_notes": "Limit during pregnancy.", "profile_flags": "pregnant,children"},
    {"name": "Taurine", "code": "", "category": "Amino Acid", "risk_level": "medium", "description": "Amino acid supplement. Safe in moderate amounts.", "safety_notes": "Avoid excessive amounts.", "profile_flags": "children,pregnant"},
    {"name": "Niacin", "code": "", "category": "Vitamin", "risk_level": "low", "description": "Vitamin B3. Essential nutrient.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Vitamin E", "code": "", "category": "Vitamin", "risk_level": "low", "description": "Antioxidant vitamin. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Folic Acid", "code": "", "category": "Vitamin", "risk_level": "low", "description": "Essential B vitamin. Important during pregnancy.", "safety_notes": "Beneficial during pregnancy.", "profile_flags": ""},
    {"name": "Iron", "code": "", "category": "Mineral", "risk_level": "low", "description": "Essential mineral. Safe in food amounts.", "safety_notes": "Safe at normal levels.", "profile_flags": ""},
    {"name": "Sodium", "code": "", "category": "Mineral", "risk_level": "medium", "description": "Essential mineral. High intake linked to hypertension.", "safety_notes": "Limit excess intake.", "profile_flags": "elderly"},
    {"name": "Potassium", "code": "", "category": "Mineral", "risk_level": "low", "description": "Essential mineral. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Calcium Carbonate", "code": "", "category": "Mineral", "risk_level": "low", "description": "Calcium supplement and filler. Safe.", "safety_notes": "Safe.", "profile_flags": ""},
    {"name": "Magnesium Stearate", "code": "", "category": "Lubricant", "risk_level": "low", "description": "Common supplement lubricant. Safe in small amounts.", "safety_notes": "Safe.", "profile_flags": ""},
]


def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            category TEXT,
            risk_level TEXT NOT NULL DEFAULT 'low',
            description TEXT,
            safety_notes TEXT,
            profile_flags TEXT,
            source TEXT
        );

        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            grade TEXT NOT NULL,
            risk_score REAL NOT NULL,
            profile TEXT,
            result_json TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS ingredient_match_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER UNIQUE REFERENCES ingredients(id),
            match_count INTEGER NOT NULL DEFAULT 0
        );
    """)

    cur.execute("SELECT COUNT(*) FROM ingredients")
    count = cur.fetchone()[0]

    if count == 0:
        for ing in SEED_INGREDIENTS:
            cur.execute("""
                INSERT OR IGNORE INTO ingredients (name, code, category, risk_level, description, safety_notes, profile_flags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ing["name"], ing.get("code", ""), ing.get("category", ""),
                ing["risk_level"], ing.get("description", ""),
                ing.get("safety_notes", ""), ing.get("profile_flags", "")
            ))

    conn.commit()
    conn.close()


def search_ingredient(name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM ingredients
        WHERE LOWER(name) LIKE LOWER(?)
           OR LOWER(code) LIKE LOWER(?)
        LIMIT 1
    """, (f"%{name}%", f"%{name}%"))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_ingredients(search: str = "", category: str = "", risk: str = "", limit: int = 100, offset: int = 0):
    conn = get_connection()
    cur = conn.cursor()
    conditions = []
    params = []
    if search:
        conditions.append("(LOWER(name) LIKE LOWER(?) OR LOWER(code) LIKE LOWER(?) OR LOWER(category) LIKE LOWER(?))")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if category:
        conditions.append("category = ?")
        params.append(category)
    if risk:
        conditions.append("risk_level = ?")
        params.append(risk)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    cur.execute(f"SELECT * FROM ingredients {where} ORDER BY name LIMIT ? OFFSET ?", params + [limit, offset])
    rows = cur.fetchall()
    cur.execute(f"SELECT COUNT(*) FROM ingredients {where}", params)
    total = cur.fetchone()[0]
    conn.close()
    return [dict(r) for r in rows], total


def get_categories():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT category FROM ingredients WHERE category != '' ORDER BY category")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def save_scan(product_name: str, raw_text: str, grade: str, risk_score: float, profile: str, result: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO scan_history (product_name, raw_text, grade, risk_score, profile, result_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (product_name, raw_text, grade, risk_score, profile, json.dumps(result)))
    conn.commit()
    conn.close()


def get_history(limit: int = 50):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scan_history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_scan_by_id(scan_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scan_history WHERE id = ?", (scan_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_scan(scan_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM scan_history WHERE id = ?", (scan_id,))
    conn.commit()
    conn.close()


def get_dashboard_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM scan_history")
    total_scans = cur.fetchone()[0]
    cur.execute("SELECT risk_level, COUNT(*) as cnt FROM ingredients GROUP BY risk_level")
    risk_dist = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT category, COUNT(*) as cnt FROM ingredients WHERE category != '' GROUP BY category ORDER BY cnt DESC LIMIT 10")
    categories = cur.fetchall()
    cur.execute("""
        SELECT i.name, i.risk_level, s.match_count
        FROM ingredient_match_stats s
        JOIN ingredients i ON s.ingredient_id = i.id
        ORDER BY s.match_count DESC LIMIT 10
    """)
    top_matched = cur.fetchall()
    cur.execute("SELECT grade, COUNT(*) as cnt FROM scan_history GROUP BY grade ORDER BY grade")
    grade_dist = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT risk_score FROM scan_history ORDER BY created_at DESC LIMIT 30")
    recent_scores = [r[0] for r in cur.fetchall()]
    conn.close()
    return {
        "total_scans": total_scans,
        "risk_dist": risk_dist,
        "categories": [(r[0], r[1]) for r in categories],
        "top_matched": [(r[0], r[1], r[2]) for r in top_matched],
        "grade_dist": grade_dist,
        "recent_scores": recent_scores,
    }


def increment_match_stat(ingredient_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ingredient_match_stats (ingredient_id, match_count)
        VALUES (?, 1)
        ON CONFLICT(ingredient_id) DO UPDATE SET match_count = match_count + 1
    """, (ingredient_id,))
    conn.commit()
    conn.close()
