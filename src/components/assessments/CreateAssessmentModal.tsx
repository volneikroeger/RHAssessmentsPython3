import React, { useState } from 'react';
import { X, Save, Plus } from 'lucide-react';
import { supabase } from '../../lib/supabase';

interface CreateAssessmentModalProps {
  onClose: () => void;
  onSuccess: () => void;
  editAssessment?: any;
}

type Framework = 'BIG_FIVE' | 'DISC' | 'CAREER_ANCHORS' | 'OCEAN' | 'CUSTOM';
type Status = 'DRAFT' | 'ACTIVE' | 'ARCHIVED';

export function CreateAssessmentModal({ onClose, onSuccess, editAssessment }: CreateAssessmentModalProps) {
  const [name, setName] = useState(editAssessment?.name || '');
  const [description, setDescription] = useState(editAssessment?.description || '');
  const [framework, setFramework] = useState<Framework>(editAssessment?.framework || 'DISC');
  const [status, setStatus] = useState<Status>(editAssessment?.status || 'DRAFT');
  const [estimatedDuration, setEstimatedDuration] = useState(editAssessment?.estimated_duration || 15);
  const [instructions, setInstructions] = useState(editAssessment?.instructions || '');
  const [randomizeQuestions, setRandomizeQuestions] = useState(editAssessment?.randomize_questions || false);
  const [allowSkip, setAllowSkip] = useState(editAssessment?.allow_skip || false);
  const [showProgress, setShowProgress] = useState(editAssessment?.show_progress !== false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const frameworks: { value: Framework; label: string }[] = [
    { value: 'DISC', label: 'DISC Personality Assessment' },
    { value: 'BIG_FIVE', label: 'Big Five Personality Traits' },
    { value: 'OCEAN', label: 'OCEAN Model' },
    { value: 'CAREER_ANCHORS', label: 'Career Anchors' },
    { value: 'CUSTOM', label: 'Custom Assessment' },
  ];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { data: membership } = await supabase
        .from('organization_members')
        .select('organization_id, role')
        .eq('user_id', user.id)
        .eq('is_active', true)
        .single();

      if (!membership) throw new Error('No active organization membership found');

      const assessmentData = {
        organization_id: membership.organization_id,
        name,
        description,
        framework,
        status,
        estimated_duration: estimatedDuration,
        instructions,
        randomize_questions: randomizeQuestions,
        allow_skip: allowSkip,
        show_progress: showProgress,
        created_by: user.id,
      };

      if (editAssessment) {
        const { error: updateError } = await supabase
          .from('assessment_definitions')
          .update(assessmentData)
          .eq('id', editAssessment.id);

        if (updateError) throw updateError;
      } else {
        const { error: insertError } = await supabase
          .from('assessment_definitions')
          .insert(assessmentData);

        if (insertError) throw insertError;
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save assessment');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full my-8">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h2 className="text-xl font-bold text-slate-900">
            {editAssessment ? 'Edit Assessment' : 'Create New Assessment'}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Assessment Name *
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Leadership Assessment"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of the assessment purpose..."
                rows={3}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Framework *
              </label>
              <select
                required
                value={framework}
                onChange={(e) => setFramework(e.target.value as Framework)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {frameworks.map((fw) => (
                  <option key={fw.value} value={fw.value}>
                    {fw.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Status *
              </label>
              <select
                required
                value={status}
                onChange={(e) => setStatus(e.target.value as Status)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="DRAFT">Draft</option>
                <option value="ACTIVE">Active</option>
                <option value="ARCHIVED">Archived</option>
              </select>
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Estimated Duration (minutes)
              </label>
              <input
                type="number"
                min="1"
                max="240"
                value={estimatedDuration}
                onChange={(e) => setEstimatedDuration(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Instructions
              </label>
              <textarea
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="Instructions for test-takers..."
                rows={4}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="col-span-2 space-y-3">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Assessment Settings
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={randomizeQuestions}
                  onChange={(e) => setRandomizeQuestions(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700">Randomize question order</span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={allowSkip}
                  onChange={(e) => setAllowSkip(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700">Allow skipping questions</span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showProgress}
                  onChange={(e) => setShowProgress(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700">Show progress bar</span>
              </label>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> After creating the assessment, you'll need to add questions to it before sending it to candidates.
            </p>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-slate-700 hover:text-slate-900"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  {editAssessment ? 'Update Assessment' : 'Create Assessment'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
