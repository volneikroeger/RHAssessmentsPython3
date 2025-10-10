/*
  # Create DISC Assessment Bank System

  ## Overview
  Complete multilingual DISC assessment database supporting normative items, ipsative blocks,
  scenarios, scoring rules, report templates, and all supporting data for professional
  DISC personality assessments.

  ## 1. New Tables

  ### disc_versions
  - Tracks assessment bank versions with metadata
  - Fields: id, version, created_at, notes

  ### disc_items_norm
  - 120 normative assessment items with bilingual text
  - Fields: item_id (natural key), texto_pt, texto_simples_pt, texto_en, texto_simples_en
  - Factor weights: peso_d, peso_i, peso_s, peso_c
  - Metadata: fator_primario, fatores_sec, invertido, sutil, contexto, leitura_nivel

  ### disc_blocks_ipsa
  - 24 ipsative (forced-choice) blocks with 4 phrases each
  - Each phrase in PT/EN with factor mapping
  - Fields: bloco_id, frase_a_pt/en, fator_a, frase_b_pt/en, fator_b, etc.

  ### disc_scenarios
  - 12 situational judgment scenarios
  - Four response options per scenario in PT/EN
  - Fields: cenario_id, prompt_pt/en, opc_a_pt/en, fator_a, etc.

  ### disc_likert_map
  - 5-point Likert scale to DISC score mapping
  - Fields: resposta (1-5), ancora_pt/en, escore_d/i/s/c, escore_im

  ### disc_rules
  - Scoring calculation rules and formulas
  - Fields: regra_id, descricao_pt/en, formula_pt/en, aplicacao

  ### disc_thresholds
  - Interpretation thresholds by factor
  - Fields: fator (D/I/S/C), baixo, medio, alto, nota_pt/en

  ### disc_report_templates
  - Report section templates with conditional logic
  - Fields: secao_key, secao_pt/en, condicao, texto_pt/en, bullets_pt/en, metricas, placeholders

  ### disc_words
  - Descriptive words by factor and intensity
  - Fields: fator, intensidade (baixa/média/alta), lista_pt/en (CSV string)

  ### disc_interview
  - Interview guide questions by DISC axis
  - Fields: eixo (D/I/S/C), pergunta_pt/en, observar_pt/en, follow_pt/en

  ### disc_quality_checks
  - Data quality validation criteria
  - Fields: checagem_pt/en, criterio_pt/en, acao_pt/en

  ### disc_ethics
  - Ethical principles for assessment use
  - Fields: principio_pt/en, como_aplicamos_pt/en

  ## 2. Indexes
  - Natural keys (item_id, bloco_id, cenario_id)
  - Factor fields for filtering
  - Version references for multi-version support

  ## 3. Security
  - Enable RLS on all tables
  - Organization-scoped read access for authenticated members
  - HR/Admin role required for data import/management
*/

-- ============================================================================
-- DISC VERSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version text UNIQUE NOT NULL,
  created_at timestamptz DEFAULT now(),
  notes text,
  data_criacao date
);

-- ============================================================================
-- DISC NORMATIVE ITEMS (120 items)
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_items_norm (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  item_id text NOT NULL,
  texto_pt text NOT NULL,
  texto_simples_pt text,
  texto_en text,
  texto_simples_en text,
  fator_primario text CHECK (fator_primario IN ('D', 'I', 'S', 'C')),
  fatores_sec text,
  invertido boolean DEFAULT false,
  peso_d numeric(5,2) DEFAULT 0,
  peso_i numeric(5,2) DEFAULT 0,
  peso_s numeric(5,2) DEFAULT 0,
  peso_c numeric(5,2) DEFAULT 0,
  sutil boolean DEFAULT false,
  contexto text,
  leitura_nivel text,
  versao_str text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(version_ref, item_id)
);

CREATE INDEX IF NOT EXISTS idx_disc_items_norm_version ON disc_items_norm(version_ref);
CREATE INDEX IF NOT EXISTS idx_disc_items_norm_fator ON disc_items_norm(fator_primario);
CREATE INDEX IF NOT EXISTS idx_disc_items_norm_item_id ON disc_items_norm(item_id);

