"""
Test LightRAG — Memoir App
Contourne tiktoken (bloqué par proxy) avec un tokenizer minimal.
"""
import asyncio
import os
import sys
import numpy as np

# ── Tokenizer minimal (remplace tiktoken) ───────────────────────────────────
class SimpleTokenizer:
    def encode(self, text):
        return list(text.encode("utf-8"))
    def decode(self, tokens):
        return bytes(tokens).decode("utf-8", errors="replace")

# Patch avant import lightrag
import tiktoken
from tiktoken import registry as _reg
_orig = _reg.get_encoding
def _patched_get_encoding(name):
    class FakeEncoding:
        name = "cl100k_base"
        def encode(self, text, *args, **kwargs):
            return list(text.encode("utf-8"))
        def decode(self, tokens):
            return bytes(t % 256 for t in tokens).decode("utf-8", errors="replace")
        def encode_ordinary(self, text):
            return self.encode(text)
    return FakeEncoding()
_reg.get_encoding = _patched_get_encoding
tiktoken.encoding_for_model = lambda m: _patched_get_encoding("cl100k_base")
tiktoken.get_encoding = _patched_get_encoding

from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc

WORKING_DIR = "/tmp/lightrag_memoir_test"
os.makedirs(WORKING_DIR, exist_ok=True)

# ── Mock LLM (Ollama/llama3.2 en production) ────────────────────────────────
async def mock_llm(prompt, system_prompt=None, history_messages=[], **kwargs):
    text = (system_prompt or "") + prompt
    if "entit" in text.lower() or "extract" in text.lower() or "tuple" in text.lower():
        return (
            '("entity"<|>FAMILLE<|>PERSONNE<|>Membres de la famille)<|>'
            '("entity"<|>MÈRE<|>PERSONNE<|>La mère du narrateur)<|>'
            '("entity"<|>ENFANCE<|>PÉRIODE<|>Période enfance)<|>'
            '("entity"<|>MER<|>LIEU<|>La mer vacances)<|>'
            '("entity"<|>VACANCES<|>ÉVÉNEMENT<|>Voyages estivaux)<|>'
            '("relationship"<|>MÈRE<|>FAMILLE<|>La mère fait partie de la famille<|>9)<|>'
            '("relationship"<|>ENFANCE<|>MER<|>Souvenirs enfance à la mer<|>8)<|>'
            '("relationship"<|>FAMILLE<|>VACANCES<|>Vacances en famille<|>9)'
        )
    if "summar" in text.lower() or "résum" in text.lower():
        return "Ce document parle de souvenirs de famille, de l'enfance et de vacances à la mer."
    return "Les souvenirs mentionnent la famille, la mère, l'enfance et des vacances à la mer."

async def mock_embedding(texts):
    result = []
    for t in texts:
        np.random.seed(hash(t[:30]) % (2**31))
        result.append(np.random.rand(384))
    return np.array(result)

# ── Init LightRAG ────────────────────────────────────────────────────────────
print("Initialisation de LightRAG...")
rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=mock_llm,
    embedding_func=EmbeddingFunc(
        embedding_dim=384,
        max_token_size=512,
        func=mock_embedding,
    ),
)
print("✅ LightRAG initialisé\n")

ENTRIES = [
    "Entrée du 15 juillet 2023 — Vacances en famille à la mer. Maman avait préparé des sandwichs pour la route. J'adore ce moment où on aperçoit l'océan depuis l'autoroute. Comme chaque été depuis mon enfance.",
    "Entrée du 3 décembre 2023 — Je repense à mon enfance dans la maison de campagne. Le jardin était immense. Ma mère nous appelait pour le dîner, l'odeur de sa cuisine traversait tout le jardin.",
    "Entrée du 20 janvier 2024 — Réunion de famille pour l'anniversaire de grand-mère. On a regardé de vieilles photos. Maman pleurait un peu en voyant les photos de grand-père.",
    "Entrée du 8 mars 2024 — Journée difficile. Je pense à ma mère qui vieillit. J'essaie de lui rendre visite plus souvent. Ces moments passés ensemble sont précieux.",
]

async def main():
    await rag.initialize_storages()

    print("=" * 55)
    print("  TEST LIGHTRAG — Memoir App")
    print("=" * 55)

    print("\n📝 Indexation de 4 entrées memoir...")
    await rag.ainsert(ENTRIES)
    print("✅ Entrées indexées avec succès !\n")

    queries = [
        ("Quand ai-je parlé de ma mère ?", "hybrid"),
        ("Quels souvenirs d'enfance est-ce que j'ai ?", "local"),
        ("Résume mes souvenirs de vacances en famille", "global"),
    ]

    print("🔍 Recherches en langage naturel :\n")
    for query, mode in queries:
        print(f"❓ {query}")
        result = await rag.aquery(query, param=QueryParam(mode=mode))
        preview = str(result)[:200].strip().replace("\n", " ")
        print(f"   [{mode}] → {preview}\n")

    print("=" * 55)
    print("✅ LightRAG fonctionne !")
    print("   En production :")
    print("   - llama3.2 via Ollama remplace le mock LLM")
    print("   - nomic-embed-text remplace les embeddings mock")
    print("   - PostgreSQL remplace le stockage local")
    print("=" * 55)

asyncio.run(main())
