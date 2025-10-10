import React from 'react';
import { AssessmentList } from '../../components/assessments/AssessmentList';
import { AssessmentBuilder } from '../../components/assessments/AssessmentBuilder';
import { ClipboardCheck } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function AssessmentsListPage() {
  return (
    <div className="p-6">
      <AssessmentList />
    </div>
  );
}

export function TemplateLibraryPage() {
  return (
    <div className="p-6">
      <AssessmentBuilder />
    </div>
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
