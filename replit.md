# SafeScan — AI-Powered Ingredient Scanner & Risk Analyzer

A web app that lets users paste ingredient lists from food or personal care products and instantly get a safety analysis — risk scores, traffic light indicators, and profile-specific warnings.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 8080)
- `pnpm --filter @workspace/ingredient-scanner run dev` — run the frontend
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Frontend: React + Vite + Tailwind + shadcn/ui + Recharts
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `lib/api-spec/openapi.yaml` — source of truth for all API contracts
- `lib/db/src/schema/ingredients.ts` — DB schema (ingredients, scan_history, ingredient_match_stats)
- `artifacts/api-server/src/routes/` — backend route handlers (ingredients, scan, history, stats)
- `artifacts/ingredient-scanner/src/` — React frontend (pages, components)

## Architecture decisions

- Dataset of 1,273 ingredients from the uploaded Excel is loaded into PostgreSQL at first seed
- Risk levels are mapped: moderate → medium; worst of child/pregnancy/elderly risks = overall risk
- Ingredient matching uses fuzzy ILIKE search on the first 3 words of each token
- Scan scoring: high=10pts, medium=4pts, low=1pt, unknown=2pt; normalized to 0-100 then graded A-F
- Profile flags (children, pregnant, elderly) drive profile-specific warnings on scan results

## Product

- Scanner: paste any ingredient list → get a product grade (A-F), risk score, and per-ingredient traffic lights
- Database: browse and search 1,273+ ingredients with risk levels and safety notes
- History: save and revisit past scans
- Dashboard: charts showing risk distribution, top risky ingredients, category breakdowns

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Always run `pnpm --filter @workspace/db run push` after schema changes before restarting the API
- Always run codegen after editing `lib/api-spec/openapi.yaml`
- The scan endpoint uses ILIKE fuzzy matching — very short ingredient names (< 3 chars) may not match

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
