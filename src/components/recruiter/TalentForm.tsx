import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext';
import { X, Upload, AlertCircle, CheckCircle } from 'lucide-react';

interface TalentFormProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function TalentForm({ onClose, onSuccess }: TalentFormProps) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [duplicateCheck, setDuplicateCheck] = useState<{ field: string; message: string } | null>(null);

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    location: '',
    job_title: '',
    experience_level: '',
    linkedin_url: '',
    github_url: '',
    portfolio_url: '',
    skills: '',
    salary_expectation: '',
    availability: '',
    work_preference: '',
    notes: '',
  });

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      checkForDuplicates();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [formData.email, formData.linkedin_url]);

  const checkForDuplicates = async () => {
    setDuplicateCheck(null);

    if (formData.email.trim()) {
      const { data } = await supabase
        .from('talents')
        .select('id')
        .eq('email', formData.email.trim())
        .maybeSingle();

      if (data) {
        setDuplicateCheck({
          field: 'email',
          message: 'A talent with this email already exists in your database.',
        });
        return;
      }
    }

    if (formData.linkedin_url.trim()) {
      const { data } = await supabase
        .from('talents')
        .select('id')
        .eq('linkedin_url', formData.linkedin_url.trim())
        .maybeSingle();

      if (data) {
        setDuplicateCheck({
          field: 'linkedin_url',
          message: 'A talent with this LinkedIn URL already exists in your database.',
        });
        return;
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (duplicateCheck) {
      setError('Please resolve duplicate entries before submitting.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      if (!user) throw new Error('User not authenticated');

      const skillsArray = formData.skills
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const { error: insertError } = await supabase.from('talents').insert({
        recruiter_id: user.id,
        full_name: formData.full_name,
        email: formData.email,
        phone: formData.phone || null,
        location: formData.location || null,
        job_title: formData.job_title || null,
        experience_level: formData.experience_level || null,
        linkedin_url: formData.linkedin_url || null,
        github_url: formData.github_url || null,
        portfolio_url: formData.portfolio_url || null,
        skills: skillsArray.length > 0 ? skillsArray : null,
        salary_expectation: formData.salary_expectation || null,
        availability: formData.availability || null,
        work_preference: formData.work_preference || null,
        notes: formData.notes || null,
        status: 'active',
      });

      if (insertError) throw insertError;

      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add talent');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-xl max-w-4xl w-full my-8">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h2 className="text-2xl font-bold text-slate-900">Add New Talent</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {duplicateCheck && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-900">Duplicate Detected</p>
                <p className="text-sm text-amber-700">{duplicateCheck.message}</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-slate-700 mb-2">
                Full Name *
              </label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                required
                value={formData.full_name}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">
                Email *
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent ${
                  duplicateCheck?.field === 'email' ? 'border-amber-300' : 'border-slate-300'
                }`}
                placeholder="john@example.com"
              />
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-slate-700 mb-2">
                Phone
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                placeholder="+1 (555) 123-4567"
              />
            </div>

            <div>
              <label htmlFor="location" className="block text-sm font-medium text-slate-700 mb-2">
                Location
              </label>
              <input
                id="location"
                name="location"
                type="text"
                value={formData.location}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                placeholder="San Francisco, CA"
              />
            </div>

            <div>
              <label htmlFor="job_title" className="block text-sm font-medium text-slate-700 mb-2">
                Job Title
              </label>
              <input
                id="job_title"
                name="job_title"
                type="text"
                value={formData.job_title}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                placeholder="Senior Software Engineer"
              />
            </div>

            <div>
              <label htmlFor="experience_level" className="block text-sm font-medium text-slate-700 mb-2">
                Experience Level
              </label>
              <select
                id="experience_level"
                name="experience_level"
                value={formData.experience_level}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
              >
                <option value="">Select level</option>
                <option value="entry">Entry Level</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
                <option value="executive">Executive</option>
              </select>
            </div>

            <div>
              <label htmlFor="linkedin_url" className="block text-sm font-medium text-slate-700 mb-2">
                LinkedIn URL
              </label>
              <input
                id="linkedin_url"
                name="linkedin_url"
                type="url"
                value={formData.linkedin_url}
                onChange={handleChange}
                className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent ${
                  duplicateCheck?.field === 'linkedin_url' ? 'border-amber-300' : 'border-slate-300'
                }`}
                placeholder="https://linkedin.com/in/johndoe"
              />
            </div>

            <div>
              <label htmlFor="github_url" className="block text-sm font-medium text-slate-700 mb-2">
                GitHub URL
              </label>
              <input
                id="github_url"
                name="github_url"
                type="url"
                value={formData.github_url}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                placeholder="https://github.com/johndoe"
              />
            </div>

            <div>
              <label htmlFor="portfolio_url" className="block text-sm font-medium text-slate-700 mb-2">
                Portfolio URL
              </label>
              <input
                id="portfolio_url"
                name="portfolio_url"
                type="url"
                value={formData.portfolio_url}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                placeholder="https://johndoe.com"
              />
            </div>

            <div>
              <label htmlFor="availability" className="block text-sm font-medium text-slate-700 mb-2">
                Availability
              </label>
              <select
                id="availability"
                name="availability"
                value={formData.availability}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
              >
                <option value="">Select availability</option>
                <option value="immediate">Immediate</option>
                <option value="two_weeks">Two Weeks</option>
                <option value="one_month">One Month</option>
                <option value="not_available">Not Available</option>
              </select>
            </div>

            <div>
              <label htmlFor="work_preference" className="block text-sm font-medium text-slate-700 mb-2">
                Work Preference
              </label>
              <select
                id="work_preference"
                name="work_preference"
                value={formData.work_preference}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
              >
                <option value="">Select preference</option>
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite">On-site</option>
              </select>
            </div>

            <div>
              <label htmlFor="salary_expectation" className="block text-sm font-medium text-slate-700 mb-2">
                Salary Expectation
              </label>
              <input
                id="salary_expectation"
                name="salary_expectation"
                type="text"
                value={formData.salary_expectation}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                placeholder="$100k - $150k"
              />
            </div>
          </div>

          <div>
            <label htmlFor="skills" className="block text-sm font-medium text-slate-700 mb-2">
              Skills (comma-separated)
            </label>
            <input
              id="skills"
              name="skills"
              type="text"
              value={formData.skills}
              onChange={handleChange}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
              placeholder="JavaScript, React, Node.js, Python"
            />
          </div>

          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-slate-700 mb-2">
              Notes
            </label>
            <textarea
              id="notes"
              name="notes"
              rows={4}
              value={formData.notes}
              onChange={handleChange}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent resize-none"
              placeholder="Add any additional notes about this talent..."
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2.5 text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !!duplicateCheck}
              className="px-6 py-2.5 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Adding...' : 'Add Talent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
