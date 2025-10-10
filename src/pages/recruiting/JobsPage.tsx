import React from 'react';
import { Briefcase } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function JobsPage() {
  return (
    <PlaceholderPage
      title="Job Postings"
      description="Create and manage job openings. Match candidates to positions and track the hiring pipeline."
      icon={Briefcase}
      features={[
        'Job Posting Management',
        'Candidate Matching',
        'Application Pipeline',
        'Client Requirements',
        'Job Templates',
        'Performance Metrics',
      ]}
    />
  );
}
