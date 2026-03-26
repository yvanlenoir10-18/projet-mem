-- Initialisation PostgreSQL pour projet-mem
-- Ce script s'exécute automatiquement au premier démarrage du container

-- Extension pgvector (requise par LightRAG pour le stockage vectoriel)
CREATE EXTENSION IF NOT EXISTS vector;

-- Extension pour la recherche full-text (requise pour la recherche d'entrées)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Extension UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
