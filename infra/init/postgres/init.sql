CREATE EXTENSION IF NOT EXISTS vector;

-- Separate database for the LiteLLM proxy's own Prisma-managed tables
-- (virtual keys, users, spend tracking) so it doesn't collide with app schema.
SELECT 'CREATE DATABASE litellm OWNER sdlc'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'litellm')\gexec

CREATE TABLE IF NOT EXISTS code_chunks (
  id UUID PRIMARY KEY,
  collection TEXT NOT NULL,
  path TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS code_chunks_collection_idx ON code_chunks (collection);
