import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { QUICK_ACTIONS } from '../../config';
import {
  UserPlus,
  PlusCircle,
  Briefcase,
  Settings,
  ShieldCheck,
} from 'lucide-react';

const iconMap: Record<string, React.FC<{ className?: string }>> = {
  UserPlus,
  PlusCircle,
  Briefcase,
  Settings,
  ShieldCheck,
};

const Icon = ({ name, className }: { name: string; className?: string }) => {
  const IconComponent = iconMap[name] || PlusCircle;
  return <IconComponent className={className} />;
};

export function Sidebar() {
  const { profile } = useAuth();
  const navigate = useNavigate();
  const userRole = profile?.role || 'company';
  const isAdmin = profile?.role === 'admin';

  const quickActions = QUICK_ACTIONS[userRole] || [];

  return (
    <aside className="hidden md:block w-64 bg-white border-r border-slate-200 min-h-screen sticky top-16">
      <div className="p-4">
        <div className="mb-6">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Quick Actions
          </h3>
          <div className="flex flex-col gap-1">
            {quickActions.map((action) => (
              <button
                key={action.label}
                onClick={() => navigate(action.path)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors text-left"
              >
                <Icon name={action.icon} className="w-4 h-4" />
                <span className="text-sm font-medium">{action.label}</span>
              </button>
            ))}
          </div>
        </div>

        {isAdmin && (
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Super Admin
            </h3>
            <div className="flex flex-col gap-1">
              <button
                onClick={() => navigate('/admin/super')}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors text-left"
              >
                <ShieldCheck className="w-4 h-4" />
                <span className="text-sm font-medium">Super Admin Panel</span>
              </button>
              <button
                onClick={() => navigate('/admin/system-config')}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors text-left"
              >
                <Settings className="w-4 h-4" />
                <span className="text-sm font-medium">System Settings</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
