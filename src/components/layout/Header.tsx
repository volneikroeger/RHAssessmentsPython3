import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { ROUTES, MAIN_NAVIGATION, ADMIN_NAVIGATION, USER_MENU_ITEMS } from '../../config';
import {
  Menu,
  X,
  ChevronDown,
  Home,
  Users,
  ClipboardCheck,
  TrendingUp,
  Briefcase,
  CreditCard,
  BarChart,
  Mail,
  Settings,
  User,
  LogOut,
  Building2,
  Database,
  Globe,
  FolderKanban,
  FolderOpen,
  PlusCircle,
  List,
  Sliders,
  LayoutDashboard,
  FileText,
  Building,
  ShieldCheck,
  UserCircle,
} from 'lucide-react';

const iconMap: Record<string, React.FC<{ className?: string }>> = {
  Home,
  Users,
  ClipboardCheck,
  TrendingUp,
  Briefcase,
  CreditCard,
  BarChart,
  Mail,
  Settings,
  User,
  Building2,
  Database,
  Globe,
  FolderKanban,
  FolderOpen,
  PlusCircle,
  List,
  Sliders,
  LayoutDashboard,
  FileText,
  Building,
  ShieldCheck,
  UserCircle,
};

const Icon = ({ name, className }: { name: string; className?: string }) => {
  const IconComponent = iconMap[name] || Home;
  return <IconComponent className={className} />;
};

export function Header() {
  const { profile, signOut } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  const handleNavigate = (path: string | undefined) => {
    if (path) {
      navigate(path);
      setMobileMenuOpen(false);
      setActiveDropdown(null);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    navigate(ROUTES.LOGIN);
  };

  const isAdmin = profile?.role === 'admin';
  const userRole = profile?.role || 'company';

  const filteredNavigation = MAIN_NAVIGATION.filter((item) => {
    if (!item.roles) return true;
    return item.roles.includes(userRole);
  });

  return (
    <header className="bg-slate-900 text-white shadow-lg sticky top-0 z-50">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-4">
            <button
              onClick={() => handleNavigate(ROUTES.DASHBOARD)}
              className="flex items-center gap-2 hover:opacity-80 transition-opacity"
            >
              <div className="bg-white p-1.5 rounded-lg">
                <Building2 className="w-5 h-5 text-slate-900" />
              </div>
              <span className="font-bold text-lg hidden sm:inline">
                {profile?.company_name || 'Talent Platform'}
              </span>
            </button>
          </div>

          <nav className="hidden lg:flex items-center gap-1">
            {filteredNavigation.map((item) => (
              <div key={item.label} className="relative">
                {item.children ? (
                  <div className="relative">
                    <button
                      onClick={() =>
                        setActiveDropdown(activeDropdown === item.label ? null : item.label)
                      }
                      className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors"
                    >
                      <Icon name={item.icon} className="w-4 h-4" />
                      <span className="text-sm font-medium">{item.label}</span>
                      <ChevronDown className="w-4 h-4" />
                    </button>
                    {activeDropdown === item.label && (
                      <div className="absolute top-full left-0 mt-1 w-56 bg-white text-slate-900 rounded-lg shadow-xl border border-slate-200 py-2">
                        {item.children.map((child) => (
                          <button
                            key={child.label}
                            onClick={() => handleNavigate(child.path)}
                            className="w-full flex items-center gap-2 px-4 py-2 hover:bg-slate-50 transition-colors text-left"
                          >
                            <Icon name={child.icon} className="w-4 h-4" />
                            <span className="text-sm">{child.label}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={() => handleNavigate(item.path)}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    <Icon name={item.icon} className="w-4 h-4" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </button>
                )}
              </div>
            ))}

            {isAdmin && (
              <div className="relative">
                <button
                  onClick={() => setActiveDropdown(activeDropdown === 'admin' ? null : 'admin')}
                  className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  <span className="text-sm font-medium">Admin</span>
                  <ChevronDown className="w-4 h-4" />
                </button>
                {activeDropdown === 'admin' && (
                  <div className="absolute top-full right-0 mt-1 w-64 bg-white text-slate-900 rounded-lg shadow-xl border border-slate-200 py-2">
                    {ADMIN_NAVIGATION.map((section) => (
                      <div key={section.label}>
                        <div className="px-4 py-2 text-xs font-semibold text-slate-500 uppercase">
                          {section.label}
                        </div>
                        {section.children?.map((child) => (
                          <button
                            key={child.label}
                            onClick={() => handleNavigate(child.path)}
                            className="w-full flex items-center gap-2 px-4 py-2 hover:bg-slate-50 transition-colors text-left"
                          >
                            <Icon name={child.icon} className="w-4 h-4" />
                            <span className="text-sm">{child.label}</span>
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </nav>

          <div className="flex items-center gap-3">
            <button className="hidden lg:flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors">
              <Globe className="w-4 h-4" />
              <span className="text-sm">EN</span>
            </button>

            <div className="relative">
              <button
                onClick={() => setActiveDropdown(activeDropdown === 'user' ? null : 'user')}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <User className="w-4 h-4" />
                <span className="text-sm hidden sm:inline">
                  {profile?.full_name?.split(' ')[0] || 'User'}
                </span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {activeDropdown === 'user' && (
                <div className="absolute top-full right-0 mt-1 w-56 bg-white text-slate-900 rounded-lg shadow-xl border border-slate-200 py-2">
                  {USER_MENU_ITEMS.map((item) => (
                    <button
                      key={item.label}
                      onClick={() => handleNavigate(item.path)}
                      className="w-full flex items-center gap-2 px-4 py-2 hover:bg-slate-50 transition-colors text-left"
                    >
                      <Icon name={item.icon} className="w-4 h-4" />
                      <span className="text-sm">{item.label}</span>
                    </button>
                  ))}
                  <hr className="my-2 border-slate-200" />
                  <button
                    onClick={handleSignOut}
                    className="w-full flex items-center gap-2 px-4 py-2 hover:bg-slate-50 transition-colors text-left text-red-600"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="text-sm">Logout</span>
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-slate-800 transition-colors"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-slate-800 py-4">
            <nav className="flex flex-col gap-2">
              {filteredNavigation.map((item) => (
                <div key={item.label}>
                  {item.children ? (
                    <div>
                      <button
                        onClick={() =>
                          setActiveDropdown(activeDropdown === item.label ? null : item.label)
                        }
                        className="w-full flex items-center justify-between px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <Icon name={item.icon} className="w-4 h-4" />
                          <span className="text-sm font-medium">{item.label}</span>
                        </div>
                        <ChevronDown className="w-4 h-4" />
                      </button>
                      {activeDropdown === item.label && (
                        <div className="ml-6 mt-2 flex flex-col gap-1">
                          {item.children.map((child) => (
                            <button
                              key={child.label}
                              onClick={() => handleNavigate(child.path)}
                              className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors text-left"
                            >
                              <Icon name={child.icon} className="w-4 h-4" />
                              <span className="text-sm">{child.label}</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <button
                      onClick={() => handleNavigate(item.path)}
                      className="w-full flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors text-left"
                    >
                      <Icon name={item.icon} className="w-4 h-4" />
                      <span className="text-sm font-medium">{item.label}</span>
                    </button>
                  )}
                </div>
              ))}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
