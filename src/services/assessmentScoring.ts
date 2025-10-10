import { supabase } from '../lib/supabase';
import type {
  AssessmentInstance,
  Question,
  Response,
  ScoreProfile,
  DimensionScores,
  PercentileScores,
  NormScores,
  NormScore,
  ValidationData,
  DimensionInterpretation,
  ComparisonResult,
  AssessmentFramework,
  QuestionOption
} from '../types/assessments';

export class AssessmentScorer {
  private instance: AssessmentInstance;
  private responses: Response[];
  private questions: Question[];
  private questionOptions: Map<string, QuestionOption[]>;
  private framework: AssessmentFramework;

  constructor(
    instance: AssessmentInstance,
    responses: Response[],
    questions: Question[],
    questionOptions: Map<string, QuestionOption[]>
  ) {
    this.instance = instance;
    this.responses = responses;
    this.questions = questions;
    this.questionOptions = questionOptions;
    this.framework = 'BIG_FIVE';
  }

  async calculateAllScores(): Promise<ScoreProfile> {
    const dimensionScores = this.calculateDimensionScores();
    const percentileScores = await this.calculatePercentileScores(dimensionScores);
    const normScores = await this.calculateNormScores(dimensionScores);
    const { profileType, strengths, developmentAreas, recommendations } =
      this.generateProfileInterpretation(dimensionScores, percentileScores);

    const validator = new AssessmentValidator(this.instance, this.responses, this.questions);
    const validationData = validator.validateCompletion();
    const patternAnalysis = validator.detectResponsePatterns(this.questionOptions);

    const scoreProfile: Partial<ScoreProfile> = {
      organization_id: this.instance.organization_id,
      instance_id: this.instance.id,
      dimension_scores: dimensionScores,
      percentile_scores: percentileScores,
      norm_scores: normScores,
      profile_type: profileType,
      strengths,
      development_areas: developmentAreas,
      recommendations,
      validation_data: {
        ...validationData,
        ...patternAnalysis
      }
    };

    const { data, error } = await supabase
      .from('score_profiles')
      .upsert(scoreProfile)
      .select()
      .single();

    if (error) throw error;
    return data as ScoreProfile;
  }

  private calculateDimensionScores(): DimensionScores {
    const dimensionTotals: { [key: string]: number } = {};
    const dimensionCounts: { [key: string]: number } = {};
    const dimensionWeights: { [key: string]: number } = {};

    for (const response of this.responses) {
      const question = this.questions.find(q => q.id === response.question_id);
      if (!question) continue;

      const dimension = question.dimension || 'general';
      let score = this.getNumericScore(response, question.question_id);

      if (score === null) continue;

      if (question.reverse_scored) {
        score = this.applyReverseScoring(score, question.question_type);
      }

      const weightedScore = score * question.weight;

      if (!dimensionTotals[dimension]) {
        dimensionTotals[dimension] = 0;
        dimensionCounts[dimension] = 0;
        dimensionWeights[dimension] = 0;
      }

      dimensionTotals[dimension] += weightedScore;
      dimensionCounts[dimension] += 1;
      dimensionWeights[dimension] += question.weight;
    }

    const dimensionScores: DimensionScores = {};
    for (const dimension in dimensionTotals) {
      if (dimensionWeights[dimension] > 0) {
        dimensionScores[dimension] = dimensionTotals[dimension] / dimensionWeights[dimension];
      } else {
        dimensionScores[dimension] = 0;
      }
    }

    return dimensionScores;
  }

  private getNumericScore(response: Response, questionId: string): number | null {
    if (response.numeric_value !== undefined && response.numeric_value !== null) {
      return response.numeric_value;
    } else if (response.selected_option_id) {
      const options = this.questionOptions.get(questionId);
      const option = options?.find(o => o.id === response.selected_option_id);
      return option ? option.value : null;
    }
    return null;
  }

  private applyReverseScoring(score: number, questionType: string): number {
    if (questionType === 'LIKERT_5') {
      return 6.0 - score;
    } else if (questionType === 'LIKERT_7') {
      return 8.0 - score;
    }
    return score;
  }

  private async calculatePercentileScores(dimensionScores: DimensionScores): Promise<PercentileScores> {
    const percentileScores: PercentileScores = {};
    const comparisonData = await this.getComparisonData();

    for (const [dimension, score] of Object.entries(dimensionScores)) {
      if (comparisonData[dimension] && comparisonData[dimension].length > 0) {
        percentileScores[dimension] = this.calculatePercentile(score, comparisonData[dimension]);
      } else {
        percentileScores[dimension] = this.scoreToPercentileFallback(score);
      }
    }

    return percentileScores;
  }

