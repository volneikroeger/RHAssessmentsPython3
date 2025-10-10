import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';
import { LoginPage } from './components/auth/LoginPage';
import { RegisterPage } from './components/auth/RegisterPage';
import { ROUTES } from './config/routes';

import { DashboardPage } from './pages/dashboard/DashboardPage';
import { RecruiterDashboardPage } from './pages/recruiting/RecruiterDashboardPage';
import { CandidatesPage } from './pages/recruiting/CandidatesPage';
import { JobsPage } from './pages/recruiting/JobsPage';

import { OrganizationsPage, EmployeesPage, DepartmentsPage, OrganizationSettingsPage } from './pages/organizations/OrganizationsPage';
import { AssessmentsListPage, TemplateLibraryPage, QuestionBankPage } from './pages/assessments/AssessmentsPage';
import { PDIDashboardPage, PDIPlansListPage } from './pages/pdi/PDIPage';
import { BillingDashboardPage, InvoicesPage } from './pages/billing/BillingPage';
import { ReportsDashboardPage, AnalyticsPage } from './pages/reports/ReportsPage';
import { EmailsDashboardPage, EmailTemplatesPage } from './pages/emails/EmailsPage';
import { ProfilePage, MyDataPage } from './pages/account/AccountPage';
import { SystemConfigPage, SuperAdminPage, UserManagementPage } from './pages/admin/AdminPage';
import { PrivacyPolicyPage, TermsOfServicePage } from './pages/legal/LegalPage';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-slate-200 border-t-slate-900 mb-4"></div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<LoginPage />} />
      <Route path={ROUTES.REGISTER} element={<RegisterPage />} />

      <Route
        path={ROUTES.DASHBOARD}
        element={
          <PrivateRoute>
            <DashboardPage />
          </PrivateRoute>
        }
      />

      <Route
        path={ROUTES.RECRUITING.DASHBOARD}
        element={
          <PrivateRoute>
            <RecruiterDashboardPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.RECRUITING.CANDIDATES}
        element={
          <PrivateRoute>
            <CandidatesPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.RECRUITING.JOBS}
        element={
          <PrivateRoute>
            <JobsPage />
          </PrivateRoute>
        }
      />

      <Route
        path={ROUTES.ORGANIZATIONS.LIST}
        element={
          <PrivateRoute>
            <OrganizationsPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/organizations/:id/employees"
        element={
          <PrivateRoute>
            <EmployeesPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/organizations/:id/departments"
        element={
          <PrivateRoute>
            <DepartmentsPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/organizations/:id/settings"
        element={
          <PrivateRoute>
            <OrganizationSettingsPage />
          </PrivateRoute>
        }
      />

      <Route
        path={ROUTES.ASSESSMENTS.LIST}
        element={
          <PrivateRoute>
            <AssessmentsListPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.ASSESSMENTS.TEMPLATE_LIBRARY}
        element={
          <PrivateRoute>
            <TemplateLibraryPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.ASSESSMENTS.QUESTION_BANK}
        element={
          <PrivateRoute>
            <QuestionBankPage />
          </PrivateRoute>
        }
      />

      <Route
        path={ROUTES.PDI.DASHBOARD}
        element={
          <PrivateRoute>
            <PDIDashboardPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.PDI.LIST}
        element={
          <PrivateRoute>
            <PDIPlansListPage />
          </PrivateRoute>
        }
      />

      <Route
        path={ROUTES.BILLING.DASHBOARD}
        element={
          <PrivateRoute>
            <BillingDashboardPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.BILLING.INVOICES}
        element={
          <PrivateRoute>
            <InvoicesPage />
          </PrivateRoute>
        }
      />

      <Route
        path={ROUTES.REPORTS.DASHBOARD}
        element={
          <PrivateRoute>
            <ReportsDashboardPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.REPORTS.ANALYTICS}
        element={
          <PrivateRoute>
            <AnalyticsPage />
          </PrivateRoute>
        }
      />

      <Route
        path={ROUTES.EMAILS.DASHBOARD}
        element={
          <PrivateRoute>
            <EmailsDashboardPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.EMAILS.TEMPLATES}
        element={
          <PrivateRoute>
            <EmailTemplatesPage />
          </PrivateRoute>
        }
      />

      <Route
        path={ROUTES.ACCOUNT.PROFILE}
        element={
          <PrivateRoute>
            <ProfilePage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.ACCOUNT.MY_DATA}
        element={
          <PrivateRoute>
            <MyDataPage />
          </PrivateRoute>
        }
      />

      <Route
        path={ROUTES.ADMIN.SYSTEM_CONFIG}
        element={
          <PrivateRoute>
            <SystemConfigPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.ADMIN.SUPER_ADMIN}
        element={
          <PrivateRoute>
            <SuperAdminPage />
          </PrivateRoute>
        }
      />
      <Route
        path={ROUTES.ADMIN.USER_MANAGEMENT}
        element={
          <PrivateRoute>
            <UserManagementPage />
          </PrivateRoute>
        }
      />

      <Route path={ROUTES.LEGAL.PRIVACY} element={<PrivacyPolicyPage />} />
      <Route path={ROUTES.LEGAL.TERMS} element={<TermsOfServicePage />} />

      <Route path="/" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
      <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}

export default App;
