import React from 'react';
import { BarChart } from 'lucide-react';
import { PlaceholderPage } from '../../components/common/PlaceholderPage';

export function ReportsDashboardPage() {
  return (
    <PlaceholderPage
      title="Reports & Analytics"
      description="Generate comprehensive reports and gain insights into your talent management data."
      icon={BarChart}
      features={[
        'Custom Report Builder',
        'Pre-built Templates',
        'Data Visualization',
        'Export to PDF/Excel',
        'Scheduled Reports',
        'Benchmark Comparisons',
      ]}
    />
  );
}

export function AnalyticsPage() {
  return (
    <PlaceholderPage
      title="Analytics"
      description="Deep dive into your organization's data with advanced analytics and visualizations."
      icon={BarChart}
    />
  );
}
