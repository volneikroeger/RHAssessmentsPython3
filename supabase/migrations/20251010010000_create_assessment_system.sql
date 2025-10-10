/*
  # Create Comprehensive Assessment System

  1. New Tables
    - `assessment_definitions`
      - Defines assessment frameworks (Big Five, DISC, Career Anchors, etc.)
      - Stores configuration, instructions, and metadata
      - Supports versioning and status management

    - `questions`
      - Individual assessment questions
      - Multiple question types (Likert scales, multiple choice, ranking, text)
      - Supports reverse scoring and weighting
      - Belongs to assessment definitions

    - `question_options`
      - Response options for questions
      - Numeric values for scoring
      - Order and display text

    - `assessment_instances`
      - Individual assessment sessions
      - Tracks progress and completion status
      - Token-based access control
      - Links to users and organizations

    - `responses`
      - User responses to questions
      - Supports multiple response types (numeric, text, selected option)
      - Tracks timing information

    - `score_profiles`
      - Calculated assessment scores
      - Dimensional scores, percentiles, norm scores
      - Profile interpretations and recommendations
      - Validation metadata

    - `assessment_reports`
      - Generated reports (HTML, PDF, JSON)
      - Access control and sharing
      - File storage references

  2. Security
    - Enable RLS on all tables
    - Organization-scoped access policies
    - User-specific access for assessment instances
    - Admin override capabilities

  3. Important Notes
    - All UUID fields use gen_random_uuid() for automatic generation
    - JSONB fields for flexible data storage (scores, interpretations)
    - Timestamps track creation and updates
    - Foreign key constraints ensure referential integrity
*/

-- Assessment Definitions Table
CREATE TABLE IF NOT EXISTS assessment_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  framework text NOT NULL CHECK (framework IN ('BIG_FIVE', 'DISC', 'CAREER_ANCHORS', 'OCEAN', 'CUSTOM')),
  version text DEFAULT '1.0',
  status text NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'ACTIVE', 'ARCHIVED')),
  instructions text,
  estimated_duration integer DEFAULT 15,
  randomize_questions boolean DEFAULT false,
  allow_skip boolean DEFAULT false,
  show_progress boolean DEFAULT true,
  created_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Questions Table
CREATE TABLE IF NOT EXISTS questions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id uuid NOT NULL REFERENCES assessment_definitions(id) ON DELETE CASCADE,
  text text NOT NULL,
  question_type text NOT NULL CHECK (question_type IN ('LIKERT_5', 'LIKERT_7', 'MULTIPLE_CHOICE', 'FORCED_CHOICE', 'RANKING', 'TEXT')),
  order_number integer NOT NULL DEFAULT 0,
  dimension text,
  reverse_scored boolean DEFAULT false,
  weight numeric(5,2) DEFAULT 1.0,
  required boolean DEFAULT true,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Question Options Table
CREATE TABLE IF NOT EXISTS question_options (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  text text NOT NULL,
  value integer NOT NULL,
  order_number integer NOT NULL DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

-- Assessment Instances Table
CREATE TABLE IF NOT EXISTS assessment_instances (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  assessment_id uuid NOT NULL REFERENCES assessment_definitions(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'INVITED' CHECK (status IN ('INVITED', 'STARTED', 'IN_PROGRESS', 'COMPLETED', 'EXPIRED', 'CANCELLED')),
  token text UNIQUE NOT NULL,
  invited_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  current_question integer DEFAULT 0,
  progress_percentage numeric(5,2) DEFAULT 0.0,
  invited_at timestamptz DEFAULT now(),
  started_at timestamptz,
  completed_at timestamptz,
  expires_at timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Responses Table
CREATE TABLE IF NOT EXISTS responses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  instance_id uuid NOT NULL REFERENCES assessment_instances(id) ON DELETE CASCADE,
  question_id uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  numeric_value integer,
  text_value text,
  selected_option_id uuid REFERENCES question_options(id) ON DELETE SET NULL,
  answered_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(instance_id, question_id)
);

-- Score Profiles Table
CREATE TABLE IF NOT EXISTS score_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  instance_id uuid UNIQUE NOT NULL REFERENCES assessment_instances(id) ON DELETE CASCADE,
  dimension_scores jsonb DEFAULT '{}',
  percentile_scores jsonb DEFAULT '{}',
  norm_scores jsonb DEFAULT '{}',
  profile_type text,
  strengths jsonb DEFAULT '[]',
  development_areas jsonb DEFAULT '[]',
  recommendations jsonb DEFAULT '[]',
  validation_data jsonb DEFAULT '{}',
  calculated_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Assessment Reports Table
CREATE TABLE IF NOT EXISTS assessment_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  instance_id uuid NOT NULL REFERENCES assessment_instances(id) ON DELETE CASCADE,
  format text NOT NULL CHECK (format IN ('HTML', 'PDF', 'JSON')),
  title text NOT NULL,
  content text,
  file_path text,
  is_public boolean DEFAULT false,
  generated_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_assessment_definitions_org ON assessment_definitions(organization_id);
CREATE INDEX IF NOT EXISTS idx_assessment_definitions_status ON assessment_definitions(status);
CREATE INDEX IF NOT EXISTS idx_questions_assessment ON questions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_questions_order ON questions(assessment_id, order_number);
CREATE INDEX IF NOT EXISTS idx_question_options_question ON question_options(question_id);
CREATE INDEX IF NOT EXISTS idx_assessment_instances_org ON assessment_instances(organization_id);
CREATE INDEX IF NOT EXISTS idx_assessment_instances_user ON assessment_instances(user_id);
CREATE INDEX IF NOT EXISTS idx_assessment_instances_token ON assessment_instances(token);
CREATE INDEX IF NOT EXISTS idx_assessment_instances_status ON assessment_instances(status);
CREATE INDEX IF NOT EXISTS idx_responses_instance ON responses(instance_id);
CREATE INDEX IF NOT EXISTS idx_responses_question ON responses(question_id);
CREATE INDEX IF NOT EXISTS idx_score_profiles_org ON score_profiles(organization_id);
CREATE INDEX IF NOT EXISTS idx_score_profiles_instance ON score_profiles(instance_id);
CREATE INDEX IF NOT EXISTS idx_assessment_reports_org ON assessment_reports(organization_id);
CREATE INDEX IF NOT EXISTS idx_assessment_reports_instance ON assessment_reports(instance_id);

-- Enable Row Level Security
ALTER TABLE assessment_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE score_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_reports ENABLE ROW LEVEL SECURITY;

-- RLS Policies for assessment_definitions
CREATE POLICY "Users can view assessments in their organization"
  ON assessment_definitions FOR SELECT
  TO authenticated
  USING (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid() AND is_active = true
    )
  );

CREATE POLICY "Org admins can create assessments"
  ON assessment_definitions FOR INSERT
  TO authenticated
  WITH CHECK (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR')
      AND is_active = true
    )
  );

