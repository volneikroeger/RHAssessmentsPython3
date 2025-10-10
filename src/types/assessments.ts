export type AssessmentFramework = 'BIG_FIVE' | 'DISC' | 'CAREER_ANCHORS' | 'OCEAN' | 'CUSTOM';

export type AssessmentStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED';

export type QuestionType = 'LIKERT_5' | 'LIKERT_7' | 'MULTIPLE_CHOICE' | 'FORCED_CHOICE' | 'RANKING' | 'TEXT';

export type InstanceStatus = 'INVITED' | 'STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'EXPIRED' | 'CANCELLED';

export type ReportFormat = 'HTML' | 'PDF' | 'JSON';

export interface AssessmentDefinition {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  framework: AssessmentFramework;
  version: string;
  status: AssessmentStatus;
  instructions?: string;
  estimated_duration: number;
  randomize_questions: boolean;
  allow_skip: boolean;
  show_progress: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface Question {
  id: string;
  assessment_id: string;
  text: string;
  question_type: QuestionType;
  order_number: number;
  dimension?: string;
  reverse_scored: boolean;
  weight: number;
  required: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface QuestionOption {
  id: string;
  question_id: string;
  text: string;
  value: number;
  order_number: number;
  created_at: string;
}

export interface AssessmentInstance {
  id: string;
  organization_id: string;
  assessment_id: string;
  user_id: string;
  status: InstanceStatus;
  token: string;
  invited_by?: string;
  current_question: number;
  progress_percentage: number;
  invited_at: string;
  started_at?: string;
  completed_at?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Response {
  id: string;
  instance_id: string;
  question_id: string;
  numeric_value?: number;
  text_value?: string;
  selected_option_id?: string;
  answered_at: string;
  updated_at: string;
}

export interface DimensionScores {
  [dimension: string]: number;
}

export interface PercentileScores {
  [dimension: string]: number;
}

export interface NormScore {
  z_score: number;
  t_score: number;
  sten_score: number;
}

export interface NormScores {
  [dimension: string]: NormScore;
}

export interface ValidationData {
  is_complete: boolean;
  completion_rate: number;
  required_complete: boolean;
  missing_required: number;
  total_questions: number;
  answered_questions: number;
  warnings: string[];
  extreme_response_rate?: number;
  middle_response_rate?: number;
  response_variance?: number;
}

export interface ScoreProfile {
  id: string;
  organization_id: string;
  instance_id: string;
  dimension_scores: DimensionScores;
  percentile_scores: PercentileScores;
  norm_scores: NormScores;
  profile_type?: string;
  strengths: string[];
  development_areas: string[];
  recommendations: string[];
  validation_data: ValidationData;
  calculated_at: string;
  updated_at: string;
}

export interface AssessmentReport {
  id: string;
  organization_id: string;
  instance_id: string;
  format: ReportFormat;
  title: string;
  content?: string;
  file_path?: string;
  is_public: boolean;
  generated_at: string;
  updated_at: string;
}

export interface DimensionInterpretation {
  level: string;
  description: string;
  implications: string;
  development_tips: string;
}

export interface ComparisonResult {
  framework: AssessmentFramework;
  dimension_differences: {
    [dimension: string]: {
      profile1_score: number;
      profile2_score: number;
      difference: number;
      significant: boolean;
    };
  };
  similarity_score: number;
  key_differences: string[];
}
