import { pgTable, text, serial, integer, real } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod/v4";

export const ingredientsTable = pgTable("ingredients", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  code: text("code"),
  category: text("category"),
  riskLevel: text("risk_level").notNull().default("low"), // low, medium, high
  description: text("description"),
  safetyNotes: text("safety_notes"),
  profileFlags: text("profile_flags"), // comma-separated: children,pregnant,elderly,allergen
  source: text("source"),
});

export const scanHistoryTable = pgTable("scan_history", {
  id: serial("id").primaryKey(),
  productName: text("product_name").notNull(),
  rawText: text("raw_text").notNull(),
  grade: text("grade").notNull(),
  riskScore: real("risk_score").notNull(),
  profile: text("profile"),
  resultJson: text("result_json"),
  createdAt: text("created_at").notNull().default(new Date().toISOString()),
});

export const ingredientMatchStatsTable = pgTable("ingredient_match_stats", {
  id: serial("id").primaryKey(),
  ingredientId: integer("ingredient_id").notNull().references(() => ingredientsTable.id),
  matchCount: integer("match_count").notNull().default(0),
});

export const insertIngredientSchema = createInsertSchema(ingredientsTable).omit({ id: true });
export const insertScanHistorySchema = createInsertSchema(scanHistoryTable).omit({ id: true });
export const insertIngredientMatchStatSchema = createInsertSchema(ingredientMatchStatsTable).omit({ id: true });

export type Ingredient = typeof ingredientsTable.$inferSelect;
export type InsertIngredient = z.infer<typeof insertIngredientSchema>;
export type ScanHistory = typeof scanHistoryTable.$inferSelect;
export type InsertScanHistory = z.infer<typeof insertScanHistorySchema>;
