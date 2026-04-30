/**
 * Service Claude AI
 *
 * Utilise l'API Anthropic pour enrichir les entrées memoir :
 * - Résumé automatique
 * - Analyse d'humeur
 * - Suggestion de tags
 * - Extraction de personnes/lieux mentionnés
 */

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY ?? "";
const MODEL = "claude-haiku-4-5-20251001"; // Haiku = rapide + économique pour ce use case

interface AnalysisResult {
  summary: string;
  mood: string;
  mood_score: number; // -1 (négatif) à 1 (positif)
  tags: string[];
  people: string[];
  places: string[];
}

async function callClaude(prompt: string, system: string): Promise<string> {
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 1024,
      system,
      messages: [{ role: "user", content: prompt }],
    }),
  });

  if (!response.ok) {
    throw new Error(`Anthropic API error: ${response.status}`);
  }

  const data = (await response.json()) as {
    content: Array<{ type: string; text: string }>;
  };
  return data.content[0]?.text ?? "";
}

/**
 * Analyse complète d'une entrée memoir.
 * Retourne résumé, humeur, tags, personnes et lieux.
 */
export async function analyzeEntry(content: string): Promise<AnalysisResult> {
  const system = `Tu es un assistant spécialisé dans l'analyse de journaux intimes et mémoires.
Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après.
Sois bienveillant, respectueux et non-jugeant envers le contenu personnel.`;

  const prompt = `Analyse cette entrée de journal intime et retourne un JSON avec ces champs :
- summary: résumé en 1-2 phrases (en français)
- mood: humeur principale en un mot (ex: heureux, nostalgique, anxieux, serein...)
- mood_score: score de -1 (très négatif) à 1 (très positif)
- tags: liste de 3-5 thèmes/tags pertinents
- people: liste des personnes mentionnées (prénom ou relation)
- places: liste des lieux mentionnés

Entrée :
"""
${content}
"""`;

  const raw = await callClaude(prompt, system);

  try {
    const cleaned = raw.replace(/```json\n?|\n?```/g, "").trim();
    return JSON.parse(cleaned) as AnalysisResult;
  } catch {
    // Fallback si le JSON est mal formé
    return {
      summary: raw.slice(0, 200),
      mood: "inconnu",
      mood_score: 0,
      tags: [],
      people: [],
      places: [],
    };
  }
}

/**
 * Génère un résumé court d'une entrée memoir.
 */
export async function summarizeEntry(content: string): Promise<string> {
  const system = `Tu résumes des entrées de journal intime en 1-2 phrases courtes,
en préservant l'émotion principale. Tu écris en français.`;

  return callClaude(`Résume cette entrée :\n\n${content}`, system);
}

/**
 * Suggère des questions de réflexion basées sur une entrée.
 * Utile pour encourager l'écriture approfondie.
 */
export async function suggestReflections(content: string): Promise<string[]> {
  const system = `Tu es un coach de journal intime bienveillant.
Tu proposes des questions ouvertes pour approfondir la réflexion.
Tu réponds avec une liste JSON de 3 questions en français.`;

  const raw = await callClaude(
    `Propose 3 questions de réflexion basées sur cette entrée :\n\n${content}`,
    system
  );

  try {
    const cleaned = raw.replace(/```json\n?|\n?```/g, "").trim();
    return JSON.parse(cleaned) as string[];
  } catch {
    return [raw];
  }
}

/**
 * Vérifie si le service Claude est configuré.
 */
export function isConfigured(): boolean {
  return ANTHROPIC_API_KEY.length > 0;
}
