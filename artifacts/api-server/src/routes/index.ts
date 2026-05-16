import { Router, type IRouter } from "express";
import healthRouter from "./health";
import ingredientsRouter from "./ingredients";
import scanRouter from "./scan";
import historyRouter from "./history";
import statsRouter from "./stats";

const router: IRouter = Router();

router.use(healthRouter);
router.use(ingredientsRouter);
router.use(scanRouter);
router.use(historyRouter);
router.use(statsRouter);

export default router;
