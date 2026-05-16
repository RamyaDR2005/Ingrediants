import { Router } from "express";
import { db } from "@workspace/db";
import { ingredientsTable, ingredientMatchStatsTable } from "@workspace/db";
import { ScanIngredientsBody } from "@workspace/api-zod";
import { ilike, sql } from "drizzle-orm";
import { detectAndDecodeCode } from "../lib/codes";

const router = Router();

function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .replace(/\(.*?\)/g, " ")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenizeIngredients(rawText: string): string[] {
  return rawText
    .split(/[,;\n•|]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 2);
}

function computeGrade(riskScore: number): "A" | "B" | "C" | "D" | "F" {
  if (riskScore <= 10) return "A";
  if (riskScore <= 25) return "B";
  if (riskScore <= 45) return "C";
  if (riskScore <= 65) return "D";
  return "F";
}

function getProfileWarning(
  ingredient: { profileFlags: string | null; name: string },
  profile: string
): string | null {
  if (!ingredient.profileFlags) return null;
  const flags = ingredient.profileFlags.split(",").map((f) => f.trim());
  const warnings: string[] = [];
  if (profile === "children" && flags.includes("children")) warnings.push("Not recommended for children");
  if (profile === "pregnant" && flags.includes("pregnant")) warnings.push("Caution during pregnancy");
  if (profile === "elderly" && flags.includes("elderly")) warnings.push("Use caution for elderly individuals");
  if (profile === "allergen" && flags.includes("allergen")) warnings.push("Potential allergen");
  return warnings.length > 0 ? warnings.join(". ") : null;
}

router.post("/scan", async (req, res) => {
  const parsed = ScanIngredientsBody.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid body", details: parsed.error.issues });
  }
  const { text, profile = "general" } = parsed.data;

  const tokens = tokenizeIngredients(text);
  const matchedIngredients: Array<{
    raw: string;
    matched: typeof ingredientsTable.$inferSelect | null;
    riskLevel: "low" | "medium" | "high" | "unknown";
    warning: string | null;
    decodedCode?: string;
    codeDescription?: string;
  }> = [];

  for (const token of tokens) {
    // 1. Try chemical code detection first (E-numbers, INS, CI codes)
    const codeMatch = detectAndDecodeCode(token);
    if (codeMatch) {
      const { code, entry } = codeMatch;
      let warning = entry.description;
      if (profile === "children" && entry.riskLevel === "high") {
        warning += ". Not recommended for children.";
      }
      if (profile === "pregnant" && entry.riskLevel !== "low") {
        warning += ". Use caution during pregnancy.";
      }
      matchedIngredients.push({
        raw: token,
        matched: {
          id: -1,
          name: entry.name,
          code,
          category: entry.category,
          riskLevel: entry.riskLevel,
          description: entry.description,
          safetyNotes: entry.description,
          profileFlags: null,
          source: code,
        },
        riskLevel: entry.riskLevel,
        warning,
        decodedCode: code,
        codeDescription: entry.description,
      });
      continue;
    }

    // 2. Fuzzy DB lookup
    const normalized = normalizeText(token);
    if (!normalized) continue;

    const words = normalized.split(" ").filter((w) => w.length > 2);
    const primaryTerm = words.slice(0, 3).join(" ");

    let matched = null;
    if (primaryTerm) {
      const rows = await db
        .select()
        .from(ingredientsTable)
        .where(ilike(ingredientsTable.name, `%${primaryTerm}%`))
        .limit(1);
      if (rows.length > 0) {
        matched = rows[0];
        await db
          .insert(ingredientMatchStatsTable)
          .values({ ingredientId: matched.id, matchCount: 1 })
          .onConflictDoUpdate({
            target: ingredientMatchStatsTable.ingredientId,
            set: { matchCount: sql`${ingredientMatchStatsTable.matchCount} + 1` },
          });
      }
    }

    let riskLevel: "low" | "medium" | "high" | "unknown" = "unknown";
    let warning: string | null = null;

    if (matched) {
      riskLevel = matched.riskLevel as "low" | "medium" | "high";
      warning = matched.safetyNotes ?? null;
      const profileWarning = getProfileWarning(matched, profile);
      if (profileWarning) {
        warning = warning ? `${warning}. ${profileWarning}` : profileWarning;
      }
    }

    matchedIngredients.push({ raw: token, matched, riskLevel, warning });
  }

  // Compute risk score
  let totalScore = 0;
  let lowCount = 0, mediumCount = 0, highCount = 0, unknownCount = 0;

  for (const item of matchedIngredients) {
    if (item.riskLevel === "high") { totalScore += 10; highCount++; }
    else if (item.riskLevel === "medium") { totalScore += 4; mediumCount++; }
    else if (item.riskLevel === "low") { totalScore += 1; lowCount++; }
    else { totalScore += 2; unknownCount++; }
  }

  const total = matchedIngredients.length || 1;
  const normalizedScore = Math.min(100, (totalScore / total) * 10);
  const grade = computeGrade(normalizedScore);

  let summary = `Analyzed ${total} ingredient${total !== 1 ? "s" : ""}.`;
  if (highCount > 0) summary += ` Found ${highCount} high-risk ingredient${highCount !== 1 ? "s" : ""}.`;
  if (mediumCount > 0) summary += ` ${mediumCount} medium-risk.`;
  if (lowCount > 0) summary += ` ${lowCount} low-risk.`;
  if (unknownCount > 0) summary += ` ${unknownCount} unknown/unmatched.`;

  return res.json({
    ingredients: matchedIngredients,
    grade,
    riskScore: Math.round(normalizedScore * 10) / 10,
    summary,
    profile,
    lowCount,
    mediumCount,
    highCount,
    unknownCount,
  });
});

export default router;
