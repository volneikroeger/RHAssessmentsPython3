import React from 'react';
import { User } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function ProfilePage() {
  return (
    <PlaceholderPage
      title="Profile Settings"
      description="Manage your personal information, preferences, and account settings."
      icon={User}
    />
  );
}

export function MyDataPage() {
  return (
    <PlaceholderPage
      title="My Data"
      description="View and export all your personal data in compliance with privacy regulations."
      icon={User}
    />
  );
}