CREATE POLICY "Org admins can update assessments"
  ON assessment_definitions FOR UPDATE
  TO authenticated
  USING (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR')
      AND is_active = true
    )
  );

CREATE POLICY "Org admins can delete assessments"
  ON assessment_definitions FOR DELETE
  TO authenticated
  USING (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR')
      AND is_active = true
    )
  );

-- RLS Policies for questions
CREATE POLICY "Users can view questions in their org assessments"
  ON questions FOR SELECT
  TO authenticated
  USING (
    assessment_id IN (
      SELECT id FROM assessment_definitions
      WHERE organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid() AND is_active = true
      )
    )
  );

CREATE POLICY "Org admins can manage questions"
  ON questions FOR ALL
  TO authenticated
  USING (
    assessment_id IN (
      SELECT id FROM assessment_definitions
      WHERE organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid()
        AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR')
        AND is_active = true
      )
    )
  );

-- RLS Policies for question_options
CREATE POLICY "Users can view question options"
  ON question_options FOR SELECT
  TO authenticated
  USING (
    question_id IN (
      SELECT q.id FROM questions q
      JOIN assessment_definitions ad ON ad.id = q.assessment_id
      WHERE ad.organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid() AND is_active = true
      )
    )
  );

CREATE POLICY "Org admins can manage question options"
  ON question_options FOR ALL
  TO authenticated
  USING (
    question_id IN (
      SELECT q.id FROM questions q
      JOIN assessment_definitions ad ON ad.id = q.assessment_id
      WHERE ad.organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid()
        AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR')
        AND is_active = true
      )
    )
  );

-- RLS Policies for assessment_instances
CREATE POLICY "Users can view their own assessment instances"
  ON assessment_instances FOR SELECT
  TO authenticated
  USING (
    user_id = auth.uid() OR
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR', 'MANAGER')
      AND is_active = true
    )
  );

CREATE POLICY "Org admins can create assessment instances"
  ON assessment_instances FOR INSERT
  TO authenticated
  WITH CHECK (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR', 'MANAGER')
      AND is_active = true
    )
  );

CREATE POLICY "Users can update their own instances"
  ON assessment_instances FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid());

-- RLS Policies for responses
CREATE POLICY "Users can view their own responses"
  ON responses FOR SELECT
  TO authenticated
  USING (
    instance_id IN (
      SELECT id FROM assessment_instances
      WHERE user_id = auth.uid() OR
      organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid()
        AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR', 'MANAGER')
        AND is_active = true
      )
    )
  );

CREATE POLICY "Users can create their own responses"
  ON responses FOR INSERT
  TO authenticated
  WITH CHECK (
    instance_id IN (
      SELECT id FROM assessment_instances
      WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update their own responses"
  ON responses FOR UPDATE
  TO authenticated
  USING (
    instance_id IN (
      SELECT id FROM assessment_instances
      WHERE user_id = auth.uid()
    )
  );

-- RLS Policies for score_profiles
CREATE POLICY "Users can view score profiles"
  ON score_profiles FOR SELECT
  TO authenticated
  USING (
    instance_id IN (
      SELECT id FROM assessment_instances
      WHERE user_id = auth.uid() OR
      organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid()
        AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR', 'MANAGER')
        AND is_active = true
      )
    )
  );

CREATE POLICY "System can create score profiles"
  ON score_profiles FOR INSERT
  TO authenticated
  WITH CHECK (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid() AND is_active = true
    )
  );

CREATE POLICY "System can update score profiles"
  ON score_profiles FOR UPDATE
  TO authenticated
  USING (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid() AND is_active = true
    )
  );

-- RLS Policies for assessment_reports
CREATE POLICY "Users can view reports"
  ON assessment_reports FOR SELECT
  TO authenticated
  USING (
    is_public = true OR
    instance_id IN (
      SELECT id FROM assessment_instances
      WHERE user_id = auth.uid() OR
      organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid()
        AND role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR', 'MANAGER')
        AND is_active = true
      )
    )
  );

CREATE POLICY "System can create reports"
  ON assessment_reports FOR INSERT
  TO authenticated
  WITH CHECK (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid() AND is_active = true
    )
  );
