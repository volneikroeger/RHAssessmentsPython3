-- Allow anonymous users to view assessment instances via valid token
CREATE POLICY "Anyone can view assessment instance with valid token"
  ON assessment_instances FOR SELECT
  TO anon
  USING (
    token IS NOT NULL
    AND (expires_at IS NULL OR expires_at > now())
    AND status IN ('INVITED', 'STARTED', 'IN_PROGRESS')
  );

-- Allow anonymous users to update assessment instance progress via token
CREATE POLICY "Anyone can update assessment instance via token"
  ON assessment_instances FOR UPDATE
  TO anon
  USING (
    token IS NOT NULL
    AND (expires_at IS NULL OR expires_at > now())
    AND status IN ('INVITED', 'STARTED', 'IN_PROGRESS')
  )
  WITH CHECK (
    token IS NOT NULL
    AND status IN ('STARTED', 'IN_PROGRESS', 'COMPLETED')
  );

-- Allow anonymous users to view questions for their assessment
CREATE POLICY "Anyone can view questions for valid assessment"
  ON questions FOR SELECT
  TO anon
  USING (
    assessment_id IN (
      SELECT assessment_id FROM assessment_instances
      WHERE token IS NOT NULL
      AND (expires_at IS NULL OR expires_at > now())
    )
    AND is_active = true
  );

-- Allow anonymous users to view question options
CREATE POLICY "Anyone can view options for accessible questions"
  ON question_options FOR SELECT
  TO anon
  USING (
    question_id IN (
      SELECT q.id FROM questions q
      JOIN assessment_instances ai ON ai.assessment_id = q.assessment_id
      WHERE ai.token IS NOT NULL
      AND (ai.expires_at IS NULL OR ai.expires_at > now())
      AND q.is_active = true
    )
  );

-- Allow anonymous users to view their responses
CREATE POLICY "Anyone can view responses for valid token"
  ON responses FOR SELECT
  TO anon
  USING (
    instance_id IN (
      SELECT id FROM assessment_instances
      WHERE token IS NOT NULL
      AND (expires_at IS NULL OR expires_at > now())
    )
  );

-- Allow anonymous users to create responses via token
CREATE POLICY "Anyone can create responses with valid token"
  ON responses FOR INSERT
  TO anon
  WITH CHECK (
    instance_id IN (
      SELECT id FROM assessment_instances
      WHERE token IS NOT NULL
      AND (expires_at IS NULL OR expires_at > now())
      AND status IN ('INVITED', 'STARTED', 'IN_PROGRESS')
    )
  );

-- Allow anonymous users to update their responses
CREATE POLICY "Anyone can update responses with valid token"
  ON responses FOR UPDATE
  TO anon
  USING (
    instance_id IN (
      SELECT id FROM assessment_instances
      WHERE token IS NOT NULL
      AND (expires_at IS NULL OR expires_at > now())
      AND status IN ('INVITED', 'STARTED', 'IN_PROGRESS')
    )
  )
  WITH CHECK (
    instance_id IN (
      SELECT id FROM assessment_instances
      WHERE token IS NOT NULL
      AND (expires_at IS NULL OR expires_at > now())
      AND status IN ('INVITED', 'STARTED', 'IN_PROGRESS')
    )
  );

-- Allow anonymous users to view assessment definitions for their instances
CREATE POLICY "Anyone can view assessment definition via token"
  ON assessment_definitions FOR SELECT
  TO anon
  USING (
    id IN (
      SELECT assessment_id FROM assessment_instances
      WHERE token IS NOT NULL
      AND (expires_at IS NULL OR expires_at > now())
    )
  );