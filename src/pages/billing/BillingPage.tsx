import React from 'react';
import { CreditCard } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function BillingDashboardPage() {
  return (
    <PlaceholderPage
      title="Billing & Subscriptions"
      description="Manage your subscription plans, payment methods, and billing history all in one place."
      icon={CreditCard}
      features={[
        'Flexible Subscription Plans',
        'Usage-based Billing',
        'Invoice Management',
        'Payment Methods',
        'Usage Analytics',
        'Automatic Renewals',
      ]}
    />
  );
}

export function InvoicesPage() {
  return (
    <PlaceholderPage
      title="Invoices"
      description="View and download all your billing invoices and payment history."
      icon={CreditCard}
    />
  );
}
