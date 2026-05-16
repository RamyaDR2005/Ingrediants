import { Router } from "express";
import { db } from "@workspace/db";
import { ingredientsTable } from "@workspace/db";
import {
  ListIngredientsQueryParams,
  GetIngredientParams,
} from "@workspace/api-zod";
import { eq, ilike, or, and, sql } from "drizzle-orm";

const router = Router();

router.get("/ingredients", async (req, res) => {
  const parsed = ListIngredientsQueryParams.safeParse(req.query);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid query params" });
  }
  const { search, riskLevel, category, limit = 50, offset = 0 } = parsed.data;

  const conditions = [];
  if (search) {
    conditions.push(
      or(
        ilike(ingredientsTable.name, `%${search}%`),
        ilike(ingredientsTable.code, `%${search}%`)
      )
    );
  }
  if (riskLevel) {
    conditions.push(eq(ingredientsTable.riskLevel, riskLevel));
  }
  if (category) {
    conditions.push(ilike(ingredientsTable.category, `%${category}%`));
  }

  const rows = await db
    .select()
    .from(ingredientsTable)
    .where(conditions.length > 0 ? and(...conditions) : undefined)
    .limit(limit)
    .offset(offset);

  return res.json(rows);
});

router.get("/ingredients/:id", async (req, res) => {
  const parsed = GetIngredientParams.safeParse(req.params);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid params" });
  }
  const [row] = await db
    .select()
    .from(ingredientsTable)
    .where(eq(ingredientsTable.id, parsed.data.id));
  if (!row) {
    return res.status(404).json({ error: "Not found" });
  }
  return res.json(row);
});

export default router;
