import { ROUTES } from './routes';

export interface NavItem {
  label: string;
  path?: string;
  icon: string;
  children?: NavItem[];
  roles?: ('recruiter' | 'company' | 'admin')[];
  requiresOrg?: boolean;
}

export const MAIN_NAVIGATION: NavItem[] = [
  {
    label: 'Dashboard',
    path: ROUTES.DASHBOARD,
    icon: 'Home',
  },
  {
    label: 'Organization',
    icon: 'Users',
    roles: ['company', 'admin'],
    requiresOrg: true,
    children: [
      {
        label: 'Employees',
        path: ROUTES.ORGANIZATIONS.EMPLOYEES,
        icon: 'UserCircle',
      },
      {
        label: 'Departments',
        path: ROUTES.ORGANIZATIONS.DEPARTMENTS,
        icon: 'Building2',
      },
      {
        label: 'Settings',
        path: ROUTES.ORGANIZATIONS.SETTINGS,
        icon: 'Settings',
      },
    ],
  },
  {
    label: 'Assessments',
    path: ROUTES.ASSESSMENTS.LIST,
    icon: 'ClipboardCheck',
    roles: ['company', 'admin'],
  },
  {
    label: 'PDI Plans',
    path: ROUTES.PDI.DASHBOARD,
    icon: 'TrendingUp',
    roles: ['company', 'admin'],
  },
  {
    label: 'Recruiting',
    icon: 'Briefcase',
    roles: ['recruiter', 'admin'],
    children: [
      {
        label: 'Dashboard',
        path: ROUTES.RECRUITING.DASHBOARD,
        icon: 'LayoutDashboard',
      },
      {
        label: 'Candidates',
        path: ROUTES.RECRUITING.CANDIDATES,
        icon: 'Users',
      },
      {
        label: 'Jobs',
        path: ROUTES.RECRUITING.JOBS,
        icon: 'Briefcase',
      },
      {
        label: 'Clients',
        path: ROUTES.RECRUITING.CLIENTS,
        icon: 'Building',
      },
      {
        label: 'Reports',
        path: ROUTES.RECRUITING.REPORTS,
        icon: 'FileText',
      },
    ],
  },
  {
    label: 'Billing',
    path: ROUTES.BILLING.DASHBOARD,
    icon: 'CreditCard',
  },
  {
    label: 'Reports',
    path: ROUTES.REPORTS.DASHBOARD,
    icon: 'BarChart',
  },
  {
    label: 'Emails',
    path: ROUTES.EMAILS.DASHBOARD,
    icon: 'Mail',
  },
];

export const ADMIN_NAVIGATION: NavItem[] = [
  {
    label: 'Assessment Management',
    icon: 'FolderKanban',
    children: [
      {
        label: 'Template Library',
        path: ROUTES.ASSESSMENTS.TEMPLATE_LIBRARY,
        icon: 'FolderOpen',
      },
      {
        label: 'Create Template',
        path: ROUTES.ASSESSMENTS.CREATE,
        icon: 'PlusCircle',
      },
      {
        label: 'Question Bank',
        path: ROUTES.ASSESSMENTS.QUESTION_BANK,
        icon: 'List',
      },
    ],
  },
  {
    label: 'System Configuration',
    icon: 'Settings',
    children: [
      {
        label: 'System Settings',
        path: ROUTES.ADMIN.SYSTEM_CONFIG,
        icon: 'Sliders',
      },
      {
        label: 'Organizations',
        path: ROUTES.ORGANIZATIONS.LIST,
        icon: 'Building2',
      },
      {
        label: 'User Management',
        path: ROUTES.ADMIN.USER_MANAGEMENT,
        icon: 'Users',
      },
    ],
  },
];

export const QUICK_ACTIONS = {
  company: [
    {
      label: 'Send Assessment',
      path: ROUTES.ASSESSMENTS.LIST,
      icon: 'PlusCircle',
    },
    {
      label: 'Add Employee',
      path: ROUTES.ORGANIZATIONS.CREATE_EMPLOYEE,
      icon: 'UserPlus',
    },
  ],
  recruiter: [
    {
      label: 'Add Candidate',
      path: ROUTES.RECRUITING.CREATE_CANDIDATE,
      icon: 'UserPlus',
    },
    {
      label: 'Create Job',
      path: ROUTES.RECRUITING.CREATE_JOB,
      icon: 'Briefcase',
    },
  ],
  admin: [
    {
      label: 'System Settings',
      path: ROUTES.ADMIN.SYSTEM_CONFIG,
      icon: 'Settings',
    },
    {
      label: 'Super Admin Panel',
      path: ROUTES.ADMIN.SUPER_ADMIN,
      icon: 'ShieldCheck',
    },
  ],
};

export const USER_MENU_ITEMS = [
  {
    label: 'Profile',
    path: ROUTES.ACCOUNT.PROFILE,
    icon: 'User',
  },
  {
    label: 'Switch Organization',
    path: ROUTES.ORGANIZATIONS.LIST,
    icon: 'Building2',
  },
  {
    label: 'My Data',
    path: ROUTES.ACCOUNT.MY_DATA,
    icon: 'Database',
  },
];
