import React from 'react';
import { Users } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function CandidatesPage() {
  return (
    <PlaceholderPage
      title="Candidate Management"
      description="Track and manage all your recruitment candidates in one centralized location."
      icon={Users}
      features={[
        'Candidate Database',
        'Application Tracking',
        'Interview Scheduling',
        'Skills Assessment',
        'Communication History',
        'Document Management',
      ]}
    />
  );
}
