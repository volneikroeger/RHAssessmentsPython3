import React, { useState, useEffect } from 'react';
import { ClipboardCheck, Eye, Send, Plus, Edit, Trash2 } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import type { AssessmentDefinition, AssessmentInstance } from '../../types/assessments';
import { InviteModal } from './InviteModal';
import { CreateAssessmentModal } from './CreateAssessmentModal';

export function AssessmentList() {
  const [definitions, setDefinitions] = useState<AssessmentDefinition[]>([]);
  const [instances, setInstances] = useState<AssessmentInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'definitions' | 'instances'>('definitions');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const { data: user } = await supabase.auth.getUser();
      if (!user.user) return;

      const { data: defData } = await supabase
        .from('assessment_definitions')
        .select('*')
        .order('created_at', { ascending: false });

      setDefinitions((defData as AssessmentDefinition[]) || []);

      const { data: instData } = await supabase
        .from('assessment_instances')
        .select('*, assessment:assessment_definitions(name)')
        .eq('user_id', user.user.id)
        .order('invited_at', { ascending: false });

      setInstances((instData as any[]) || []);
      setLoading(false);
    } catch (error) {
      console.error('Error loading assessments:', error);
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      {showCreateModal && (
        <CreateAssessmentModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            loadData();
            setShowCreateModal(false);
          }}
        />
      )}

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Assessments</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Create Assessment
        </button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <div className="flex">
            <button
              onClick={() => setActiveTab('definitions')}
              className={`px-6 py-3 font-medium ${
                activeTab === 'definitions'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Assessment Definitions ({definitions.length})
            </button>
            <button
              onClick={() => setActiveTab('instances')}
              className={`px-6 py-3 font-medium ${
                activeTab === 'instances'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              My Assessments ({instances.length})
            </button>
          </div>
        </div>

        <div className="p-6">
          {activeTab === 'definitions' ? (
            <DefinitionsList definitions={definitions} onRefresh={loadData} />
          ) : (
            <InstancesList instances={instances} onRefresh={loadData} />
          )}
        </div>
      </div>
    </div>
  );
}

function DefinitionsList({ definitions, onRefresh }: { definitions: AssessmentDefinition[]; onRefresh: () => void }) {
  const [inviteModalAssessment, setInviteModalAssessment] = useState<AssessmentDefinition | null>(null);
  const [editModalAssessment, setEditModalAssessment] = useState<AssessmentDefinition | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  async function handleDelete(id: string) {
    try {
      const { error } = await supabase
        .from('assessment_definitions')
        .delete()
        .eq('id', id);

      if (error) throw error;
      onRefresh();
    } catch (error) {
      console.error('Error deleting assessment:', error);
      alert('Failed to delete assessment. It may have associated data.');
    } finally {
      setDeleteConfirm(null);
    }
  }

  if (definitions.length === 0) {
    return (
      <div className="text-center py-12">
        <ClipboardCheck className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No assessment definitions found</p>
        <p className="text-gray-500 text-sm mt-2">Create your first assessment to get started</p>
      </div>
    );
  }

  return (
    <>
      {inviteModalAssessment && (
        <InviteModal
          assessment={inviteModalAssessment}
          onClose={() => setInviteModalAssessment(null)}
          onSuccess={() => {
            onRefresh();
          }}
        />
      )}

      {editModalAssessment && (
        <CreateAssessmentModal
          editAssessment={editModalAssessment}
          onClose={() => setEditModalAssessment(null)}
          onSuccess={() => {
            onRefresh();
            setEditModalAssessment(null);
          }}
        />
      )}

      {deleteConfirm && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-2">Delete Assessment?</h3>
            <p className="text-slate-600 mb-6">
              Are you sure you want to delete this assessment? This action cannot be undone and will remove all associated questions.
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-slate-700 hover:text-slate-900"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {definitions.map((def) => (
        <div key={def.id} className="border rounded-lg p-4 hover:border-blue-300 transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h3 className="font-semibold text-gray-900">{def.name}</h3>
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    def.status === 'ACTIVE'
                      ? 'bg-green-100 text-green-800'
                      : def.status === 'DRAFT'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {def.status}
                </span>
              </div>
              {def.description && (
                <p className="text-sm text-gray-600 mt-1">{def.description}</p>
              )}
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <span>{def.framework.replace(/_/g, ' ')}</span>
                <span>•</span>
                <span>{def.estimated_duration} min</span>
                <span>•</span>
                <span>v{def.version}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setInviteModalAssessment(def)}
                className="p-2 text-gray-600 hover:text-blue-600"
                title="Send Assessment"
              >
                <Send className="h-4 w-4" />
              </button>
              <button
                onClick={() => setEditModalAssessment(def)}
                className="p-2 text-gray-600 hover:text-blue-600"
                title="Edit"
              >
                <Edit className="h-4 w-4" />
              </button>
              <button
                onClick={() => setDeleteConfirm(def.id)}
                className="p-2 text-gray-600 hover:text-red-600"
                title="Delete"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ))}
      </div>
    </>
  );
}

function InstancesList({ instances, onRefresh }: { instances: any[]; onRefresh: () => void }) {
  if (instances.length === 0) {
    return (
      <div className="text-center py-12">
        <ClipboardCheck className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No assessments assigned to you</p>
        <p className="text-gray-500 text-sm mt-2">Check back later for new assessments</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {instances.map((instance) => (
        <div key={instance.id} className="border rounded-lg p-4 hover:border-blue-300 transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h3 className="font-semibold text-gray-900">{instance.assessment?.name}</h3>
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    instance.status === 'COMPLETED'
                      ? 'bg-green-100 text-green-800'
                      : instance.status === 'IN_PROGRESS'
                      ? 'bg-blue-100 text-blue-800'
                      : instance.status === 'INVITED'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {instance.status.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <span>Invited: {new Date(instance.invited_at).toLocaleDateString()}</span>
                {instance.completed_at && (
                  <>
                    <span>•</span>
                    <span>Completed: {new Date(instance.completed_at).toLocaleDateString()}</span>
                  </>
                )}
                {instance.progress_percentage > 0 && instance.status !== 'COMPLETED' && (
                  <>
                    <span>•</span>
                    <span>Progress: {instance.progress_percentage.toFixed(0)}%</span>
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {instance.status === 'COMPLETED' ? (
                <button
                  onClick={() => (window.location.href = `/assessments/results/${instance.id}`)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Eye className="h-4 w-4" />
                  View Results
                </button>
              ) : (
                <button
                  onClick={() => (window.location.href = `/assessments/take/${instance.token}`)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {instance.status === 'INVITED' ? 'Start' : 'Continue'}
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