  private async getComparisonData(): Promise<{ [dimension: string]: number[] }> {
    const { data: instances } = await supabase
      .from('assessment_instances')
      .select('id, assessment_id')
      .eq('organization_id', this.instance.organization_id)
      .eq('status', 'COMPLETED')
      .neq('id', this.instance.id);

    if (!instances) return {};

    const { data: profiles } = await supabase
      .from('score_profiles')
      .select('dimension_scores')
      .in('instance_id', instances.map(i => i.id));

    if (!profiles) return {};

    const comparisonData: { [dimension: string]: number[] } = {};
    for (const profile of profiles) {
      for (const [dimension, score] of Object.entries(profile.dimension_scores as DimensionScores)) {
        if (!comparisonData[dimension]) {
          comparisonData[dimension] = [];
        }
        comparisonData[dimension].push(score);
      }
    }

    return comparisonData;
  }

  private calculatePercentile(score: number, comparisonScores: number[]): number {
    if (comparisonScores.length === 0) return 50.0;

    const belowCount = comparisonScores.filter(s => s < score).length;
    const equalCount = comparisonScores.filter(s => s === score).length;

    const percentile = ((belowCount + 0.5 * equalCount) / comparisonScores.length) * 100;
    return Math.max(1.0, Math.min(99.0, percentile));
  }

  private scoreToPercentileFallback(score: number): number {
    const isSevenPoint = this.questions.some(q => q.question_type === 'LIKERT_7');
    const mean = isSevenPoint ? 4.0 : 3.0;
    const std = isSevenPoint ? 1.5 : 1.0;

    const zScore = (score - mean) / std;
    const percentile = 50.0 * (1.0 + this.erf(zScore / Math.sqrt(2.0)));

    return Math.max(1.0, Math.min(99.0, percentile));
  }

  private erf(x: number): number {
    const sign = x >= 0 ? 1 : -1;
    x = Math.abs(x);

    const a1 = 0.254829592;
    const a2 = -0.284496736;
    const a3 = 1.421413741;
    const a4 = -1.453152027;
    const a5 = 1.061405429;
    const p = 0.3275911;

    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);

