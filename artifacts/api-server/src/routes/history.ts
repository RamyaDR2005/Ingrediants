import { Router } from "express";
import { db } from "@workspace/db";
import { scanHistoryTable } from "@workspace/db";
import {
  ListHistoryQueryParams,
  GetHistoryParams,
  DeleteHistoryParams,
  SaveHistoryBody,
} from "@workspace/api-zod";
import { eq, desc } from "drizzle-orm";

const router = Router();

router.get("/history", async (req, res) => {
  const parsed = ListHistoryQueryParams.safeParse(req.query);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid query params" });
  }
  const { limit = 20, offset = 0 } = parsed.data;
  const rows = await db
    .select()
    .from(scanHistoryTable)
    .orderBy(desc(scanHistoryTable.id))
    .limit(limit)
    .offset(offset);
  return res.json(rows);
});

router.post("/history", async (req, res) => {
  const parsed = SaveHistoryBody.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid body", details: parsed.error.issues });
  }
  const [row] = await db
    .insert(scanHistoryTable)
    .values({
      ...parsed.data,
      createdAt: new Date().toISOString(),
    })
    .returning();
  return res.status(201).json(row);
});

router.get("/history/:id", async (req, res) => {
  const parsed = GetHistoryParams.safeParse(req.params);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid params" });
  }
  const [row] = await db
    .select()
    .from(scanHistoryTable)
    .where(eq(scanHistoryTable.id, parsed.data.id));
  if (!row) {
    return res.status(404).json({ error: "Not found" });
  }
  return res.json(row);
});

router.delete("/history/:id", async (req, res) => {
  const parsed = DeleteHistoryParams.safeParse(req.params);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid params" });
  }
  await db.delete(scanHistoryTable).where(eq(scanHistoryTable.id, parsed.data.id));
  return res.status(204).send();
});

export default router;
