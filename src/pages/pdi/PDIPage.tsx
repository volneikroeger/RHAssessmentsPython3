import React from 'react';
import { TrendingUp } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function PDIDashboardPage() {
  return (
    <PlaceholderPage
      title="Professional Development Plans (PDI)"
      description="Create and track Individual Development Plans to help employees grow and reach their career goals."
      icon={TrendingUp}
      features={[
        'Goal Setting & Tracking',
        'Skill Gap Analysis',
        'Development Activities',
        'Progress Monitoring',
        'Manager Reviews',
        'Bulk Plan Generation',
      ]}
    />
  );
}

export function PDIPlansListPage() {
  return (
    <PlaceholderPage
      title="Development Plans"
      description="View and manage all active professional development plans across your organization."
      icon={TrendingUp}
    />
  );
}
