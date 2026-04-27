/**
 * Route de recherche intelligente
 * Utilise LightRAG pour des requêtes en langage naturel sur les entrées memoir
 *
 * GET  /api/search?q=...&mode=hybrid
 * POST /api/search
 */

import { Router, Request, Response, NextFunction } from "express";
import {
  searchEntries,
  healthCheck,
} from "../../services/lightrag.service.js";

const router = Router();

/**
 * POST /api/search
 * Body: { query: string, mode?: "hybrid" | "local" | "global" | "naive" }
 *
 * Recherche en langage naturel dans toutes les entrées memoir de l'utilisateur.
 * Exemples de requêtes :
 *   "Quand ai-je parlé de ma famille pour la dernière fois ?"
 *   "Quels souvenirs d'été est-ce que j'ai ?"
 *   "Résume mes entrées sur le travail"
 */
router.post("/", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { query, mode = "hybrid" } = req.body as {
      query?: string;
      mode?: string;
    };

    if (!query || typeof query !== "string" || query.trim().length === 0) {
      return res.status(400).json({
        error: "Le champ 'query' est requis et ne peut pas être vide.",
      });
    }

    const validModes = ["hybrid", "local", "global", "naive"];
    if (!validModes.includes(mode)) {
      return res.status(400).json({
        error: `Mode invalide. Valeurs acceptées : ${validModes.join(", ")}`,
      });
    }

    const result = await searchEntries(
      query.trim(),
      mode as "hybrid" | "local" | "global" | "naive"
    );

    return res.json({
      query: query.trim(),
      mode: result.mode,
      response: result.response,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/search?q=...&mode=hybrid
 * Alias GET pour faciliter les tests depuis un navigateur
 */
router.get("/", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const query = req.query.q as string;
    const mode = (req.query.mode as string) ?? "hybrid";

    if (!query || query.trim().length === 0) {
      return res.status(400).json({
        error: "Le paramètre 'q' est requis.",
        example: "/api/search?q=quand ai-je parlé de mes vacances",
      });
    }

    const validModes = ["hybrid", "local", "global", "naive"];
    if (!validModes.includes(mode)) {
      return res.status(400).json({
        error: `Mode invalide. Valeurs acceptées : ${validModes.join(", ")}`,
      });
    }

    const result = await searchEntries(
      query.trim(),
      mode as "hybrid" | "local" | "global" | "naive"
    );

    return res.json({
      query: query.trim(),
      mode: result.mode,
      response: result.response,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/search/health
 * Vérifie si LightRAG est disponible
 */
router.get(
  "/health",
  async (_req: Request, res: Response, next: NextFunction) => {
    try {
      const available = await healthCheck();
      if (available) {
        return res.json({ status: "ok", lightrag: "available" });
      } else {
        return res.status(503).json({
          status: "degraded",
          lightrag: "unavailable",
          message:
            "LightRAG n'est pas accessible. Lancez: docker compose up lightrag",
        });
      }
    } catch (error) {
      next(error);
    }
  }
);

export default router;