-- ============================================================================
-- DISC IPSATIVE BLOCKS (24 blocks, 4 phrases each)
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_blocks_ipsa (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  bloco_id text NOT NULL,
  frase_a_pt text NOT NULL,
  frase_a_en text,
  fator_a text CHECK (fator_a IN ('D', 'I', 'S', 'C')),
  frase_b_pt text NOT NULL,
  frase_b_en text,
  fator_b text CHECK (fator_b IN ('D', 'I', 'S', 'C')),
  frase_c_pt text NOT NULL,
  frase_c_en text,
  fator_c text CHECK (fator_c IN ('D', 'I', 'S', 'C')),
  frase_d_pt text NOT NULL,
  frase_d_en text,
  fator_d text CHECK (fator_d IN ('D', 'I', 'S', 'C')),
  regra_pt text,
  regra_en text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(version_ref, bloco_id)
);

CREATE INDEX IF NOT EXISTS idx_disc_blocks_ipsa_version ON disc_blocks_ipsa(version_ref);
CREATE INDEX IF NOT EXISTS idx_disc_blocks_ipsa_bloco_id ON disc_blocks_ipsa(bloco_id);

-- ============================================================================
-- DISC SCENARIOS (12 scenarios, 4 options each)
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_scenarios (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  cenario_id text NOT NULL,
  prompt_pt text NOT NULL,
  prompt_en text,
  opc_a_pt text NOT NULL,
  opc_a_en text,
  fator_a text CHECK (fator_a IN ('D', 'I', 'S', 'C')),
  opc_b_pt text NOT NULL,
  opc_b_en text,
  fator_b text CHECK (fator_b IN ('D', 'I', 'S', 'C')),
  opc_c_pt text NOT NULL,
  opc_c_en text,
  fator_c text CHECK (fator_c IN ('D', 'I', 'S', 'C')),
  opc_d_pt text NOT NULL,
  opc_d_en text,
  fator_d text CHECK (fator_d IN ('D', 'I', 'S', 'C')),
  regra_pt text,
  regra_en text,
  contexto text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(version_ref, cenario_id)
);

CREATE INDEX IF NOT EXISTS idx_disc_scenarios_version ON disc_scenarios(version_ref);
CREATE INDEX IF NOT EXISTS idx_disc_scenarios_cenario_id ON disc_scenarios(cenario_id);

-- ============================================================================
-- DISC LIKERT MAPPING (5 response levels)
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_likert_map (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  resposta integer NOT NULL CHECK (resposta BETWEEN 1 AND 5),
  ancora_pt text NOT NULL,
  ancora_en text,
  escore_d numeric(5,2) DEFAULT 0,
  escore_i numeric(5,2) DEFAULT 0,
  escore_s numeric(5,2) DEFAULT 0,
  escore_c numeric(5,2) DEFAULT 0,
  escore_im numeric(5,2) DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  UNIQUE(version_ref, resposta)
);

CREATE INDEX IF NOT EXISTS idx_disc_likert_map_version ON disc_likert_map(version_ref);

-- ============================================================================
-- DISC SCORING RULES
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  regra_id text NOT NULL,
  descricao_pt text NOT NULL,
  descricao_en text,
  formula_pt text,
  formula_en text,
  aplicacao text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(version_ref, regra_id)
);

CREATE INDEX IF NOT EXISTS idx_disc_rules_version ON disc_rules(version_ref);

-- ============================================================================
-- DISC INTERPRETATION THRESHOLDS
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_thresholds (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  fator text NOT NULL CHECK (fator IN ('D', 'I', 'S', 'C')),
  baixo numeric(5,2),
  medio numeric(5,2),
  alto numeric(5,2),
  nota_pt text,
  nota_en text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(version_ref, fator)
);

CREATE INDEX IF NOT EXISTS idx_disc_thresholds_version ON disc_thresholds(version_ref);
CREATE INDEX IF NOT EXISTS idx_disc_thresholds_fator ON disc_thresholds(fator);

