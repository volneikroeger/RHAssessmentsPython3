import React from 'react';
import { ClipboardCheck } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function AssessmentsListPage() {
  return (
    <PlaceholderPage
      title="Psychological Assessments"
      description="Create, manage, and send psychological assessments to evaluate candidate fit and employee development."
      icon={ClipboardCheck}
      features={[
        'Pre-built Assessment Templates',
        'Custom Question Banks',
        'Automated Scoring',
        'Detailed Reports',
        'Multi-language Support',
        'Compliance & Privacy',
      ]}
    />
  );
}

export function TemplateLibraryPage() {
  return (
    <PlaceholderPage
      title="Assessment Template Library"
      description="Browse and manage your library of assessment templates. Create new templates or customize existing ones."
      icon={ClipboardCheck}
    />
  );
}

export function QuestionBankPage() {
  return (
    <PlaceholderPage
      title="Question Bank"
      description="Manage your repository of assessment questions. Organize by category, difficulty, and competency."
      icon={ClipboardCheck}
    />
  );
}
