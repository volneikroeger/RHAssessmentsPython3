import React, { useEffect, useState } from 'react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext';
import { Database } from '../../lib/database.types';
import { Users, Plus, Search, Filter, LogOut, User as UserIcon } from 'lucide-react';
import { TalentList } from './TalentList';
import { TalentForm } from './TalentForm';

type Talent = Database['public']['Tables']['talents']['Row'];

export function RecruiterDashboard() {
  const { profile, signOut } = useAuth();
  const [talents, setTalents] = useState<Talent[]>([]);
  const [filteredTalents, setFilteredTalents] = useState<Talent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'placed' | 'archived'>('all');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadTalents();
  }, []);

  useEffect(() => {
    filterTalents();
  }, [talents, searchQuery, statusFilter]);

  const loadTalents = async () => {
    try {
      const { data, error } = await supabase
        .from('talents')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setTalents(data || []);
    } catch (error) {
      console.error('Error loading talents:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterTalents = () => {
    let filtered = talents;

    if (statusFilter !== 'all') {
      filtered = filtered.filter((t) => t.status === statusFilter);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (t) =>
          t.full_name.toLowerCase().includes(query) ||
          t.email.toLowerCase().includes(query) ||
          t.job_title?.toLowerCase().includes(query) ||
          t.location?.toLowerCase().includes(query) ||
          t.skills?.some((skill) => skill.toLowerCase().includes(query))
      );
    }

    setFilteredTalents(filtered);
  };

  const stats = {
    total: talents.length,
    active: talents.filter((t) => t.status === 'active').length,
    placed: talents.filter((t) => t.status === 'placed').length,
    archived: talents.filter((t) => t.status === 'archived').length,
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-3">
              <div className="bg-slate-900 p-2 rounded-lg">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Talent Manager</h1>
                <p className="text-sm text-slate-600">Welcome back, {profile?.full_name}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Add Talent
              </button>
              <button
                onClick={signOut}
                className="flex items-center gap-2 text-slate-600 hover:text-slate-900 px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Total Talents</h3>
              <UserIcon className="w-5 h-5 text-slate-400" />
            </div>
            <p className="text-3xl font-bold text-slate-900">{stats.total}</p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Active</h3>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>
            <p className="text-3xl font-bold text-slate-900">{stats.active}</p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Placed</h3>
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            </div>
            <p className="text-3xl font-bold text-slate-900">{stats.placed}</p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Archived</h3>
              <div className="w-3 h-3 bg-slate-400 rounded-full"></div>
            </div>
            <p className="text-3xl font-bold text-slate-900">{stats.archived}</p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search talents by name, email, title, location, or skills..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                />
              </div>
              <div className="flex items-center gap-2">
                <Filter className="w-5 h-5 text-slate-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="placed">Placed</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>
          </div>

          <TalentList
            talents={filteredTalents}
            loading={loading}
            onRefresh={loadTalents}
            onAddClick={() => setShowAddModal(true)}
          />
        </div>
      </main>

      {showAddModal && (
        <TalentForm
          onClose={() => setShowAddModal(false)}
          onSuccess={loadTalents}
        />
      )}
    </div>
  );
}
