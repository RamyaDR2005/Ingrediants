export interface CodeEntry {
  name: string;
  category: string;
  riskLevel: "low" | "medium" | "high";
  description: string;
}

// E-number mappings (common food additives)
export const E_NUMBERS: Record<string, CodeEntry> = {
  "E100": { name: "Curcumin", category: "Colorant", riskLevel: "low", description: "Natural yellow color from turmeric. Generally safe." },
  "E101": { name: "Riboflavin (Vitamin B2)", category: "Colorant", riskLevel: "low", description: "Natural yellow color, also a nutrient." },
  "E102": { name: "Tartrazine", category: "Colorant", riskLevel: "high", description: "Synthetic yellow dye linked to hyperactivity in children and allergic reactions." },
  "E104": { name: "Quinoline Yellow", category: "Colorant", riskLevel: "medium", description: "Synthetic dye. May cause hyperactivity; banned in some countries." },
  "E110": { name: "Sunset Yellow FCF", category: "Colorant", riskLevel: "high", description: "Synthetic orange dye linked to hyperactivity, allergic reactions, and potential carcinogenicity." },
  "E120": { name: "Carmine (Cochineal)", category: "Colorant", riskLevel: "medium", description: "Red dye from insects. Can cause severe allergic reactions." },
  "E122": { name: "Carmoisine", category: "Colorant", riskLevel: "high", description: "Synthetic red dye. Linked to hyperactivity and allergic reactions." },
  "E123": { name: "Amaranth", category: "Colorant", riskLevel: "high", description: "Synthetic red dye. Banned in the US. Potential carcinogen." },
  "E124": { name: "Ponceau 4R", category: "Colorant", riskLevel: "high", description: "Synthetic red dye. Linked to hyperactivity and allergic reactions." },
  "E127": { name: "Erythrosine", category: "Colorant", riskLevel: "high", description: "Synthetic red dye. Potential thyroid disruptor." },
  "E129": { name: "Allura Red AC", category: "Colorant", riskLevel: "high", description: "Synthetic red dye. Linked to hyperactivity in children." },
  "E131": { name: "Patent Blue V", category: "Colorant", riskLevel: "medium", description: "Synthetic blue dye. May cause allergic reactions." },
  "E132": { name: "Indigotine", category: "Colorant", riskLevel: "medium", description: "Synthetic blue dye. Can cause nausea and allergic reactions." },
  "E133": { name: "Brilliant Blue FCF", category: "Colorant", riskLevel: "medium", description: "Synthetic blue dye. May cause allergic reactions." },
  "E150a": { name: "Caramel Color I", category: "Colorant", riskLevel: "low", description: "Plain caramel color, generally safe." },
  "E150d": { name: "Caramel Color IV", category: "Colorant", riskLevel: "medium", description: "Sulfite-ammonia caramel. Contains 4-MEI, a possible carcinogen." },
  "E151": { name: "Brilliant Black BN", category: "Colorant", riskLevel: "medium", description: "Synthetic black dye. May cause hyperactivity." },
  "E160a": { name: "Beta-carotene", category: "Colorant", riskLevel: "low", description: "Natural orange color from carrots. Safe and nutritious." },
  "E171": { name: "Titanium Dioxide", category: "Colorant", riskLevel: "high", description: "White colorant. Possible carcinogen; banned in France. Avoid if possible." },
  "E200": { name: "Sorbic Acid", category: "Preservative", riskLevel: "low", description: "Preservative from berries. Generally recognized as safe." },
  "E202": { name: "Potassium Sorbate", category: "Preservative", riskLevel: "low", description: "Common food preservative. Generally safe in small amounts." },
  "E210": { name: "Benzoic Acid", category: "Preservative", riskLevel: "medium", description: "Preservative that can form benzene (carcinogen) with Vitamin C." },
  "E211": { name: "Sodium Benzoate", category: "Preservative", riskLevel: "high", description: "Preservative linked to hyperactivity in children. Can form carcinogenic benzene with Vitamin C." },
  "E212": { name: "Potassium Benzoate", category: "Preservative", riskLevel: "high", description: "Preservative similar to sodium benzoate. Linked to hyperactivity and potential carcinogen." },
  "E220": { name: "Sulphur Dioxide", category: "Preservative", riskLevel: "high", description: "Preservative and antioxidant. Can trigger asthma attacks; avoid if asthmatic." },
  "E221": { name: "Sodium Sulphite", category: "Preservative", riskLevel: "high", description: "Preservative. Can cause severe allergic reactions in sulfite-sensitive individuals." },
  "E250": { name: "Sodium Nitrite", category: "Preservative", riskLevel: "high", description: "Preservative in cured meats. Can form carcinogenic nitrosamines. Limit consumption." },
  "E251": { name: "Sodium Nitrate", category: "Preservative", riskLevel: "high", description: "Preservative in cured meats. Potential carcinogen through nitrosamine formation." },
  "E260": { name: "Acetic Acid (Vinegar)", category: "Acidity Regulator", riskLevel: "low", description: "Common acidity regulator. Generally safe." },
  "E270": { name: "Lactic Acid", category: "Acidity Regulator", riskLevel: "low", description: "Natural fermentation product. Safe for most people." },
  "E300": { name: "Ascorbic Acid (Vitamin C)", category: "Antioxidant", riskLevel: "low", description: "Antioxidant and vitamin. Beneficial nutrient." },
  "E321": { name: "Butylated Hydroxytoluene (BHT)", category: "Antioxidant", riskLevel: "high", description: "Synthetic antioxidant. Potential endocrine disruptor and carcinogen at high doses." },
  "E320": { name: "Butylated Hydroxyanisole (BHA)", category: "Antioxidant", riskLevel: "high", description: "Synthetic antioxidant. Probable carcinogen. Avoid if possible." },
  "E330": { name: "Citric Acid", category: "Acidity Regulator", riskLevel: "low", description: "Common natural acid. Generally safe." },
  "E407": { name: "Carrageenan", category: "Thickener", riskLevel: "medium", description: "Seaweed-derived thickener. May cause inflammation in the digestive system." },
  "E420": { name: "Sorbitol", category: "Sweetener", riskLevel: "medium", description: "Sugar alcohol sweetener. Can cause digestive issues in large amounts." },
  "E421": { name: "Mannitol", category: "Sweetener", riskLevel: "medium", description: "Sugar alcohol. Can cause digestive issues." },
  "E450": { name: "Diphosphates", category: "Emulsifier", riskLevel: "medium", description: "Phosphate additive. Excess phosphate linked to kidney issues." },
  "E471": { name: "Mono- and Diglycerides", category: "Emulsifier", riskLevel: "low", description: "Common emulsifier. Generally safe but may contain trans fats." },
  "E621": { name: "Monosodium Glutamate (MSG)", category: "Flavor Enhancer", riskLevel: "medium", description: "Flavor enhancer. May cause headaches and other symptoms in sensitive individuals." },
  "E627": { name: "Disodium Guanylate", category: "Flavor Enhancer", riskLevel: "medium", description: "Flavor enhancer. Avoid if sensitive to purines (gout)." },
  "E631": { name: "Disodium Inosinate", category: "Flavor Enhancer", riskLevel: "medium", description: "Flavor enhancer. Avoid if sensitive to purines." },
  "E951": { name: "Aspartame", category: "Sweetener", riskLevel: "high", description: "Artificial sweetener. Controversial — possible carcinogen (Group 2B WHO). Avoid for phenylketonuria." },
  "E952": { name: "Cyclamate", category: "Sweetener", riskLevel: "high", description: "Artificial sweetener. Banned in the US. Possible carcinogen." },
  "E954": { name: "Saccharin", category: "Sweetener", riskLevel: "medium", description: "Artificial sweetener. Previously linked to bladder cancer in animals." },
  "E955": { name: "Sucralose", category: "Sweetener", riskLevel: "medium", description: "Artificial sweetener. May alter gut microbiome. Generally considered safe." },
};

