import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Building2, LogOut, Users, Briefcase, TrendingUp } from 'lucide-react';

export function CompanyDashboard() {
  const { profile, signOut } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-3">
              <div className="bg-slate-900 p-2 rounded-lg">
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">
                  {profile?.company_name || 'Company Portal'}
                </h1>
                <p className="text-sm text-slate-600">Welcome back, {profile?.full_name}</p>
              </div>
            </div>
            <button
              onClick={signOut}
              className="flex items-center gap-2 text-slate-600 hover:text-slate-900 px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-slate-100 mb-6">
            <Building2 className="w-10 h-10 text-slate-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-3">Company Dashboard</h2>
          <p className="text-slate-600 max-w-2xl mx-auto mb-8">
            Your company portal is being set up. Soon you'll be able to browse talent pools,
            post job openings, and connect with recruiters to find the perfect candidates for your team.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
            <div className="p-6 border border-slate-200 rounded-lg">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Browse Talent</h3>
              <p className="text-sm text-slate-600">
                Access curated talent pools from our network of recruiters
              </p>
            </div>

            <div className="p-6 border border-slate-200 rounded-lg">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Briefcase className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Post Jobs</h3>
              <p className="text-sm text-slate-600">
                Create job listings and reach qualified candidates
              </p>
            </div>

            <div className="p-6 border border-slate-200 rounded-lg">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Track Progress</h3>
              <p className="text-sm text-slate-600">
                Monitor your hiring pipeline and candidate engagement
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