-- ============================================================================
-- DISC REPORT TEMPLATES
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_report_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  secao_key text NOT NULL,
  secao_pt text NOT NULL,
  secao_en text,
  condicao text,
  texto_pt text,
  texto_en text,
  bullets_pt text,
  bullets_en text,
  metricas text,
  placeholders text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(version_ref, secao_key)
);

CREATE INDEX IF NOT EXISTS idx_disc_report_templates_version ON disc_report_templates(version_ref);
CREATE INDEX IF NOT EXISTS idx_disc_report_templates_secao ON disc_report_templates(secao_key);

-- ============================================================================
-- DISC DESCRIPTIVE WORDS
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_words (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  fator text NOT NULL CHECK (fator IN ('D', 'I', 'S', 'C')),
  intensidade text NOT NULL CHECK (intensidade IN ('baixa', 'média', 'alta')),
  lista_pt text,
  lista_en text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(version_ref, fator, intensidade)
);

CREATE INDEX IF NOT EXISTS idx_disc_words_version ON disc_words(version_ref);
CREATE INDEX IF NOT EXISTS idx_disc_words_fator ON disc_words(fator);

-- ============================================================================
-- DISC INTERVIEW GUIDE
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_interview (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  eixo text NOT NULL CHECK (eixo IN ('D', 'I', 'S', 'C')),
  pergunta_pt text NOT NULL,
  pergunta_en text,
  observar_pt text,
  observar_en text,
  follow_pt text,
  follow_en text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_disc_interview_version ON disc_interview(version_ref);
CREATE INDEX IF NOT EXISTS idx_disc_interview_eixo ON disc_interview(eixo);

-- ============================================================================
-- DISC QUALITY CHECKS
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_quality_checks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  checagem_pt text NOT NULL,
  checagem_en text,
  criterio_pt text,
  criterio_en text,
  acao_pt text,
  acao_en text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_disc_quality_checks_version ON disc_quality_checks(version_ref);

-- ============================================================================
-- DISC ETHICS PRINCIPLES
-- ============================================================================
CREATE TABLE IF NOT EXISTS disc_ethics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_ref uuid REFERENCES disc_versions(id) ON DELETE CASCADE,
  principio_pt text NOT NULL,
  principio_en text,
  como_aplicamos_pt text,
  como_aplicamos_en text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_disc_ethics_version ON disc_ethics(version_ref);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on all DISC tables
ALTER TABLE disc_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_items_norm ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_blocks_ipsa ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_likert_map ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_thresholds ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_report_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_words ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_interview ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_quality_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE disc_ethics ENABLE ROW LEVEL SECURITY;

-- Authenticated users can read all DISC data
CREATE POLICY "Authenticated users can read DISC versions"
  ON disc_versions FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC normative items"
  ON disc_items_norm FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC ipsative blocks"
  ON disc_blocks_ipsa FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC scenarios"
  ON disc_scenarios FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC Likert mapping"
  ON disc_likert_map FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC rules"
  ON disc_rules FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC thresholds"
  ON disc_thresholds FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC report templates"
  ON disc_report_templates FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC words"
  ON disc_words FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC interview guide"
  ON disc_interview FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC quality checks"
  ON disc_quality_checks FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read DISC ethics"
  ON disc_ethics FOR SELECT
  TO authenticated
  USING (true);

-- Only admins can insert/update/delete DISC data
CREATE POLICY "Admins can manage DISC versions"
  ON disc_versions FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC normative items"
  ON disc_items_norm FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC ipsative blocks"
  ON disc_blocks_ipsa FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC scenarios"
  ON disc_scenarios FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC Likert mapping"
  ON disc_likert_map FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC rules"
  ON disc_rules FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC thresholds"
  ON disc_thresholds FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC report templates"
  ON disc_report_templates FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC words"
  ON disc_words FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC interview guide"
  ON disc_interview FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC quality checks"
  ON disc_quality_checks FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );

CREATE POLICY "Admins can manage DISC ethics"
  ON disc_ethics FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
    )
  );