    return sign * y;
  }

  private async calculateNormScores(dimensionScores: DimensionScores): Promise<NormScores> {
    const normScores: NormScores = {};
    const comparisonData = await this.getComparisonData();

    for (const [dimension, score] of Object.entries(dimensionScores)) {
      let zScore: number;
      let tScore: number;
      let stenScore: number;

      if (comparisonData[dimension] && comparisonData[dimension].length > 1) {
        const mean = comparisonData[dimension].reduce((a, b) => a + b, 0) / comparisonData[dimension].length;
        const variance = comparisonData[dimension].reduce((a, b) => a + Math.pow(b - mean, 2), 0) / comparisonData[dimension].length;
        const std = Math.sqrt(variance);

        if (std > 0) {
          zScore = (score - mean) / std;
          tScore = 50 + (zScore * 10);
          stenScore = 5.5 + (zScore * 2);
        } else {
          zScore = 0.0;
          tScore = 50.0;
          stenScore = 5.5;
        }
      } else {
        const isSevenPoint = this.questions.some(q => q.question_type === 'LIKERT_7');
        const mean = isSevenPoint ? 4.0 : 3.0;
        const std = isSevenPoint ? 1.5 : 1.0;

        zScore = (score - mean) / std;
        tScore = 50 + (zScore * 10);
        stenScore = 5.5 + (zScore * 2);
      }

      normScores[dimension] = {
        z_score: Math.round(zScore * 100) / 100,
        t_score: Math.max(20, Math.min(80, Math.round(tScore * 10) / 10)),
        sten_score: Math.max(1, Math.min(10, Math.round(stenScore * 10) / 10))
      };
    }

    return normScores;
  }

  private generateProfileInterpretation(
    dimensionScores: DimensionScores,
    percentileScores: PercentileScores
  ): {
    profileType: string;
    strengths: string[];
    developmentAreas: string[];
    recommendations: string[];
  } {
    if (this.framework === 'BIG_FIVE') {
      return this.interpretBigFiveProfile(dimensionScores, percentileScores);
    } else if (this.framework === 'DISC') {
      return this.interpretDiscProfile(dimensionScores, percentileScores);
    } else if (this.framework === 'CAREER_ANCHORS') {
      return this.interpretCareerAnchorsProfile(dimensionScores, percentileScores);
    } else {
      return this.interpretGenericProfile(dimensionScores, percentileScores);
    }
  }

  private interpretBigFiveProfile(
    dimensionScores: DimensionScores,
    percentileScores: PercentileScores
  ): {
    profileType: string;
    strengths: string[];
    developmentAreas: string[];
    recommendations: string[];
  } {
    const strengths: string[] = [];
    const developmentAreas: string[] = [];
    const recommendations: string[] = [];
    const profileDescriptors: string[] = [];

    const dimensions = {
      openness: 'Openness to Experience',
      conscientiousness: 'Conscientiousness',
      extraversion: 'Extraversion',
      agreeableness: 'Agreeableness',
      neuroticism: 'Neuroticism'
    };

    for (const [dimKey, dimName] of Object.entries(dimensions)) {
      const percentile = percentileScores[dimKey] || 50;
      let level: string;

      if (percentile >= 75) {
        level = 'High';
        if (dimKey === 'openness') {
          strengths.push('Creative and open to new experiences');
          recommendations.push('Seek roles that involve innovation and change');
        } else if (dimKey === 'conscientiousness') {
          strengths.push('Highly organized and reliable');
          recommendations.push('Take on leadership roles requiring attention to detail');
        } else if (dimKey === 'extraversion') {
          strengths.push('Energetic and socially confident');
          recommendations.push('Pursue roles involving team leadership and public speaking');
        } else if (dimKey === 'agreeableness') {
          strengths.push('Cooperative and empathetic');
          recommendations.push('Excel in collaborative and customer-facing roles');
        } else if (dimKey === 'neuroticism') {
          developmentAreas.push('May experience higher stress levels');
          recommendations.push('Develop stress management and resilience techniques');
        }
      } else if (percentile <= 25) {
        level = 'Low';
        if (dimKey === 'openness') {
          developmentAreas.push('May prefer routine and familiar approaches');
          recommendations.push('Practice embracing new ideas and methods');
        } else if (dimKey === 'conscientiousness') {
          developmentAreas.push('May benefit from better organization systems');
          recommendations.push('Develop time management and planning skills');
        } else if (dimKey === 'extraversion') {
          strengths.push('Thoughtful and independent worker');
          recommendations.push('Leverage deep thinking in analytical roles');
        } else if (dimKey === 'agreeableness') {
          developmentAreas.push('May need to work on collaboration skills');
          recommendations.push('Practice active listening and empathy');
        } else if (dimKey === 'neuroticism') {
          strengths.push('Emotionally stable and calm under pressure');
          recommendations.push('Take on high-pressure leadership roles');
        }
      } else {
        level = 'Moderate';
      }

      profileDescriptors.push(`${level} ${dimName}`);
    }

    return {
      profileType: profileDescriptors.join(' | '),
      strengths,
      developmentAreas,
      recommendations
    };
  }

  private interpretDiscProfile(
    dimensionScores: DimensionScores,
    percentileScores: PercentileScores
  ): {
    profileType: string;
    strengths: string[];
    developmentAreas: string[];
    recommendations: string[];
  } {
    const dimensions = ['dominance', 'influence', 'steadiness', 'conscientiousness'];
    const dominantStyle = dimensions.reduce((a, b) =>
      (dimensionScores[a] || 0) > (dimensionScores[b] || 0) ? a : b
    );

    let profileType = '';
    let strengths: string[] = [];
    let developmentAreas: string[] = [];
    let recommendations: string[] = [];

    if (dominantStyle === 'dominance') {
      profileType = 'Dominant (D) Style';
      strengths = [
        'Results-oriented and decisive',
        'Takes charge in challenging situations',
        'Direct communication style'
      ];
      developmentAreas = [
        'May need to improve patience with others',
        'Could benefit from more collaborative approach'
      ];
      recommendations = [
        'Seek leadership roles with clear authority',
        'Practice active listening and empathy',
        'Focus on team building skills'
      ];
    } else if (dominantStyle === 'influence') {
      profileType = 'Influential (I) Style';
      strengths = [
        'Enthusiastic and persuasive',
        'Excellent interpersonal skills',
        'Optimistic and inspiring'
      ];
      developmentAreas = [
        'May need to focus more on details',
        'Could improve follow-through on tasks'
      ];
      recommendations = [
        'Excel in sales and marketing roles',
        'Develop project management skills',
        'Practice systematic approach to tasks'
      ];
    } else if (dominantStyle === 'steadiness') {
      profileType = 'Steady (S) Style';
      strengths = [
        'Reliable and supportive team member',
        'Patient and good listener',
        'Consistent performance'
      ];
      developmentAreas = [
        'May resist change and new approaches',
        'Could be more assertive when needed'
      ];
      recommendations = [
        'Thrive in stable, supportive environments',
        'Practice adapting to change',
        'Develop confidence in expressing opinions'
      ];
    } else {
      profileType = 'Conscientious (C) Style';
      strengths = [
        'Detail-oriented and analytical',
        'High quality standards',
        'Systematic and thorough'
      ];
      developmentAreas = [
        'May be overly critical or perfectionist',
        'Could benefit from faster decision-making'
      ];
      recommendations = [
        'Excel in analytical and quality-focused roles',
        'Practice making decisions with incomplete information',
        'Balance perfectionism with efficiency'
      ];
    }

    return { profileType, strengths, developmentAreas, recommendations };
  }

  private interpretCareerAnchorsProfile(
    dimensionScores: DimensionScores,
    percentileScores: PercentileScores
  ): {
    profileType: string;
    strengths: string[];
    developmentAreas: string[];
    recommendations: string[];
  } {
    const strengths: string[] = [];
    const developmentAreas: string[] = [];
    const recommendations: string[] = [];

    const anchorScores = Object.entries(dimensionScores).sort(([, a], [, b]) => b - a);
    const topAnchors = anchorScores.slice(0, 2);

    let profileType = `Primary: ${topAnchors[0][0].replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`;
    if (topAnchors.length > 1) {
      profileType += ` | Secondary: ${topAnchors[1][0].replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`;
    }

    for (const [anchor] of topAnchors) {
      if (anchor === 'technical_functional') {
        strengths.push('Strong technical expertise and competence');
        recommendations.push('Pursue roles that leverage your technical skills');
        recommendations.push('Consider becoming a subject matter expert');
      } else if (anchor === 'general_managerial') {
        strengths.push('Leadership and management potential');
        recommendations.push('Seek management and leadership opportunities');
        recommendations.push('Develop strategic thinking skills');
      } else if (anchor === 'autonomy_independence') {
        strengths.push('Self-directed and independent');
        recommendations.push('Look for roles with high autonomy');
        recommendations.push('Consider entrepreneurial opportunities');
      } else if (anchor === 'security_stability') {
        strengths.push('Values stability and long-term planning');
        recommendations.push('Seek stable organizations with clear career paths');
        developmentAreas.push('May need to embrace more change and risk');
      } else if (anchor === 'entrepreneurial_creativity') {
        strengths.push('Innovative and entrepreneurial mindset');
        recommendations.push('Consider startup environments or innovation roles');
        recommendations.push('Develop business and financial skills');
      }
    }

    return { profileType, strengths, developmentAreas, recommendations };
  }

  private interpretGenericProfile(
    dimensionScores: DimensionScores,
    percentileScores: PercentileScores
  ): {
    profileType: string;
    strengths: string[];
    developmentAreas: string[];
    recommendations: string[];
  } {
    const strengths: string[] = [];
    const developmentAreas: string[] = [];
    const recommendations: string[] = [];

    const sortedDimensions = Object.entries(dimensionScores).sort(([, a], [, b]) => b - a);

    if (sortedDimensions.length > 0) {
      const [topDim] = sortedDimensions[0];
      strengths.push(`Strong in ${topDim.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`);

      if (sortedDimensions.length > 1) {
        const [bottomDim] = sortedDimensions[sortedDimensions.length - 1];
        developmentAreas.push(`Opportunity to develop ${bottomDim.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`);
        recommendations.push(`Focus on improving ${bottomDim.replace(/_/g, ' ').toLowerCase()} skills`);
      }
    }

    return {
      profileType: 'Custom Assessment Profile',
      strengths,
      developmentAreas,
      recommendations
    };
  }
}

