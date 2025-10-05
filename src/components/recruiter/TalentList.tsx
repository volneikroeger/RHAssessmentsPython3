import React from 'react';
import { Database } from '../../lib/database.types';
import { Mail, MapPin, Briefcase, ExternalLink, Linkedin, Github, Globe } from 'lucide-react';

type Talent = Database['public']['Tables']['talents']['Row'];

interface TalentListProps {
  talents: Talent[];
  loading: boolean;
  onRefresh: () => void;
  onAddClick: () => void;
}

export function TalentList({ talents, loading, onRefresh, onAddClick }: TalentListProps) {
  if (loading) {
    return (
      <div className="p-12 text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-slate-200 border-t-slate-900"></div>
        <p className="mt-4 text-slate-600">Loading talents...</p>
      </div>
    );
  }

  if (talents.length === 0) {
    return (
      <div className="p-12 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
          <Briefcase className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-2">No talents found</h3>
        <p className="text-slate-600 mb-6">Get started by adding your first talent to the system.</p>
        <button
          onClick={onAddClick}
          className="bg-slate-900 text-white px-6 py-2.5 rounded-lg hover:bg-slate-800 transition-colors"
        >
          Add Your First Talent
        </button>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'placed':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'archived':
        return 'bg-slate-100 text-slate-700 border-slate-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getExperienceLabel = (level: string | null) => {
    if (!level) return null;
    const labels: Record<string, string> = {
      entry: 'Entry Level',
      mid: 'Mid Level',
      senior: 'Senior',
      lead: 'Lead',
      executive: 'Executive',
    };
    return labels[level] || level;
  };

  return (
    <div className="divide-y divide-slate-200">
      {talents.map((talent) => (
        <div key={talent.id} className="p-6 hover:bg-slate-50 transition-colors">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
                  <span className="text-lg font-semibold text-slate-700">
                    {talent.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-slate-900 mb-1">{talent.full_name}</h3>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
                    {talent.job_title && (
                      <span className="flex items-center gap-1">
                        <Briefcase className="w-4 h-4" />
                        {talent.job_title}
                      </span>
                    )}
                    {talent.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {talent.location}
                      </span>
                    )}
                    {talent.experience_level && (
                      <span className="px-2 py-1 bg-slate-100 rounded text-xs font-medium">
                        {getExperienceLabel(talent.experience_level)}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-4 mb-3">
                <a
                  href={`mailto:${talent.email}`}
                  className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                >
                  <Mail className="w-4 h-4" />
                  {talent.email}
                </a>
                {talent.linkedin_url && (
                  <a
                    href={talent.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                  >
                    <Linkedin className="w-4 h-4" />
                    LinkedIn
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
                {talent.github_url && (
                  <a
                    href={talent.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                  >
                    <Github className="w-4 h-4" />
                    GitHub
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
                {talent.portfolio_url && (
                  <a
                    href={talent.portfolio_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                  >
                    <Globe className="w-4 h-4" />
                    Portfolio
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>

              {talent.skills && talent.skills.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {talent.skills.slice(0, 8).map((skill, index) => (
                    <span
                      key={index}
                      className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-md text-xs font-medium"
                    >
                      {skill}
                    </span>
                  ))}
                  {talent.skills.length > 8 && (
                    <span className="px-2.5 py-1 text-slate-500 text-xs font-medium">
                      +{talent.skills.length - 8} more
                    </span>
                  )}
                </div>
              )}

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                {talent.work_preference && (
                  <span className="capitalize">{talent.work_preference}</span>
                )}
                {talent.availability && (
                  <span className="capitalize">{talent.availability.replace('_', ' ')}</span>
                )}
                {talent.salary_expectation && (
                  <span>{talent.salary_expectation}</span>
                )}
              </div>
            </div>

            <div className="flex flex-col items-end gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(talent.status)}`}>
                {talent.status.charAt(0).toUpperCase() + talent.status.slice(1)}
              </span>
              <span className="text-xs text-slate-500">
                Added {new Date(talent.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
