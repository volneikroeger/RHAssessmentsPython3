"""
Advanced scoring algorithms for psychological assessments.
"""
import json
import math
import statistics
from typing import Dict, List, Tuple, Optional, Any
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from .models import AssessmentInstance, Response, Question, ScoreProfile

User = get_user_model()


class AssessmentScorer:
    """
    Main class for calculating assessment scores and profiles.
    """
    
    def __init__(self, assessment_instance: AssessmentInstance):
        self.instance = assessment_instance
        self.assessment = assessment_instance.assessment
        self.responses = assessment_instance.responses.select_related('question', 'selected_option')
        self.framework = assessment_instance.assessment.framework
    
    def calculate_all_scores(self) -> ScoreProfile:
        """
        Calculate all scores and create/update ScoreProfile.
        """
        # Calculate raw dimension scores
        dimension_scores = self._calculate_dimension_scores()
        
        # Calculate percentile scores
        percentile_scores = self._calculate_percentile_scores(dimension_scores)
        
        # Calculate norm scores (T-scores, Z-scores)
        norm_scores = self._calculate_norm_scores(dimension_scores)
        
        # Generate profile interpretation
        profile_type, strengths, development_areas, recommendations = self._generate_profile_interpretation(
            dimension_scores, percentile_scores
        )
        
        # Create or update score profile
        score_profile, created = ScoreProfile.objects.get_or_create(
            instance=self.instance,
            defaults={'organization': self.instance.organization}
        )
        
        score_profile.dimension_scores = dimension_scores
        score_profile.percentile_scores = percentile_scores
        score_profile.norm_scores = norm_scores
        score_profile.profile_type = profile_type
        score_profile.strengths = strengths
        score_profile.development_areas = development_areas
        score_profile.recommendations = recommendations
        score_profile.save()
        
        return score_profile
    
    def _calculate_dimension_scores(self) -> Dict[str, float]:
        """
        Calculate raw scores for each dimension.
        """
        dimension_scores = {}
        dimension_totals = {}
        dimension_counts = {}
        dimension_weights = {}
        
        for response in self.responses:
            question = response.question
            dimension = question.dimension or 'general'
            
            # Get numeric value
            score = self._get_numeric_score(response)
            if score is None:
                continue
            
            # Apply reverse scoring if needed
            if question.reverse_scored:
                score = self._apply_reverse_scoring(score, question.question_type)
            
            # Apply question weight
            weighted_score = score * question.weight
            
            # Accumulate scores
            if dimension not in dimension_totals:
                dimension_totals[dimension] = 0
                dimension_counts[dimension] = 0
                dimension_weights[dimension] = 0
            
            dimension_totals[dimension] += weighted_score
            dimension_counts[dimension] += 1
            dimension_weights[dimension] += question.weight
        
        # Calculate averages
        for dimension in dimension_totals:
            if dimension_weights[dimension] > 0:
                dimension_scores[dimension] = dimension_totals[dimension] / dimension_weights[dimension]
            else:
                dimension_scores[dimension] = 0.0
        
        return dimension_scores
    
    def _get_numeric_score(self, response: Response) -> Optional[float]:
        """
        Extract numeric score from response.
        """
        if response.numeric_value is not None:
            return float(response.numeric_value)
        elif response.selected_option:
            return float(response.selected_option.value)
        elif response.text_value:
            # For text responses, we might need custom scoring logic
            return self._score_text_response(response.text_value, response.question)
        return None
    
    def _apply_reverse_scoring(self, score: float, question_type: str) -> float:
        """
        Apply reverse scoring based on question type.
        """
        if question_type == 'LIKERT_5':
            return 6.0 - score
        elif question_type == 'LIKERT_7':
            return 8.0 - score
        elif question_type == 'MULTIPLE_CHOICE':
            # For multiple choice, reverse scoring would need custom logic
            # based on the specific options
            return score
        return score
    
    def _score_text_response(self, text: str, question: Question) -> Optional[float]:
        """
        Score text responses (placeholder for future NLP implementation).
        """
        # This could be expanded with NLP sentiment analysis or keyword matching
        # For now, return None to exclude from scoring
        return None
    
    def _calculate_percentile_scores(self, dimension_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate percentile scores based on normative data.
        """
        percentile_scores = {}
        
        # Get comparison data from other completed assessments
        comparison_data = self._get_comparison_data()
        
        for dimension, score in dimension_scores.items():
            if dimension in comparison_data and comparison_data[dimension]:
                percentile = self._calculate_percentile(score, comparison_data[dimension])
                percentile_scores[dimension] = percentile
            else:
                # If no comparison data, use a simple conversion
                percentile_scores[dimension] = self._score_to_percentile_fallback(score)
        
        return percentile_scores
    
    def _get_comparison_data(self) -> Dict[str, List[float]]:
        """
        Get comparison data from other completed assessments of the same framework.
        """
        comparison_data = {}
        
        # Get completed instances of the same assessment framework
        completed_instances = AssessmentInstance.objects.filter(
            assessment__framework=self.framework,
            status='COMPLETED',
            organization=self.instance.organization  # Same organization for fair comparison
        ).exclude(id=self.instance.id)
        
        # Collect dimension scores from score profiles
        for instance in completed_instances:
            try:
                score_profile = instance.score_profile
                for dimension, score in score_profile.dimension_scores.items():
                    if dimension not in comparison_data:
                        comparison_data[dimension] = []
                    comparison_data[dimension].append(score)
            except ScoreProfile.DoesNotExist:
                continue
        
        return comparison_data
    
    def _calculate_percentile(self, score: float, comparison_scores: List[float]) -> float:
        """
        Calculate percentile rank for a score against comparison data.
        """
        if not comparison_scores:
            return 50.0  # Default to 50th percentile if no data
        
        # Count scores below the current score
        below_count = sum(1 for s in comparison_scores if s < score)
        equal_count = sum(1 for s in comparison_scores if s == score)
        
        # Calculate percentile using the standard formula
        percentile = (below_count + 0.5 * equal_count) / len(comparison_scores) * 100
        
        return max(1.0, min(99.0, percentile))  # Clamp between 1-99
    
    def _score_to_percentile_fallback(self, score: float) -> float:
        """
        Fallback percentile calculation when no comparison data is available.
        """
        # Assume normal distribution with mean=4, std=1.5 for 7-point scales
        if self._is_seven_point_scale():
            mean = 4.0
            std = 1.5
        else:  # 5-point scale
            mean = 3.0
            std = 1.0
        
        # Calculate Z-score
        z_score = (score - mean) / std
        
        # Convert Z-score to percentile using cumulative normal distribution
        percentile = self._z_score_to_percentile(z_score)
        
        return max(1.0, min(99.0, percentile))
    
    def _is_seven_point_scale(self) -> bool:
        """
        Check if this assessment primarily uses 7-point scales.
        """
        seven_point_questions = self.assessment.questions.filter(
            question_type='LIKERT_7'
        ).count()
        five_point_questions = self.assessment.questions.filter(
            question_type='LIKERT_5'
        ).count()
        
        return seven_point_questions > five_point_questions
    
    def _z_score_to_percentile(self, z_score: float) -> float:
        """
        Convert Z-score to percentile using approximation.
        """
        # Using the error function approximation for normal distribution
        # This is a simplified implementation
        return 50.0 * (1.0 + math.erf(z_score / math.sqrt(2.0)))
    
    def _calculate_norm_scores(self, dimension_scores: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """
        Calculate normalized scores (T-scores, Z-scores, Sten scores).
        """
        norm_scores = {}
        comparison_data = self._get_comparison_data()
        
        for dimension, score in dimension_scores.items():
            norm_scores[dimension] = {}
            
            if dimension in comparison_data and len(comparison_data[dimension]) > 1:
                # Calculate with actual data
                mean = statistics.mean(comparison_data[dimension])
                std = statistics.stdev(comparison_data[dimension])
                
                if std > 0:
                    z_score = (score - mean) / std
                    t_score = 50 + (z_score * 10)  # T-score: mean=50, std=10
                    sten_score = 5.5 + (z_score * 2)  # Sten: mean=5.5, std=2
                else:
                    z_score = 0.0
                    t_score = 50.0
                    sten_score = 5.5
            else:
                # Use fallback calculations
                if self._is_seven_point_scale():
                    mean, std = 4.0, 1.5
                else:
                    mean, std = 3.0, 1.0
                
                z_score = (score - mean) / std
                t_score = 50 + (z_score * 10)
                sten_score = 5.5 + (z_score * 2)
            
            norm_scores[dimension] = {
                'z_score': round(z_score, 2),
                't_score': round(max(20, min(80, t_score)), 1),  # Clamp T-scores
                'sten_score': round(max(1, min(10, sten_score)), 1)  # Clamp Sten scores
            }
        
        return norm_scores
    
    def _generate_profile_interpretation(
        self, 
        dimension_scores: Dict[str, float], 
        percentile_scores: Dict[str, float]
    ) -> Tuple[str, List[str], List[str], List[str]]:
        """
        Generate profile interpretation based on scores.
        """
        if self.framework == 'BIG_FIVE':
            return self._interpret_big_five_profile(dimension_scores, percentile_scores)
        elif self.framework == 'DISC':
            return self._interpret_disc_profile(dimension_scores, percentile_scores)
        elif self.framework == 'CAREER_ANCHORS':
            return self._interpret_career_anchors_profile(dimension_scores, percentile_scores)
        else:
            return self._interpret_generic_profile(dimension_scores, percentile_scores)
    
    def _interpret_big_five_profile(
        self, 
        dimension_scores: Dict[str, float], 
        percentile_scores: Dict[str, float]
    ) -> Tuple[str, List[str], List[str], List[str]]:
        """
        Interpret Big Five personality profile.
        """
        strengths = []
        development_areas = []
        recommendations = []
        
        # Analyze each Big Five dimension
        dimensions = {
            'openness': 'Openness to Experience',
            'conscientiousness': 'Conscientiousness',
            'extraversion': 'Extraversion',
            'agreeableness': 'Agreeableness',
            'neuroticism': 'Neuroticism'
        }
        
        profile_descriptors = []
        
        for dim_key, dim_name in dimensions.items():
            score = dimension_scores.get(dim_key, 0)
            percentile = percentile_scores.get(dim_key, 50)
            
            if percentile >= 75:
                level = "High"
                if dim_key == 'openness':
                    strengths.append("Creative and open to new experiences")
                    recommendations.append("Seek roles that involve innovation and change")
                elif dim_key == 'conscientiousness':
                    strengths.append("Highly organized and reliable")
                    recommendations.append("Take on leadership roles requiring attention to detail")
                elif dim_key == 'extraversion':
                    strengths.append("Energetic and socially confident")
                    recommendations.append("Pursue roles involving team leadership and public speaking")
                elif dim_key == 'agreeableness':
                    strengths.append("Cooperative and empathetic")
                    recommendations.append("Excel in collaborative and customer-facing roles")
                elif dim_key == 'neuroticism':
                    development_areas.append("May experience higher stress levels")
                    recommendations.append("Develop stress management and resilience techniques")
            
            elif percentile <= 25:
                level = "Low"
                if dim_key == 'openness':
                    development_areas.append("May prefer routine and familiar approaches")
                    recommendations.append("Practice embracing new ideas and methods")
                elif dim_key == 'conscientiousness':
                    development_areas.append("May benefit from better organization systems")
                    recommendations.append("Develop time management and planning skills")
                elif dim_key == 'extraversion':
                    strengths.append("Thoughtful and independent worker")
                    recommendations.append("Leverage deep thinking in analytical roles")
                elif dim_key == 'agreeableness':
                    development_areas.append("May need to work on collaboration skills")
                    recommendations.append("Practice active listening and empathy")
                elif dim_key == 'neuroticism':
                    strengths.append("Emotionally stable and calm under pressure")
                    recommendations.append("Take on high-pressure leadership roles")
            else:
                level = "Moderate"
            
            profile_descriptors.append(f"{level} {dim_name}")
        
        # Generate overall profile type
        profile_type = " | ".join(profile_descriptors)
        
        return profile_type, strengths, development_areas, recommendations
    
    def _interpret_disc_profile(
        self, 
        dimension_scores: Dict[str, float], 
        percentile_scores: Dict[str, float]
    ) -> Tuple[str, List[str], List[str], List[str]]:
        """
        Interpret DISC behavioral profile.
        """
        strengths = []
        development_areas = []
        recommendations = []
        
        # Find dominant DISC style
        disc_dimensions = ['dominance', 'influence', 'steadiness', 'conscientiousness']
        dominant_style = max(disc_dimensions, key=lambda d: dimension_scores.get(d, 0))
        
        # Generate profile based on dominant style
        if dominant_style == 'dominance':
            profile_type = "Dominant (D) Style"
            strengths.extend([
                "Results-oriented and decisive",
                "Takes charge in challenging situations",
                "Direct communication style"
            ])
            development_areas.extend([
                "May need to improve patience with others",
                "Could benefit from more collaborative approach"
            ])
            recommendations.extend([
                "Seek leadership roles with clear authority",
                "Practice active listening and empathy",
                "Focus on team building skills"
            ])
        
        elif dominant_style == 'influence':
            profile_type = "Influential (I) Style"
            strengths.extend([
                "Enthusiastic and persuasive",
                "Excellent interpersonal skills",
                "Optimistic and inspiring"
            ])
            development_areas.extend([
                "May need to focus more on details",
                "Could improve follow-through on tasks"
            ])
            recommendations.extend([
                "Excel in sales and marketing roles",
                "Develop project management skills",
                "Practice systematic approach to tasks"
            ])
        
        elif dominant_style == 'steadiness':
            profile_type = "Steady (S) Style"
            strengths.extend([
                "Reliable and supportive team member",
                "Patient and good listener",
                "Consistent performance"
            ])
            development_areas.extend([
                "May resist change and new approaches",
                "Could be more assertive when needed"
            ])
            recommendations.extend([
                "Thrive in stable, supportive environments",
                "Practice adapting to change",
                "Develop confidence in expressing opinions"
            ])
        
        else:  # conscientiousness
            profile_type = "Conscientious (C) Style"
            strengths.extend([
                "Detail-oriented and analytical",
                "High quality standards",
                "Systematic and thorough"
            ])
            development_areas.extend([
                "May be overly critical or perfectionist",
                "Could benefit from faster decision-making"
            ])
            recommendations.extend([
                "Excel in analytical and quality-focused roles",
                "Practice making decisions with incomplete information",
                "Balance perfectionism with efficiency"
            ])
        
        return profile_type, strengths, development_areas, recommendations
    
    def _interpret_career_anchors_profile(
        self, 
        dimension_scores: Dict[str, float], 
        percentile_scores: Dict[str, float]
    ) -> Tuple[str, List[str], List[str], List[str]]:
        """
        Interpret Career Anchors profile.
        """
        strengths = []
        development_areas = []
        recommendations = []
        
        # Find top career anchors
        anchor_scores = [(anchor, score) for anchor, score in dimension_scores.items()]
        anchor_scores.sort(key=lambda x: x[1], reverse=True)
        
        top_anchors = anchor_scores[:2]  # Top 2 anchors
        
        profile_type = f"Primary: {top_anchors[0][0].title()}"
        if len(top_anchors) > 1:
            profile_type += f" | Secondary: {top_anchors[1][0].title()}"
        
        # Generate recommendations based on top anchors
        for anchor, score in top_anchors:
            if anchor == 'technical_functional':
                strengths.append("Strong technical expertise and competence")
                recommendations.append("Pursue roles that leverage your technical skills")
                recommendations.append("Consider becoming a subject matter expert")
            
            elif anchor == 'general_managerial':
                strengths.append("Leadership and management potential")
                recommendations.append("Seek management and leadership opportunities")
                recommendations.append("Develop strategic thinking skills")
            
            elif anchor == 'autonomy_independence':
                strengths.append("Self-directed and independent")
                recommendations.append("Look for roles with high autonomy")
                recommendations.append("Consider entrepreneurial opportunities")
            
            elif anchor == 'security_stability':
                strengths.append("Values stability and long-term planning")
                recommendations.append("Seek stable organizations with clear career paths")
                development_areas.append("May need to embrace more change and risk")
            
            elif anchor == 'entrepreneurial_creativity':
                strengths.append("Innovative and entrepreneurial mindset")
                recommendations.append("Consider startup environments or innovation roles")
                recommendations.append("Develop business and financial skills")
        
        return profile_type, strengths, development_areas, recommendations
    
    def _interpret_generic_profile(
        self, 
        dimension_scores: Dict[str, float], 
        percentile_scores: Dict[str, float]
    ) -> Tuple[str, List[str], List[str], List[str]]:
        """
        Generic profile interpretation for custom assessments.
        """
        strengths = []
        development_areas = []
        recommendations = []
        
        # Find highest and lowest scoring dimensions
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_dimensions:
            # Top dimension becomes strength
            top_dim, top_score = sorted_dimensions[0]
            strengths.append(f"Strong in {top_dim.replace('_', ' ').title()}")
            
            # Bottom dimension becomes development area
            if len(sorted_dimensions) > 1:
                bottom_dim, bottom_score = sorted_dimensions[-1]
                development_areas.append(f"Opportunity to develop {bottom_dim.replace('_', ' ').title()}")
                recommendations.append(f"Focus on improving {bottom_dim.replace('_', ' ').lower()} skills")
        
        profile_type = "Custom Assessment Profile"
        
        return profile_type, strengths, development_areas, recommendations


class NormativeDataManager:
    """
    Manages normative data for percentile calculations.
    """
    
    @staticmethod
    def get_industry_norms(framework: str, industry: str = None) -> Dict[str, Dict[str, float]]:
        """
        Get industry-specific normative data.
        """
        # This would typically load from a database or external file
        # For now, return sample normative data
        
        if framework == 'BIG_FIVE':
            return {
                'openness': {'mean': 4.2, 'std': 1.3},
                'conscientiousness': {'mean': 4.5, 'std': 1.2},
                'extraversion': {'mean': 3.8, 'std': 1.4},
                'agreeableness': {'mean': 4.1, 'std': 1.1},
                'neuroticism': {'mean': 3.2, 'std': 1.3}
            }
        elif framework == 'DISC':
            return {
                'dominance': {'mean': 3.5, 'std': 1.2},
                'influence': {'mean': 3.7, 'std': 1.3},
                'steadiness': {'mean': 4.0, 'std': 1.1},
                'conscientiousness': {'mean': 3.9, 'std': 1.2}
            }
        
        return {}
    
    @staticmethod
    def calculate_reliability_coefficient(assessment_framework: str) -> float:
        """
        Get reliability coefficient for the assessment framework.
        """
        # These would be based on psychometric validation studies
        reliability_coefficients = {
            'BIG_FIVE': 0.85,  # Cronbach's alpha
            'DISC': 0.82,
            'CAREER_ANCHORS': 0.78,
            'OCEAN': 0.85,
            'CUSTOM': 0.75
        }
        
        return reliability_coefficients.get(assessment_framework, 0.75)


class AssessmentValidator:
    """
    Validates assessment responses and data quality.
    """
    
    def __init__(self, assessment_instance: AssessmentInstance):
        self.instance = assessment_instance
        self.responses = assessment_instance.responses.select_related('question')
    
    def validate_completion(self) -> Dict[str, Any]:
        """
        Validate that assessment is properly completed.
        """
        total_questions = self.instance.assessment.questions.filter(is_active=True).count()
        answered_questions = self.responses.count()
        required_questions = self.instance.assessment.questions.filter(
            is_active=True, 
            required=True
        ).count()
        answered_required = self.responses.filter(question__required=True).count()
        
        return {
            'is_complete': answered_questions >= total_questions,
            'completion_rate': (answered_questions / total_questions * 100) if total_questions > 0 else 0,
            'required_complete': answered_required >= required_questions,
            'missing_required': required_questions - answered_required,
            'total_questions': total_questions,
            'answered_questions': answered_questions
        }
    
    def detect_response_patterns(self) -> Dict[str, Any]:
        """
        Detect potentially problematic response patterns.
        """
        numeric_responses = [
            self._get_numeric_value(r) for r in self.responses 
            if self._get_numeric_value(r) is not None
        ]
        
        if not numeric_responses:
            return {'valid': True, 'warnings': []}
        
        warnings = []
        
        # Check for straight-lining (all same responses)
        if len(set(numeric_responses)) == 1:
            warnings.append("All responses are identical - may indicate disengagement")
        
        # Check for extreme response bias (only using endpoints)
        min_val, max_val = min(numeric_responses), max(numeric_responses)
        extreme_responses = sum(1 for r in numeric_responses if r in [min_val, max_val])
        extreme_rate = extreme_responses / len(numeric_responses)
        
        if extreme_rate > 0.8:
            warnings.append("High use of extreme responses - may indicate response bias")
        
        # Check for central tendency bias (only using middle values)
        if self._is_seven_point_scale():
            middle_values = [3, 4, 5]
        else:
            middle_values = [2, 3, 4]
        
        middle_responses = sum(1 for r in numeric_responses if r in middle_values)
        middle_rate = middle_responses / len(numeric_responses)
        
        if middle_rate > 0.9:
            warnings.append("High use of middle responses - may indicate uncertainty or social desirability")
        
        # Check response time (if available)
        # This would require storing response timestamps
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'extreme_response_rate': extreme_rate,
            'middle_response_rate': middle_rate,
            'response_variance': statistics.variance(numeric_responses) if len(numeric_responses) > 1 else 0
        }
    
    def _get_numeric_value(self, response: Response) -> Optional[float]:
        """Get numeric value from response."""
        if response.numeric_value is not None:
            return float(response.numeric_value)
        elif response.selected_option:
            return float(response.selected_option.value)
        return None
    
    def _is_seven_point_scale(self) -> bool:
        """Check if assessment uses 7-point scales."""
        return self.instance.assessment.questions.filter(
            question_type='LIKERT_7'
        ).exists()


class ScoreInterpreter:
    """
    Provides detailed score interpretations and recommendations.
    """
    
    @staticmethod
    def get_dimension_interpretation(
        dimension: str, 
        score: float, 
        percentile: float, 
        framework: str
    ) -> Dict[str, str]:
        """
        Get detailed interpretation for a specific dimension score.
        """
        if framework == 'BIG_FIVE':
            return ScoreInterpreter._interpret_big_five_dimension(dimension, score, percentile)
        elif framework == 'DISC':
            return ScoreInterpreter._interpret_disc_dimension(dimension, score, percentile)
        
        return {
            'level': 'Moderate',
            'description': f'Your score in {dimension} is within the average range.',
            'implications': 'This suggests a balanced approach in this area.',
            'development_tips': f'Continue to develop your {dimension} skills through practice and feedback.'
        }
    
    @staticmethod
    def _interpret_big_five_dimension(dimension: str, score: float, percentile: float) -> Dict[str, str]:
        """
        Interpret Big Five dimension scores.
        """
        interpretations = {
            'openness': {
                'high': {
                    'level': 'High Openness',
                    'description': 'You are very open to new experiences, creative, and intellectually curious.',
                    'implications': 'You likely enjoy variety, innovation, and abstract thinking.',
                    'development_tips': 'Channel your creativity into innovative projects and seek diverse experiences.'
                },
                'low': {
                    'level': 'Low Openness',
                    'description': 'You prefer familiar routines and practical approaches.',
                    'implications': 'You value tradition, stability, and concrete thinking.',
                    'development_tips': 'Try to gradually expose yourself to new ideas and experiences.'
                },
                'moderate': {
                    'level': 'Moderate Openness',
                    'description': 'You balance openness to new experiences with appreciation for tradition.',
                    'implications': 'You can adapt to change while maintaining stability.',
                    'development_tips': 'Continue to explore new ideas while leveraging your practical nature.'
                }
            },
            'conscientiousness': {
                'high': {
                    'level': 'High Conscientiousness',
                    'description': 'You are highly organized, disciplined, and goal-oriented.',
                    'implications': 'You excel at planning, following through, and maintaining high standards.',
                    'development_tips': 'Use your organizational skills to lead projects and mentor others.'
                },
                'low': {
                    'level': 'Low Conscientiousness',
                    'description': 'You tend to be more flexible and spontaneous in your approach.',
                    'implications': 'You may prefer adaptable environments and creative freedom.',
                    'development_tips': 'Develop planning and organizational systems to improve efficiency.'
                },
                'moderate': {
                    'level': 'Moderate Conscientiousness',
                    'description': 'You balance organization with flexibility.',
                    'implications': 'You can be both structured and adaptable as situations require.',
                    'development_tips': 'Continue to refine your balance between planning and spontaneity.'
                }
            }
            # Add more dimensions as needed
        }
        
        if percentile >= 70:
            level_key = 'high'
        elif percentile <= 30:
            level_key = 'low'
        else:
            level_key = 'moderate'
        
        return interpretations.get(dimension, {}).get(level_key, {
            'level': 'Moderate',
            'description': f'Your {dimension} score is in the average range.',
            'implications': 'This suggests a balanced approach.',
            'development_tips': f'Continue developing your {dimension} skills.'
        })
    
    @staticmethod
    def _interpret_disc_dimension(dimension: str, score: float, percentile: float) -> Dict[str, str]:
        """
        Interpret DISC dimension scores.
        """
        # Similar structure for DISC interpretations
        # Implementation would follow the same pattern as Big Five
        return {
            'level': f'{"High" if percentile >= 70 else "Low" if percentile <= 30 else "Moderate"} {dimension.title()}',
            'description': f'Your {dimension} score indicates specific behavioral tendencies.',
            'implications': 'This affects how you interact with others and approach tasks.',
            'development_tips': f'Leverage your {dimension} style while developing complementary skills.'
        }


def calculate_assessment_scores(assessment_instance_id: str) -> ScoreProfile:
    """
    Main function to calculate all scores for an assessment instance.
    
    Args:
        assessment_instance_id: UUID of the assessment instance
        
    Returns:
        ScoreProfile with calculated scores and interpretations
    """
    try:
        instance = AssessmentInstance.objects.get(id=assessment_instance_id)
        
        # Validate completion
        validator = AssessmentValidator(instance)
        validation_result = validator.validate_completion()
        
        if not validation_result['is_complete']:
            raise ValueError(f"Assessment is not complete: {validation_result}")
        
        # Check for response patterns
        pattern_analysis = validator.detect_response_patterns()
        
        # Calculate scores
        scorer = AssessmentScorer(instance)
        score_profile = scorer.calculate_all_scores()
        
        # Add validation metadata
        score_profile.data = score_profile.data or {}
        score_profile.data.update({
            'validation': validation_result,
            'pattern_analysis': pattern_analysis,
            'reliability_coefficient': NormativeDataManager.calculate_reliability_coefficient(
                instance.assessment.framework
            )
        })
        score_profile.save()
        
        return score_profile
        
    except AssessmentInstance.DoesNotExist:
        raise ValueError(f"Assessment instance {assessment_instance_id} not found")


def get_detailed_score_interpretation(score_profile: ScoreProfile) -> Dict[str, Any]:
    """
    Get detailed interpretation for all dimensions in a score profile.
    
    Args:
        score_profile: ScoreProfile instance
        
    Returns:
        Dictionary with detailed interpretations for each dimension
    """
    interpretations = {}
    framework = score_profile.instance.assessment.framework
    
    for dimension, score in score_profile.dimension_scores.items():
        percentile = score_profile.percentile_scores.get(dimension, 50)
        
        interpretations[dimension] = ScoreInterpreter.get_dimension_interpretation(
            dimension, score, percentile, framework
        )
        
        # Add norm scores if available
        if dimension in score_profile.norm_scores:
            interpretations[dimension]['norm_scores'] = score_profile.norm_scores[dimension]
    
    return interpretations


def compare_profiles(profile1: ScoreProfile, profile2: ScoreProfile) -> Dict[str, Any]:
    """
    Compare two score profiles and highlight differences.
    
    Args:
        profile1: First score profile
        profile2: Second score profile
        
    Returns:
        Dictionary with comparison results
    """
    if profile1.instance.assessment.framework != profile2.instance.assessment.framework:
        raise ValueError("Cannot compare profiles from different assessment frameworks")
    
    comparison = {
        'framework': profile1.instance.assessment.framework,
        'dimension_differences': {},
        'similarity_score': 0.0,
        'key_differences': []
    }
    
    # Compare dimension scores
    total_diff = 0.0
    dimension_count = 0
    
    for dimension in profile1.dimension_scores:
        if dimension in profile2.dimension_scores:
            score1 = profile1.dimension_scores[dimension]
            score2 = profile2.dimension_scores[dimension]
            diff = abs(score1 - score2)
            
            comparison['dimension_differences'][dimension] = {
                'profile1_score': score1,
                'profile2_score': score2,
                'difference': diff,
                'significant': diff > 1.0  # Threshold for significant difference
            }
            
            total_diff += diff
            dimension_count += 1
            
            # Note significant differences
            if diff > 1.5:
                comparison['key_differences'].append(
                    f"Significant difference in {dimension}: {score1:.1f} vs {score2:.1f}"
                )
    
    # Calculate overall similarity
    if dimension_count > 0:
        avg_diff = total_diff / dimension_count
        comparison['similarity_score'] = max(0, 100 - (avg_diff * 20))  # Convert to 0-100 scale
    
    return comparison