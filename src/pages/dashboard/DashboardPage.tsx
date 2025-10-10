import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Layout } from '../../components/layout';
import { BarChart, Users, TrendingUp, Calendar } from 'lucide-react';

export function DashboardPage() {
  const { profile } = useAuth();

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">
            Welcome back, {profile?.full_name?.split(' ')[0]}!
          </h1>
          <p className="text-slate-600 mt-2">
            Here's what's happening with your {profile?.role === 'recruiter' ? 'talent pool' : 'organization'} today
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-slate-900">0</h3>
            <p className="text-sm text-slate-600 mt-1">
              {profile?.role === 'recruiter' ? 'Active Candidates' : 'Total Employees'}
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-green-100 p-3 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-slate-900">0</h3>
            <p className="text-sm text-slate-600 mt-1">Active Projects</p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-orange-100 p-3 rounded-lg">
                <Calendar className="w-6 h-6 text-orange-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-slate-900">0</h3>
            <p className="text-sm text-slate-600 mt-1">Upcoming Events</p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-purple-100 p-3 rounded-lg">
                <BarChart className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-slate-900">0</h3>
            <p className="text-sm text-slate-600 mt-1">Reports Generated</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Recent Activity</h3>
            <div className="text-center py-12 text-slate-500">
              <p>No recent activity</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Stats</h3>
            <div className="text-center py-12 text-slate-500">
              <p>Statistics will appear here</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
