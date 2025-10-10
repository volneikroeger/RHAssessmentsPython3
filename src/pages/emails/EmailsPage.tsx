import React from 'react';
import { Mail } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function EmailsDashboardPage() {
  return (
    <PlaceholderPage
      title="Email Management"
      description="Create email templates, manage campaigns, and track email engagement with your candidates and employees."
      icon={Mail}
      features={[
        'Email Templates',
        'Campaign Management',
        'Bulk Sending',
        'Email Analytics',
        'Personalization',
        'Unsubscribe Management',
      ]}
    />
  );
}

export function EmailTemplatesPage() {
  return (
    <PlaceholderPage
      title="Email Templates"
      description="Create and manage reusable email templates for consistent communication."
      icon={Mail}
    />
  );
}
