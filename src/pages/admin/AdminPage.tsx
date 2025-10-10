import React from 'react';
import { Settings, ShieldCheck } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function SystemConfigPage() {
  return (
    <PlaceholderPage
      title="System Configuration"
      description="Configure system-wide settings, integrations, and platform preferences."
      icon={Settings}
      features={[
        'Global Settings',
        'Feature Flags',
        'Integration Management',
        'Security Settings',
        'Email Configuration',
        'API Management',
      ]}
    />
  );
}

export function SuperAdminPage() {
  return (
    <PlaceholderPage
      title="Super Admin Panel"
      description="Advanced administration tools for platform management and monitoring."
      icon={ShieldCheck}
    />
  );
}

export function UserManagementPage() {
  return (
    <PlaceholderPage
      title="User Management"
      description="Manage all platform users, their roles, and access permissions."
      icon={Settings}
    />
  );
}