export class AssessmentValidator {
  private instance: AssessmentInstance;
  private responses: Response[];
  private questions: Question[];

  constructor(instance: AssessmentInstance, responses: Response[], questions: Question[]) {
    this.instance = instance;
    this.responses = responses;
    this.questions = questions;
  }

  validateCompletion(): ValidationData {
    const totalQuestions = this.questions.filter(q => q.is_active).length;
    const answeredQuestions = this.responses.length;
    const requiredQuestions = this.questions.filter(q => q.is_active && q.required).length;
    const answeredRequired = this.responses.filter(r => {
      const q = this.questions.find(q => q.id === r.question_id);
      return q?.required;
    }).length;

    return {
      is_complete: answeredQuestions >= totalQuestions,
      completion_rate: totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0,
      required_complete: answeredRequired >= requiredQuestions,
      missing_required: requiredQuestions - answeredRequired,
      total_questions: totalQuestions,
      answered_questions: answeredQuestions,
      warnings: []
    };
  }

  detectResponsePatterns(questionOptions: Map<string, QuestionOption[]>): Partial<ValidationData> {
    const numericResponses: number[] = [];

    for (const response of this.responses) {
      let value: number | null = null;

      if (response.numeric_value !== undefined && response.numeric_value !== null) {
        value = response.numeric_value;
      } else if (response.selected_option_id) {
        const question = this.questions.find(q => q.id === response.question_id);
        if (question) {
          const options = questionOptions.get(question.id);
          const option = options?.find(o => o.id === response.selected_option_id);
          if (option) value = option.value;
        }
      }

      if (value !== null) numericResponses.push(value);
    }

    if (numericResponses.length === 0) {
      return { warnings: [] };
    }

    const warnings: string[] = [];

    if (new Set(numericResponses).size === 1) {
      warnings.push('All responses are identical - may indicate disengagement');
    }

    const minVal = Math.min(...numericResponses);
    const maxVal = Math.max(...numericResponses);
    const extremeResponses = numericResponses.filter(r => r === minVal || r === maxVal).length;
    const extremeRate = extremeResponses / numericResponses.length;

    if (extremeRate > 0.8) {
      warnings.push('High use of extreme responses - may indicate response bias');
    }

    const isSevenPoint = this.questions.some(q => q.question_type === 'LIKERT_7');
    const middleValues = isSevenPoint ? [3, 4, 5] : [2, 3, 4];
    const middleResponses = numericResponses.filter(r => middleValues.includes(r)).length;
    const middleRate = middleResponses / numericResponses.length;

    if (middleRate > 0.9) {
      warnings.push('High use of middle responses - may indicate uncertainty or social desirability');
    }

    const mean = numericResponses.reduce((a, b) => a + b, 0) / numericResponses.length;
    const variance = numericResponses.length > 1
      ? numericResponses.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / numericResponses.length
      : 0;

    return {
      warnings,
      extreme_response_rate: extremeRate,
      middle_response_rate: middleRate,
      response_variance: variance
    };
  }
}

