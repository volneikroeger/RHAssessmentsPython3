import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, CheckCircle, AlertCircle } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import type { AssessmentInstance, Question, QuestionOption, Response } from '../../types/assessments';

interface AssessmentTakingProps {
  token: string;
  onComplete: () => void;
}

export function AssessmentTaking({ token, onComplete }: AssessmentTakingProps) {
  const [instance, setInstance] = useState<AssessmentInstance | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [questionOptions, setQuestionOptions] = useState<Map<string, QuestionOption[]>>(new Map());
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Map<string, any>>(new Map());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAssessment();
  }, [token]);

  async function loadAssessment() {
    try {
      const { data: instanceData, error: instanceError } = await supabase
        .from('assessment_instances')
        .select('*, assessment:assessment_definitions(*)')
        .eq('token', token)
        .single();

      if (instanceError) throw instanceError;
      if (!instanceData) throw new Error('Assessment not found');

      setInstance(instanceData as any);

      const { data: questionsData, error: questionsError } = await supabase
        .from('questions')
        .select('*')
        .eq('assessment_id', instanceData.assessment_id)
        .eq('is_active', true)
        .order('order_number');

      if (questionsError) throw questionsError;
      setQuestions(questionsData as Question[]);

      const { data: optionsData, error: optionsError } = await supabase
        .from('question_options')
        .select('*')
        .in('question_id', questionsData.map((q: Question) => q.id))
        .order('order_number');

      if (optionsError) throw optionsError;

      const optionsMap = new Map<string, QuestionOption[]>();
      (optionsData as QuestionOption[]).forEach(option => {
        if (!optionsMap.has(option.question_id)) {
          optionsMap.set(option.question_id, []);
        }
        optionsMap.get(option.question_id)!.push(option);
      });
      setQuestionOptions(optionsMap);

      const { data: existingResponses } = await supabase
        .from('responses')
        .select('*')
        .eq('instance_id', instanceData.id);

      const responsesMap = new Map<string, any>();
      (existingResponses || []).forEach((r: Response) => {
        responsesMap.set(r.question_id, {
          numeric_value: r.numeric_value,
          text_value: r.text_value,
          selected_option_id: r.selected_option_id
        });
      });
      setResponses(responsesMap);

      if (instanceData.status === 'INVITED') {
        await supabase
          .from('assessment_instances')
          .update({ status: 'STARTED', started_at: new Date().toISOString() })
          .eq('id', instanceData.id);
      }

      setLoading(false);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  }

  async function saveResponse(questionId: string, responseData: any) {
    if (!instance) return;

    setSaving(true);
    try {
      const { error } = await supabase
        .from('responses')
        .upsert({
          instance_id: instance.id,
          question_id: questionId,
          ...responseData
        });

      if (error) throw error;

      setResponses(new Map(responses).set(questionId, responseData));

      const progress = ((responses.size + 1) / questions.length) * 100;
      await supabase
        .from('assessment_instances')
        .update({
          status: 'IN_PROGRESS',
          progress_percentage: progress,
          current_question: currentQuestionIndex
        })
        .eq('id', instance.id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleComplete() {
    if (!instance) return;

    try {
      await supabase
        .from('assessment_instances')
        .update({
          status: 'COMPLETED',
          completed_at: new Date().toISOString(),
          progress_percentage: 100
        })
        .eq('id', instance.id);

      onComplete();
    } catch (err: any) {
      setError(err.message);
    }
  }

  function handleNext() {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      handleComplete();
    }
  }

  function handlePrevious() {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  }

  function handleLikertResponse(questionId: string, value: number) {
    saveResponse(questionId, { numeric_value: value });
  }

  function handleOptionResponse(questionId: string, optionId: string) {
    saveResponse(questionId, { selected_option_id: optionId });
  }

  function handleTextResponse(questionId: string, text: string) {
    saveResponse(questionId, { text_value: text });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <p className="text-red-600 font-semibold">Error loading assessment</p>
          <p className="text-gray-600 mt-2">{error}</p>
        </div>
      </div>
    );
  }

  if (!instance || questions.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
          <p className="text-gray-700 font-semibold">No questions found</p>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const currentResponse = responses.get(currentQuestion.id);
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <h1 className="text-2xl font-bold text-gray-900">
                {(instance as any).assessment?.name || 'Assessment'}
              </h1>
              <span className="text-sm text-gray-600">
                Question {currentQuestionIndex + 1} of {questions.length}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <div className="mb-8">
            <p className="text-lg text-gray-800 mb-6">{currentQuestion.text}</p>

            {currentQuestion.question_type === 'LIKERT_5' && (
              <LikertScale
                max={5}
                value={currentResponse?.numeric_value}
                onChange={(value) => handleLikertResponse(currentQuestion.id, value)}
              />
            )}

            {currentQuestion.question_type === 'LIKERT_7' && (
              <LikertScale
                max={7}
                value={currentResponse?.numeric_value}
                onChange={(value) => handleLikertResponse(currentQuestion.id, value)}
              />
            )}

            {(currentQuestion.question_type === 'MULTIPLE_CHOICE' ||
              currentQuestion.question_type === 'FORCED_CHOICE') && (
              <MultipleChoice
                options={questionOptions.get(currentQuestion.id) || []}
                selectedId={currentResponse?.selected_option_id}
                onChange={(optionId) => handleOptionResponse(currentQuestion.id, optionId)}
              />
            )}

            {currentQuestion.question_type === 'TEXT' && (
              <TextResponse
                value={currentResponse?.text_value || ''}
                onChange={(text) => handleTextResponse(currentQuestion.id, text)}
              />
            )}
          </div>

          <div className="flex justify-between items-center pt-6 border-t">
            <button
              onClick={handlePrevious}
              disabled={currentQuestionIndex === 0}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-5 w-5" />
              Previous
            </button>

            {saving && (
              <span className="text-sm text-gray-600">Saving...</span>
            )}

            <button
              onClick={handleNext}
              disabled={currentQuestion.required && !currentResponse}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {currentQuestionIndex === questions.length - 1 ? (
                <>
                  <CheckCircle className="h-5 w-5" />
                  Complete
                </>
              ) : (
                <>
                  Next
                  <ChevronRight className="h-5 w-5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function LikertScale({ max, value, onChange }: { max: number; value?: number; onChange: (value: number) => void }) {
  const labels = max === 5
    ? ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']
    : ['Strongly Disagree', 'Disagree', 'Somewhat Disagree', 'Neutral', 'Somewhat Agree', 'Agree', 'Strongly Agree'];

  return (
    <div className="space-y-4">
      <div className="flex justify-between gap-2">
        {Array.from({ length: max }, (_, i) => i + 1).map((num) => (
          <button
            key={num}
            onClick={() => onChange(num)}
            className={`flex-1 py-3 px-2 rounded-lg border-2 transition-all ${
              value === num
                ? 'border-blue-600 bg-blue-50 text-blue-700 font-semibold'
                : 'border-gray-300 hover:border-blue-400 text-gray-700'
            }`}
          >
            {num}
          </button>
        ))}
      </div>
      <div className="flex justify-between text-xs text-gray-600 px-2">
        <span>{labels[0]}</span>
        <span>{labels[Math.floor(max / 2)]}</span>
        <span>{labels[max - 1]}</span>
      </div>
    </div>
  );
}

function MultipleChoice({
  options,
  selectedId,
  onChange
}: {
  options: QuestionOption[];
  selectedId?: string;
  onChange: (optionId: string) => void;
}) {
  return (
    <div className="space-y-3">
      {options.map((option) => (
        <button
          key={option.id}
          onClick={() => onChange(option.id)}
          className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
            selectedId === option.id
              ? 'border-blue-600 bg-blue-50 text-blue-700 font-semibold'
              : 'border-gray-300 hover:border-blue-400 text-gray-700'
          }`}
        >
          {option.text}
        </button>
      ))}
    </div>
  );
}

function TextResponse({ value, onChange }: { value: string; onChange: (text: string) => void }) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
      rows={6}
      placeholder="Enter your response..."
    />
  );
}
