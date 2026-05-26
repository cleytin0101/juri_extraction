-- Migration: Histórico de uploads manuais de PDFs
-- Rodar no SQL Editor do Supabase

CREATE TABLE IF NOT EXISTS upload_batches (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at      TIMESTAMPTZ DEFAULT now(),
  total_arquivos  INT DEFAULT 0,
  criados         INT DEFAULT 0,
  ja_existentes   INT DEFAULT 0,
  com_advogado    INT DEFAULT 0,
  erros           INT DEFAULT 0,
  arquivos        JSONB DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_upload_batches_created_at ON upload_batches(created_at DESC);

-- Índice para filtro por vara/órgão julgador (melhora performance do filtro)
CREATE INDEX IF NOT EXISTS idx_processos_orgao_julgador ON processos(orgao_julgador);
