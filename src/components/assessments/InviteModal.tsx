import React, { useState } from 'react';
import { X, Mail, Copy, Check, Link as LinkIcon } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import type { AssessmentDefinition } from '../../types/assessments';

interface InviteModalProps {
  assessment: AssessmentDefinition;
  onClose: () => void;
  onSuccess: () => void;
}

export function InviteModal({ assessment, onClose, onSuccess }: InviteModalProps) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedLink, setGeneratedLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function generateToken(): Promise<string> {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  async function handleGenerateLink() {
    setLoading(true);
    setError(null);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { data: profile } = await supabase
        .from('profiles')
        .select('organization_id')
        .eq('id', user.id)
        .single();

      if (!profile?.organization_id) throw new Error('No organization found');

      const token = await generateToken();

      let userId = user.id;

      if (email) {
        const { data: existingUser } = await supabase
          .from('profiles')
          .select('id')
          .eq('email', email)
          .maybeSingle();

        if (existingUser) {
          userId = existingUser.id;
        } else {
          const { data: newUser, error: userError } = await supabase.auth.admin.createUser({
            email,
            email_confirm: true,
          });

          if (userError) {
            const tempEmail = `temp_${token.substring(0, 8)}@temp.assessment`;
            userId = user.id;
          }
        }
      }

      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + 7);

      const { error: insertError } = await supabase
        .from('assessment_instances')
        .insert({
          organization_id: profile.organization_id,
          assessment_id: assessment.id,
          user_id: userId,
          token,
          invited_by: user.id,
          status: 'INVITED',
          expires_at: expiresAt.toISOString(),
        });

      if (insertError) throw insertError;

      const link = `${window.location.origin}/assessments/take/${token}`;
      setGeneratedLink(link);
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to generate link');
    } finally {
      setLoading(false);
    }
  }

  async function handleCopyLink() {
    if (!generatedLink) return;

    try {
      await navigator.clipboard.writeText(generatedLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      setError('Failed to copy link');
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h2 className="text-xl font-bold text-slate-900">Invite to Assessment</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <h3 className="font-semibold text-slate-900 mb-1">{assessment.name}</h3>
            <p className="text-sm text-slate-600">{assessment.description}</p>
            <p className="text-sm text-slate-500 mt-1">
              Estimated duration: {assessment.estimated_duration} minutes
            </p>
          </div>

          {!generatedLink ? (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Recipient Email (optional)
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Leave empty to generate a shareable link without email
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Recipient Name (optional)
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Custom Message (optional)
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Add a personal message..."
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}
            </>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 text-green-800">
                <Check className="h-5 w-5" />
                <span className="font-medium">Assessment link generated!</span>
              </div>

              <div className="bg-white border border-green-200 rounded-lg p-3">
                <p className="text-sm text-slate-600 mb-2">Share this link:</p>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={generatedLink}
                    readOnly
                    className="flex-1 px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded"
                  />
                  <button
                    onClick={handleCopyLink}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    {copied ? (
                      <>
                        <Check className="h-4 w-4" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
              </div>

              <p className="text-xs text-slate-600">
                This link will expire in 7 days. Anyone with this link can take the assessment.
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-200">
          {!generatedLink ? (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 text-slate-700 hover:text-slate-900"
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateLink}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                    Generating...
                  </>
                ) : (
                  <>
                    <LinkIcon className="h-4 w-4" />
                    Generate Link
                  </>
                )}
              </button>
            </>
          ) : (
            <button
              onClick={onClose}
              className="px-6 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
