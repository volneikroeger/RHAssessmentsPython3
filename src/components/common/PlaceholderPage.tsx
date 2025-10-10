import React from 'react';
import { Layout } from '../layout';
import { LucideIcon } from 'lucide-react';

interface PlaceholderPageProps {
  title: string;
  description: string;
  icon: LucideIcon;
  features?: string[];
}

export function PlaceholderPage({ title, description, icon: Icon, features }: PlaceholderPageProps) {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-slate-100 mb-6">
            <Icon className="w-10 h-10 text-slate-400" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900 mb-3">{title}</h2>
          <p className="text-slate-600 max-w-2xl mx-auto mb-8">{description}</p>

          {features && features.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-12">
              {features.map((feature, index) => (
                <div key={index} className="p-4 border border-slate-200 rounded-lg">
                  <p className="text-sm text-slate-700">{feature}</p>
                </div>
              ))}
            </div>
          )}

          <div className="mt-8 text-sm text-slate-500">
            <p>This module is coming soon</p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
