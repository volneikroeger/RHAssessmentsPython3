import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ROUTES } from '../../config';

export function Footer() {
  const { profile } = useAuth();
  const navigate = useNavigate();

  return (
    <footer className="bg-slate-50 border-t border-slate-200 mt-auto">
      <div className="mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-sm text-slate-600 text-center md:text-left">
            <p>© 2025 Talent Management Platform.</p>
            <p className="text-xs mt-1">
              For organizational use only. Not for clinical diagnosis.
            </p>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <button
              onClick={() => navigate(ROUTES.LEGAL.PRIVACY)}
              className="text-slate-600 hover:text-slate-900 transition-colors"
            >
              Privacy Policy
            </button>
            <span className="text-slate-400">|</span>
            <button
              onClick={() => navigate(ROUTES.LEGAL.TERMS)}
              className="text-slate-600 hover:text-slate-900 transition-colors"
            >
              Terms of Service
            </button>
            {profile?.company_name && (
              <>
                <span className="text-slate-400">|</span>
                <span className="text-slate-600">{profile.company_name}</span>
              </>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
}
