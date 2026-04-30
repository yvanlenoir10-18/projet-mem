/**
 * LightRAG Service
 *
 * Intègre LightRAG pour la recherche intelligente dans les entrées memoir.
 * LightRAG construit un graphe de connaissance et permet des requêtes
 * en langage naturel sur le contenu des entrées.
 *
 * Doc: https://github.com/HKUDS/LightRAG
 */

const LIGHTRAG_URL = process.env.LIGHTRAG_URL ?? "http://localhost:9621";
const LIGHTRAG_API_KEY = process.env.LIGHTRAG_API_KEY ?? "";

type SearchMode = "naive" | "local" | "global" | "hybrid";

interface SearchResult {
  response: string;
  mode: SearchMode;
}

interface IndexResult {
  status: string;
  document_id?: string;
}

/**
 * En-têtes communs pour toutes les requêtes LightRAG
 */
function headers(): HeadersInit {
  return {
    "Content-Type": "application/json",
    ...(LIGHTRAG_API_KEY ? { Authorization: `Bearer ${LIGHTRAG_API_KEY}` } : {}),
  };
}

/**
 * Indexe une entrée memoir dans LightRAG.
 * À appeler après chaque création ou mise à jour d'une entrée.
 *
 * @param entryId  - ID unique de l'entrée (utilisé comme document_id)
 * @param content  - Contenu textuel à indexer (titre + corps de l'entrée)
 */
export async function indexEntry(
  entryId: string,
  content: string
): Promise<IndexResult> {
  const response = await fetch(`${LIGHTRAG_URL}/documents/text`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      text: content,
      document_id: entryId,
      description: `Memoir entry ${entryId}`,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`LightRAG indexing failed: ${response.status} — ${error}`);
  }

  return response.json() as Promise<IndexResult>;
}

/**
 * Supprime une entrée de l'index LightRAG.
 * À appeler lors de la suppression d'une entrée.
 *
 * @param entryId - ID de l'entrée à supprimer de l'index
 */
export async function deleteEntryIndex(entryId: string): Promise<void> {
  const response = await fetch(`${LIGHTRAG_URL}/documents/${entryId}`, {
    method: "DELETE",
    headers: headers(),
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`LightRAG delete failed: ${response.status}`);
  }
}

/**
 * Recherche en langage naturel dans les entrées memoir.
 *
 * Modes disponibles :
 * - "hybrid"  → Combinaison locale + globale (recommandé)
 * - "local"   → Cherche dans le contexte proche des entités
 * - "global"  → Vue d'ensemble thématique
 * - "naive"   → Recherche vectorielle simple (la plus rapide)
 *
 * @param query  - Question en langage naturel
 * @param mode   - Mode de recherche (défaut: hybrid)
 */
export async function searchEntries(
  query: string,
  mode: SearchMode = "hybrid"
): Promise<SearchResult> {
  const response = await fetch(`${LIGHTRAG_URL}/query`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ query, mode }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`LightRAG search failed: ${response.status} — ${error}`);
  }

  const data = (await response.json()) as { response: string };
  return { response: data.response, mode };
}

/**
 * Vérifie si LightRAG est disponible et opérationnel.
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${LIGHTRAG_URL}/health`, {
      headers: headers(),
      signal: AbortSignal.timeout(3000),
    });
    return response.ok;
  } catch {
    return false;
  }
}
