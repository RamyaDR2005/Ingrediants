import { Router } from "express";
import { db } from "@workspace/db";
import { ingredientsTable, scanHistoryTable, ingredientMatchStatsTable } from "@workspace/db";
import { eq, sql, desc, count, avg } from "drizzle-orm";

const router = Router();

router.get("/stats/summary", async (req, res) => {
  const [ingredientStats] = await db
    .select({
      total: count(),
      highRisk: sql<number>`count(*) filter (where ${ingredientsTable.riskLevel} = 'high')`,
      mediumRisk: sql<number>`count(*) filter (where ${ingredientsTable.riskLevel} = 'medium')`,
      lowRisk: sql<number>`count(*) filter (where ${ingredientsTable.riskLevel} = 'low')`,
    })
    .from(ingredientsTable);

  const [scanStats] = await db
    .select({
      totalScans: count(),
      avgRisk: avg(scanHistoryTable.riskScore),
    })
    .from(scanHistoryTable);

  return res.json({
    totalIngredients: Number(ingredientStats?.total ?? 0),
    totalScans: Number(scanStats?.totalScans ?? 0),
    avgRiskScore: Math.round(Number(scanStats?.avgRisk ?? 0) * 10) / 10,
    highRiskCount: Number(ingredientStats?.highRisk ?? 0),
    mediumRiskCount: Number(ingredientStats?.mediumRisk ?? 0),
    lowRiskCount: Number(ingredientStats?.lowRisk ?? 0),
  });
});

router.get("/stats/risk-distribution", async (req, res) => {
  const [stats] = await db
    .select({
      low: sql<number>`count(*) filter (where ${ingredientsTable.riskLevel} = 'low')`,
      medium: sql<number>`count(*) filter (where ${ingredientsTable.riskLevel} = 'medium')`,
      high: sql<number>`count(*) filter (where ${ingredientsTable.riskLevel} = 'high')`,
    })
    .from(ingredientsTable);

  return res.json({
    low: Number(stats?.low ?? 0),
    medium: Number(stats?.medium ?? 0),
    high: Number(stats?.high ?? 0),
    unknown: 0,
  });
});

router.get("/stats/top-risky", async (req, res) => {
  const limit = Number(req.query.limit ?? 10);

  const rows = await db
    .select({
      name: ingredientsTable.name,
      code: ingredientsTable.code,
      riskLevel: ingredientsTable.riskLevel,
      count: ingredientMatchStatsTable.matchCount,
    })
    .from(ingredientMatchStatsTable)
    .innerJoin(ingredientsTable, eq(ingredientMatchStatsTable.ingredientId, ingredientsTable.id))
    .where(eq(ingredientsTable.riskLevel, "high"))
    .orderBy(desc(ingredientMatchStatsTable.matchCount))
    .limit(limit);

  return res.json(rows.map((r) => ({ name: r.name, code: r.code, count: r.count, riskLevel: r.riskLevel })));
});

router.get("/stats/categories", async (req, res) => {
  const rows = await db
    .select({
      category: ingredientsTable.category,
      count: count(),
    })
    .from(ingredientsTable)
    .groupBy(ingredientsTable.category)
    .orderBy(desc(count()));

  return res.json(
    rows
      .filter((r) => r.category)
      .map((r) => ({ category: r.category as string, count: Number(r.count) }))
  );
});

export default router;