export async function calculateAssessmentScores(instanceId: string): Promise<ScoreProfile> {
  const { data: instance } = await supabase
    .from('assessment_instances')
    .select('*')
    .eq('id', instanceId)
    .single();

  if (!instance) throw new Error('Assessment instance not found');

  const { data: responses } = await supabase
    .from('responses')
    .select('*')
    .eq('instance_id', instanceId);

  if (!responses) throw new Error('No responses found');

  const { data: assessment } = await supabase
    .from('assessment_definitions')
    .select('*')
    .eq('id', instance.assessment_id)
    .single();

  if (!assessment) throw new Error('Assessment definition not found');

  const { data: questions } = await supabase
    .from('questions')
    .select('*')
    .eq('assessment_id', assessment.id)
    .eq('is_active', true);

  if (!questions) throw new Error('No questions found');

  const { data: options } = await supabase
    .from('question_options')
    .select('*')
    .in('question_id', questions.map(q => q.id));

  const questionOptions = new Map<string, QuestionOption[]>();
  if (options) {
    for (const option of options) {
      if (!questionOptions.has(option.question_id)) {
        questionOptions.set(option.question_id, []);
      }
      questionOptions.get(option.question_id)!.push(option);
    }
  }

  const scorer = new AssessmentScorer(
    instance as AssessmentInstance,
    responses as Response[],
    questions as Question[],
    questionOptions
  );

  return await scorer.calculateAllScores();
}

export class ScoreInterpreter {
  static getDimensionInterpretation(
    dimension: string,
    score: number,
    percentile: number,
    framework: AssessmentFramework
  ): DimensionInterpretation {
    if (framework === 'BIG_FIVE') {
      return this.interpretBigFiveDimension(dimension, score, percentile);
    } else if (framework === 'DISC') {
      return this.interpretDiscDimension(dimension, score, percentile);
    }

    return {
      level: 'Moderate',
      description: `Your score in ${dimension} is within the average range.`,
      implications: 'This suggests a balanced approach in this area.',
      development_tips: `Continue to develop your ${dimension} skills through practice and feedback.`
    };
  }