// INS numbers (International Numbering System - same as E-numbers numerically)
export const INS_NUMBERS: Record<string, CodeEntry> = Object.fromEntries(
  Object.entries(E_NUMBERS).map(([key, val]) => [key.replace("E", "INS "), val])
);

// CI codes (Color Index - cosmetic colorants)
export const CI_CODES: Record<string, CodeEntry> = {
  "CI 77891": { name: "Titanium Dioxide", category: "Colorant", riskLevel: "high", description: "White pigment. Possible carcinogen when inhaled or ingested in nano form." },
  "CI 77491": { name: "Iron Oxide Red", category: "Colorant", riskLevel: "low", description: "Natural red iron oxide. Generally safe." },
  "CI 77492": { name: "Iron Oxide Yellow", category: "Colorant", riskLevel: "low", description: "Natural yellow iron oxide. Generally safe." },
  "CI 77499": { name: "Iron Oxide Black", category: "Colorant", riskLevel: "low", description: "Natural black iron oxide. Generally safe." },
  "CI 19140": { name: "Tartrazine (FD&C Yellow 5)", category: "Colorant", riskLevel: "high", description: "Synthetic yellow dye. Linked to hyperactivity and allergic reactions." },
  "CI 15985": { name: "Sunset Yellow FCF", category: "Colorant", riskLevel: "high", description: "Synthetic orange dye. Linked to hyperactivity and allergic reactions." },
  "CI 16035": { name: "Allura Red (FD&C Red 40)", category: "Colorant", riskLevel: "high", description: "Synthetic red dye. Linked to hyperactivity in children." },
  "CI 42090": { name: "Brilliant Blue FCF (FD&C Blue 1)", category: "Colorant", riskLevel: "medium", description: "Synthetic blue dye. May cause allergic reactions." },
  "CI 73015": { name: "Indigo Carmine (FD&C Blue 2)", category: "Colorant", riskLevel: "medium", description: "Synthetic blue dye. May cause nausea." },
  "CI 45430": { name: "Erythrosine (FD&C Red 3)", category: "Colorant", riskLevel: "high", description: "Synthetic red dye. Potential thyroid disruptor." },
  "CI 42051": { name: "Patent Blue V", category: "Colorant", riskLevel: "medium", description: "Synthetic blue dye. May cause allergic reactions." },
  "CI 14720": { name: "Carmoisine", category: "Colorant", riskLevel: "high", description: "Synthetic red dye. Linked to hyperactivity." },
};

// Regex patterns for code detection
export const CODE_PATTERNS = [
  { regex: /\bE(\d{3,4}[a-z]?)\b/gi, prefix: "E", lookup: E_NUMBERS },
  { regex: /\bINS\s*(\d{3,4}[a-z]?)\b/gi, prefix: "INS ", lookup: INS_NUMBERS },
  { regex: /\bCI\s*(\d{5})\b/gi, prefix: "CI ", lookup: CI_CODES },
];

export function detectAndDecodeCode(token: string): { code: string; entry: CodeEntry } | null {
  for (const { regex, prefix, lookup } of CODE_PATTERNS) {
    regex.lastIndex = 0;
    const match = regex.exec(token);
    if (match) {
      const codeKey = `${prefix}${match[1].toUpperCase()}`;
      const normalized = prefix === "E" ? codeKey : codeKey;
      if (lookup[normalized]) {
        return { code: normalized, entry: lookup[normalized] };
      }
      // Try without spaces for CI codes
      if (prefix === "CI ") {
        const noSpace = `CI ${match[1]}`;
        if (lookup[noSpace]) {
          return { code: noSpace, entry: lookup[noSpace] };
        }
      }
    }
  }
  return null;
}
