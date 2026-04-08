-- ============================================================
-- SCHEMA: Sistema de Leads Jurídicos — PJe TRT-7
-- Rodar no SQL Editor do Supabase
-- ============================================================

CREATE TYPE lead_status AS ENUM (
  'novo', 'enviado', 'respondido', 'convertido', 'descartado'
);

CREATE TYPE audiencia_tipo AS ENUM (
  'instrucao', 'una', 'conciliacao', 'outra'
);

-- Varas do tribunal
CREATE TABLE varas (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo     TEXT NOT NULL UNIQUE,
  nome       TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Sessões de pauta extraídas
CREATE TABLE pautas (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vara_id    UUID REFERENCES varas(id) ON DELETE SET NULL,
  data_pauta DATE NOT NULL,
  scraped_at TIMESTAMPTZ DEFAULT now(),
  raw_html   TEXT,
  UNIQUE(vara_id, data_pauta)
);

-- Processos individuais
CREATE TABLE processos (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pauta_id         UUID REFERENCES pautas(id) ON DELETE CASCADE,
  numero_processo  TEXT NOT NULL UNIQUE,
  orgao_julgador   TEXT,
  valor_causa      NUMERIC(15, 2),
  data_audiencia   TIMESTAMPTZ NOT NULL,
  tipo_audiencia   audiencia_tipo DEFAULT 'outra',
  resumo_caso      TEXT,
  reclamante_nome  TEXT,
  raw_data         JSONB,
  created_at       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_processos_data_audiencia ON processos(data_audiencia);
CREATE INDEX idx_processos_numero ON processos(numero_processo);

-- Empresas reclamadas
CREATE TABLE empresas (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  processo_id UUID REFERENCES processos(id) ON DELETE CASCADE,
  nome        TEXT NOT NULL,
  cnpj        TEXT,
  telefones   TEXT[],
  email       TEXT,
  endereco    TEXT,
  cnpj_data   JSONB,
  enriched_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_empresas_cnpj ON empresas(cnpj);

-- Leads de prospecção
CREATE TABLE leads (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  processo_id    UUID REFERENCES processos(id) ON DELETE CASCADE,
  empresa_id     UUID REFERENCES empresas(id) ON DELETE CASCADE,
  status         lead_status DEFAULT 'novo',
  mensagem_texto TEXT,
  enviado_em     TIMESTAMPTZ,
  respondido_em  TIMESTAMPTZ,
  convertido_em  TIMESTAMPTZ,
  notas          TEXT,
  created_at     TIMESTAMPTZ DEFAULT now(),
  updated_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);

-- Log de mensagens WhatsApp
CREATE TABLE mensagens_log (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id      UUID REFERENCES leads(id) ON DELETE CASCADE,
  telefone     TEXT NOT NULL,
  mensagem     TEXT NOT NULL,
  provider     TEXT NOT NULL DEFAULT 'mock',
  provider_ref TEXT,
  status       TEXT,
  erro         TEXT,
  created_at   TIMESTAMPTZ DEFAULT now()
);

-- Trigger: atualizar leads.updated_at automaticamente
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER leads_updated_at
  BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- View desnormalizada para o dashboard
CREATE VIEW leads_completo AS
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
  p.numero_processo,
  p.orgao_julgador,
  p.valor_causa,
  p.data_audiencia,
  p.tipo_audiencia,
  p.resumo_caso,
  p.reclamante_nome,
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

-- Seed: varas do TRT-7 — lista completa
INSERT INTO varas (codigo, nome) VALUES
  ('UVT-ARA',   'Única Vara do Trabalho de Aracati'),
  ('UVT-BAT',   'Única Vara do Trabalho de Baturité'),
  ('1VT-CAU',   '1ª Vara do Trabalho de Caucaia'),
  ('2VT-CAU',   '2ª Vara do Trabalho de Caucaia'),
  ('UVT-CRA',   'Única Vara do Trabalho de Crateús'),
  ('UVT-EUS',   'Única Vara do Trabalho de Eusébio'),
  ('1VT-FOR',   '1ª Vara do Trabalho de Fortaleza'),
  ('2VT-FOR',   '2ª Vara do Trabalho de Fortaleza'),
  ('3VT-FOR',   '3ª Vara do Trabalho de Fortaleza'),
  ('4VT-FOR',   '4ª Vara do Trabalho de Fortaleza'),
  ('5VT-FOR',   '5ª Vara do Trabalho de Fortaleza'),
  ('6VT-FOR',   '6ª Vara do Trabalho de Fortaleza'),
  ('7VT-FOR',   '7ª Vara do Trabalho de Fortaleza'),
  ('8VT-FOR',   '8ª Vara do Trabalho de Fortaleza'),
  ('9VT-FOR',   '9ª Vara do Trabalho de Fortaleza'),
  ('10VT-FOR',  '10ª Vara do Trabalho de Fortaleza'),
  ('11VT-FOR',  '11ª Vara do Trabalho de Fortaleza'),
  ('12VT-FOR',  '12ª Vara do Trabalho de Fortaleza'),
  ('13VT-FOR',  '13ª Vara do Trabalho de Fortaleza'),
  ('14VT-FOR',  '14ª Vara do Trabalho de Fortaleza'),
  ('15VT-FOR',  '15ª Vara do Trabalho de Fortaleza'),
  ('16VT-FOR',  '16ª Vara do Trabalho de Fortaleza'),
  ('17VT-FOR',  '17ª Vara do Trabalho de Fortaleza'),
  ('18VT-FOR',  '18ª Vara do Trabalho de Fortaleza'),
  ('VP-FOR',    'Vara Plantonista'),
  ('PA-CLE',    'Posto Avançado CLE - Secretaria Judiciária'),
  ('PA-PREC',   'Posto Avançado Divisão de Precatórios'),
  ('CEJUSC',    'CEJUSC-JT de 1º grau'),
  ('CA-FAN',    'Central de Atendimento Fórum Autran Nunes'),
  ('CORR',      'Corregedoria-Geral'),
  ('SEU',       'Secretaria de Execuções Unificadas, Pesquisas Patrimoniais e Expropriações'),
  ('GETEC',     'Posto Avançado de Execuções Coletivas - GETEC'),
  ('UVT-IGU',   'Única Vara do Trabalho de Iguatu'),
  ('1VT-CAR',   '1ª Vara do Trabalho da Região do Cariri'),
  ('2VT-CAR',   '2ª Vara do Trabalho da Região do Cariri'),
  ('3VT-CAR',   '3ª Vara do Trabalho da Região do Cariri'),
  ('CA-CAR',    'Central de Atendimento Cariri'),
  ('UVT-LIM',   'Única Vara do Trabalho de Limoeiro do Norte'),
  ('1VT-MAR',   '1ª Vara do Trabalho de Maracanaú'),
  ('2VT-MAR',   '2ª Vara do Trabalho de Maracanaú'),
  ('PA-MAG-1',  'Posto Avançado do Fórum Trabalhista de Maracanaú em Maranguape - 1ª VT'),
  ('PA-MAG-2',  'Posto Avançado do Fórum Trabalhista de Maracanaú em Maranguape - 2ª VT'),
  ('UVT-PAC',   'Única Vara do Trabalho de Pacajus'),
  ('UVT-QUI',   'Única Vara do Trabalho de Quixadá'),
  ('UVT-SGA',   'Única Vara do Trabalho de São Gonçalo do Amarante'),
  ('1VT-SOB',   '1ª Vara do Trabalho de Sobral'),
  ('2VT-SOB',   '2ª Vara do Trabalho de Sobral'),
  ('UVT-TIA',   'Única Vara do Trabalho de Tianguá')
ON CONFLICT (codigo) DO NOTHING;