  private static interpretBigFiveDimension(
    dimension: string,
    score: number,
    percentile: number
  ): DimensionInterpretation {
    const level = percentile >= 70 ? 'High' : percentile <= 30 ? 'Low' : 'Moderate';

    const interpretations: any = {
      openness: {
        High: {
          description: 'You are very open to new experiences, creative, and intellectually curious.',
          implications: 'You likely enjoy variety, innovation, and abstract thinking.',
          development_tips: 'Channel your creativity into innovative projects and seek diverse experiences.'
        },
        Low: {
          description: 'You prefer familiar routines and practical approaches.',
          implications: 'You value tradition, stability, and concrete thinking.',
          development_tips: 'Try to gradually expose yourself to new ideas and experiences.'
        },
        Moderate: {
          description: 'You balance openness to new experiences with appreciation for tradition.',
          implications: 'You can adapt to change while maintaining stability.',
          development_tips: 'Continue to explore new ideas while leveraging your practical nature.'
        }
      },
      conscientiousness: {
        High: {
          description: 'You are highly organized, disciplined, and goal-oriented.',
          implications: 'You excel at planning, following through, and maintaining high standards.',
          development_tips: 'Use your organizational skills to lead projects and mentor others.'
        },
        Low: {
          description: 'You tend to be more flexible and spontaneous in your approach.',
          implications: 'You may prefer adaptable environments and creative freedom.',
          development_tips: 'Develop planning and organizational systems to improve efficiency.'
        },
        Moderate: {
          description: 'You balance organization with flexibility.',
          implications: 'You can be both structured and adaptable as situations require.',
          development_tips: 'Continue to refine your balance between planning and spontaneity.'
        }
      }
    };

    const dimData = interpretations[dimension]?.[level] || {
      description: `Your ${dimension} score is in the ${level.toLowerCase()} range.`,
      implications: 'This suggests a balanced approach.',
      development_tips: `Continue developing your ${dimension} skills.`
    };

    return {
      level: `${level} ${dimension.charAt(0).toUpperCase() + dimension.slice(1)}`,
      ...dimData
    };
  }

  private static interpretDiscDimension(
    dimension: string,
    score: number,
    percentile: number
  ): DimensionInterpretation {
    const level = percentile >= 70 ? 'High' : percentile <= 30 ? 'Low' : 'Moderate';

    return {
      level: `${level} ${dimension.charAt(0).toUpperCase() + dimension.slice(1)}`,
      description: `Your ${dimension} score indicates specific behavioral tendencies.`,
      implications: 'This affects how you interact with others and approach tasks.',
      development_tips: `Leverage your ${dimension} style while developing complementary skills.`
    };
  }
}

export async function compareProfiles(
  profileId1: string,
  profileId2: string
): Promise<ComparisonResult> {
  const { data: profile1 } = await supabase
    .from('score_profiles')
    .select('*, instance:assessment_instances(assessment:assessment_definitions(framework))')
    .eq('id', profileId1)
    .single();

  const { data: profile2 } = await supabase
    .from('score_profiles')
    .select('*, instance:assessment_instances(assessment:assessment_definitions(framework))')
    .eq('id', profileId2)
    .single();

  if (!profile1 || !profile2) {
    throw new Error('One or both profiles not found');
  }

  const framework = (profile1.instance as any).assessment.framework;

  const comparison: ComparisonResult = {
    framework,
    dimension_differences: {},
    similarity_score: 0,
    key_differences: []
  };

  let totalDiff = 0;
  let dimensionCount = 0;

  for (const dimension in profile1.dimension_scores) {
    if (dimension in profile2.dimension_scores) {
      const score1 = profile1.dimension_scores[dimension];
      const score2 = profile2.dimension_scores[dimension];
      const diff = Math.abs(score1 - score2);

      comparison.dimension_differences[dimension] = {
        profile1_score: score1,
        profile2_score: score2,
        difference: diff,
        significant: diff > 1.0
      };

      totalDiff += diff;
      dimensionCount += 1;

      if (diff > 1.5) {
        comparison.key_differences.push(
          `Significant difference in ${dimension}: ${score1.toFixed(1)} vs ${score2.toFixed(1)}`
        );
      }
    }
  }

  if (dimensionCount > 0) {
    const avgDiff = totalDiff / dimensionCount;
    comparison.similarity_score = Math.max(0, 100 - (avgDiff * 20));
  }

  return comparison;
}
