export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',

  DASHBOARD: '/dashboard',

  ORGANIZATIONS: {
    LIST: '/organizations',
    CREATE: '/organizations/create',
    DETAIL: '/organizations/:id',
    UPDATE: '/organizations/:id/edit',
    EMPLOYEES: '/organizations/:id/employees',
    CREATE_EMPLOYEE: '/organizations/:id/employees/create',
    UPDATE_EMPLOYEE: '/organizations/:id/employees/:employeeId/edit',
    DEPARTMENTS: '/organizations/:id/departments',
    CREATE_DEPARTMENT: '/organizations/:id/departments/create',
    UPDATE_DEPARTMENT: '/organizations/:id/departments/:departmentId/edit',
    POSITIONS: '/organizations/:id/positions',
    MEMBERS: '/organizations/:id/members',
    SETTINGS: '/organizations/:id/settings',
    IMPORT_EMPLOYEES: '/organizations/:id/import-employees',
  },

  ASSESSMENTS: {
    LIST: '/assessments',
    CREATE: '/assessments/create',
    DETAIL: '/assessments/:id',
    UPDATE: '/assessments/:id/edit',
    INVITE: '/assessments/:id/invite',
    TAKE: '/assessments/take/:token',
    RESULT: '/assessments/result/:token',
    INSTANCES: '/assessments/instances',
    TEMPLATE_LIBRARY: '/assessments/templates',
    QUESTION_BANK: '/assessments/questions',
  },

  PDI: {
    DASHBOARD: '/pdi',
    LIST: '/pdi/plans',
    CREATE: '/pdi/plans/create',
    DETAIL: '/pdi/plans/:id',
    UPDATE: '/pdi/plans/:id/edit',
    BULK_GENERATE: '/pdi/generate',
    REPORTS: '/pdi/reports',
  },

  RECRUITING: {
    DASHBOARD: '/recruiting',
    CANDIDATES: '/recruiting/candidates',
    CREATE_CANDIDATE: '/recruiting/candidates/create',
    CANDIDATE_DETAIL: '/recruiting/candidates/:id',
    UPDATE_CANDIDATE: '/recruiting/candidates/:id/edit',
    JOBS: '/recruiting/jobs',
    CREATE_JOB: '/recruiting/jobs/create',
    JOB_DETAIL: '/recruiting/jobs/:id',
    UPDATE_JOB: '/recruiting/jobs/:id/edit',
    CLIENTS: '/recruiting/clients',
    PLACEMENTS: '/recruiting/placements',
    REPORTS: '/recruiting/reports',
  },

  BILLING: {
    DASHBOARD: '/billing',
    SUBSCRIBE: '/billing/subscribe',
    PAYMENT_METHOD: '/billing/payment-method',
    INVOICES: '/billing/invoices',
    USAGE: '/billing/usage',
  },

  REPORTS: {
    DASHBOARD: '/reports',
    LIST: '/reports/list',
    GENERATE: '/reports/generate',
    QUICK: '/reports/quick',
    DETAIL: '/reports/:id',
    ANALYTICS: '/reports/analytics',
  },

  EMAILS: {
    DASHBOARD: '/emails',
    TEMPLATES: '/emails/templates',
    CREATE_TEMPLATE: '/emails/templates/create',
    CAMPAIGNS: '/emails/campaigns',
    BULK: '/emails/bulk',
    ANALYTICS: '/emails/analytics',
  },

  ACCOUNT: {
    PROFILE: '/account/profile',
    SETTINGS: '/account/settings',
    MY_DATA: '/account/my-data',
  },

  ADMIN: {
    SYSTEM_CONFIG: '/admin/system-config',
    USER_MANAGEMENT: '/admin/users',
    SUPER_ADMIN: '/admin/super',
  },

  LEGAL: {
    PRIVACY: '/privacy',
    TERMS: '/terms',
  },
} as const;
