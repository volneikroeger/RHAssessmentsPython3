import React, { useState, useEffect } from 'react';
import { TrendingUp, Award, Target, FileText, Loader } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { calculateAssessmentScores, ScoreInterpreter } from '../../services/assessmentScoring';
import type { ScoreProfile, AssessmentInstance } from '../../types/assessments';

interface AssessmentResultsProps {
  instanceId: string;
}

export function AssessmentResults({ instanceId }: AssessmentResultsProps) {
  const [instance, setInstance] = useState<AssessmentInstance | null>(null);
  const [profile, setProfile] = useState<ScoreProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedDimension, setExpandedDimension] = useState<string | null>(null);

  useEffect(() => {
    loadResults();
  }, [instanceId]);

  async function loadResults() {
    try {
      const { data: instanceData, error: instanceError } = await supabase
        .from('assessment_instances')
        .select('*, assessment:assessment_definitions(*)')
        .eq('id', instanceId)
        .single();

      if (instanceError) throw instanceError;
      setInstance(instanceData as any);

      const { data: profileData, error: profileError } = await supabase
        .from('score_profiles')
        .select('*')
        .eq('instance_id', instanceId)
        .maybeSingle();

      if (profileError && profileError.code !== 'PGRST116') throw profileError;

      if (!profileData) {
        setCalculating(true);
        try {
          const calculatedProfile = await calculateAssessmentScores(instanceId);
          setProfile(calculatedProfile);
        } catch (calcError: any) {
          setError(`Error calculating scores: ${calcError.message}`);
        } finally {
          setCalculating(false);
        }
      } else {
        setProfile(profileData as ScoreProfile);
      }

      setLoading(false);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  }

  if (loading || calculating) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">
            {calculating ? 'Calculating your scores...' : 'Loading results...'}
          </p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 font-semibold">Error loading results</p>
          <p className="text-gray-600 mt-2">{error || 'No results found'}</p>
        </div>
      </div>
    );
  }

  const dimensionEntries = Object.entries(profile.dimension_scores);
  const framework = (instance as any)?.assessment?.framework || 'CUSTOM';

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Assessment Results</h1>
              <p className="text-gray-600 mt-1">
                {(instance as any)?.assessment?.name || 'Assessment'}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Completed</p>
              <p className="text-sm text-gray-700">
                {new Date(instance?.completed_at || '').toLocaleDateString()}
              </p>
            </div>
          </div>

          {profile.profile_type && (
            <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
              <h2 className="text-lg font-semibold text-blue-900 mb-1">Profile Type</h2>
              <p className="text-blue-800">{profile.profile_type}</p>
            </div>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <Award className="h-6 w-6 text-green-600" />
              <h2 className="text-xl font-bold text-gray-900">Strengths</h2>
            </div>
            <ul className="space-y-2">
              {profile.strengths.length > 0 ? (
                profile.strengths.map((strength, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-green-600 mt-1">✓</span>
                    <span className="text-gray-700">{strength}</span>
                  </li>
                ))
              ) : (
                <li className="text-gray-500 italic">No specific strengths identified</li>
              )}
            </ul>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <Target className="h-6 w-6 text-orange-600" />
              <h2 className="text-xl font-bold text-gray-900">Development Areas</h2>
            </div>
            <ul className="space-y-2">
              {profile.development_areas.length > 0 ? (
                profile.development_areas.map((area, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-orange-600 mt-1">→</span>
                    <span className="text-gray-700">{area}</span>
                  </li>
                ))
              ) : (
                <li className="text-gray-500 italic">No specific development areas identified</li>
              )}
            </ul>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-bold text-gray-900">Recommendations</h2>
          </div>
          <ul className="space-y-3">
            {profile.recommendations.length > 0 ? (
              profile.recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                    {index + 1}
                  </span>
                  <span className="text-gray-700">{rec}</span>
                </li>
              ))
            ) : (
              <li className="text-gray-500 italic">No specific recommendations available</li>
            )}
          </ul>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center gap-3 mb-6">
            <FileText className="h-6 w-6 text-purple-600" />
            <h2 className="text-xl font-bold text-gray-900">Dimension Scores</h2>
          </div>

          <div className="space-y-4">
            {dimensionEntries.map(([dimension, score]) => {
              const percentile = profile.percentile_scores[dimension] || 50;
              const normScore = profile.norm_scores[dimension];
              const isExpanded = expandedDimension === dimension;

              return (
                <div key={dimension} className="border rounded-lg p-4">
                  <div
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => setExpandedDimension(isExpanded ? null : dimension)}
                  >
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 capitalize">
                        {dimension.replace(/_/g, ' ')}
                      </h3>
                      <div className="flex items-center gap-4 mt-2">
                        <div className="flex-1">
                          <div className="flex justify-between text-sm text-gray-600 mb-1">
                            <span>Score: {score.toFixed(2)}</span>
                            <span>Percentile: {percentile.toFixed(0)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                percentile >= 75
                                  ? 'bg-green-500'
                                  : percentile >= 50
                                  ? 'bg-blue-500'
                                  : percentile >= 25
                                  ? 'bg-yellow-500'
                                  : 'bg-orange-500'
                              }`}
                              style={{ width: `${percentile}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                    <button className="ml-4 text-gray-400 hover:text-gray-600">
                      {isExpanded ? '−' : '+'}
                    </button>
                  </div>

                  {isExpanded && normScore && (
                    <div className="mt-4 pt-4 border-t">
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div className="text-center">
                          <p className="text-xs text-gray-500">Z-Score</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {normScore.z_score.toFixed(2)}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-xs text-gray-500">T-Score</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {normScore.t_score.toFixed(1)}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-xs text-gray-500">Sten Score</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {normScore.sten_score.toFixed(1)}
                          </p>
                        </div>
                      </div>
                      <DimensionInterpretation
                        dimension={dimension}
                        score={score}
                        percentile={percentile}
                        framework={framework}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {profile.validation_data && profile.validation_data.warnings.length > 0 && (
          <div className="bg-yellow-50 border-l-4 border-yellow-600 p-4 mt-6">
            <h3 className="text-sm font-semibold text-yellow-900 mb-2">Data Quality Notes</h3>
            <ul className="text-sm text-yellow-800 space-y-1">
              {profile.validation_data.warnings.map((warning, index) => (
                <li key={index}>• {warning}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function DimensionInterpretation({
  dimension,
  score,
  percentile,
  framework
}: {
  dimension: string;
  score: number;
  percentile: number;
  framework: string;
}) {
  const interpretation = ScoreInterpreter.getDimensionInterpretation(
    dimension,
    score,
    percentile,
    framework as any
  );

  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-3">
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase">Level</p>
        <p className="text-sm text-gray-900">{interpretation.level}</p>
      </div>
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase">Description</p>
        <p className="text-sm text-gray-700">{interpretation.description}</p>
      </div>
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase">Implications</p>
        <p className="text-sm text-gray-700">{interpretation.implications}</p>
      </div>
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase">Development Tips</p>
        <p className="text-sm text-gray-700">{interpretation.development_tips}</p>
      </div>
    </div>
  );
}
