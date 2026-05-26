-- Migration: adicionar campo responsavel em leads e upload_batches
-- Rodar no SQL Editor do Supabase

-- 1. Adicionar responsavel em leads
ALTER TABLE leads ADD COLUMN IF NOT EXISTS responsavel TEXT;

-- 2. Adicionar responsavel em upload_batches
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS responsavel TEXT;

-- 3. Recriar a view leads_completo incluindo responsavel
CREATE OR REPLACE VIEW leads_completo AS
SELECT
  l.id                  AS lead_id,
  l.status,
  l.mensagem_texto,
  l.enviado_em,
  l.respondido_em,
  l.convertido_em,
  l.created_at          AS lead_criado_em,
  l.updated_at,
  l.notas,
  l.responsavel,
  p.id                  AS processo_id,
  p.numero_processo,
  p.orgao_julgador,
  p.valor_causa,
  p.data_audiencia,
  p.tipo_audiencia,
  p.resumo_caso,
  p.reclamante_nome,
  p.tem_advogado,
  p.pdf_url,
  p.pdf_expires_at,
  e.nome                AS empresa_nome,
  e.cnpj                AS empresa_cnpj,
  e.telefones           AS empresa_telefones,
  e.email               AS empresa_email,
  v.nome                AS vara_nome,
  v.codigo              AS vara_codigo
FROM leads l
JOIN processos p ON l.processo_id = p.id
JOIN empresas e ON l.empresa_id = e.id
LEFT JOIN pautas pa ON p.pauta_id = pa.id
LEFT JOIN varas v ON pa.vara_id = v.id;
