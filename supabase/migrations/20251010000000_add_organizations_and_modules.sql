/*
  # Add Organizations and Multi-Tenant Support

  ## Overview
  This migration adds support for multi-tenant organizations, employees, departments,
  and organization membership management.

  ## New Tables

  ### 1. `organizations`
  Main organization/tenant table:
  - `id` (uuid) - Primary key
  - `name` (text) - Organization name
  - `kind` (text) - Organization type: 'COMPANY' or 'RECRUITER'
  - `subdomain` (text, unique, nullable) - Custom subdomain
  - `logo_url` (text, nullable) - Organization logo
  - `primary_color` (text, nullable) - Brand color
  - `is_active` (boolean) - Active status
  - `created_at` (timestamptz) - Creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### 2. `organization_members`
  Links users to organizations with roles:
  - `id` (uuid) - Primary key
  - `organization_id` (uuid, FK) - Reference to organization
  - `user_id` (uuid, FK) - Reference to user profile
  - `role` (text) - Member role
  - `is_active` (boolean) - Membership status
  - `created_at` (timestamptz) - Join timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### 3. `employees`
  Employee records for company organizations:
  - `id` (uuid) - Primary key
  - `organization_id` (uuid, FK) - Reference to organization
  - `first_name` (text) - Employee first name
  - `last_name` (text) - Employee last name
  - `email` (text) - Employee email
  - `phone` (text, nullable) - Contact phone
  - `job_title` (text, nullable) - Job title
  - `department_id` (uuid, FK, nullable) - Reference to department
  - `hire_date` (date, nullable) - Hire date
  - `is_active` (boolean) - Employment status
  - `created_at` (timestamptz) - Record creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### 4. `departments`
  Department structure for organizations:
  - `id` (uuid) - Primary key
  - `organization_id` (uuid, FK) - Reference to organization
  - `name` (text) - Department name
  - `description` (text, nullable) - Department description
  - `manager_id` (uuid, FK, nullable) - Reference to employee manager
  - `is_active` (boolean) - Department status
  - `created_at` (timestamptz) - Creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ## Security

  - Enable Row Level Security (RLS) on all tables
  - Organization members can access their organization's data
  - Admins have additional permissions

  ## Indexes

  - Indexes on foreign keys for performance
  - Unique constraints where appropriate
*/

-- Update profiles table to support admin role
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'profiles_role_check'
  ) THEN
    ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_role_check;
    ALTER TABLE profiles ADD CONSTRAINT profiles_role_check
      CHECK (role IN ('recruiter', 'company', 'admin'));
  END IF;
END $$;

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('COMPANY', 'RECRUITER')),
  subdomain text UNIQUE,
  logo_url text,
  primary_color text DEFAULT '#007bff',
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create organization_members table
CREATE TABLE IF NOT EXISTS organization_members (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR', 'MANAGER', 'EMPLOYEE')),
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(organization_id, user_id)
);

-- Create departments table
CREATE TABLE IF NOT EXISTS departments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  manager_id uuid,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  first_name text NOT NULL,
  last_name text NOT NULL,
  email text NOT NULL,
  phone text,
  job_title text,
  department_id uuid REFERENCES departments(id) ON DELETE SET NULL,
  hire_date date,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Add foreign key constraint for department manager after employees table exists
ALTER TABLE departments
  ADD CONSTRAINT fk_departments_manager
  FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_organizations_subdomain ON organizations(subdomain) WHERE subdomain IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_organization_members_org_id ON organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_user_id ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_employees_org_id ON employees(organization_id);
CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
CREATE INDEX IF NOT EXISTS idx_departments_org_id ON departments(organization_id);

-- Enable Row Level Security
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;

-- Organizations policies
CREATE POLICY "Users can view organizations they are members of"
  ON organizations FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM organization_members
      WHERE organization_members.organization_id = organizations.id
      AND organization_members.user_id = auth.uid()
      AND organization_members.is_active = true
    )
  );

CREATE POLICY "Organization admins can update their organization"
  ON organizations FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM organization_members
      WHERE organization_members.organization_id = organizations.id
      AND organization_members.user_id = auth.uid()
      AND organization_members.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
      AND organization_members.is_active = true
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM organization_members
      WHERE organization_members.organization_id = organizations.id
      AND organization_members.user_id = auth.uid()
      AND organization_members.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
      AND organization_members.is_active = true
    )
  );

-- Organization members policies
CREATE POLICY "Users can view members of their organizations"
  ON organization_members FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM organization_members om
      WHERE om.organization_id = organization_members.organization_id
      AND om.user_id = auth.uid()
      AND om.is_active = true
    )
  );

CREATE POLICY "Organization admins can manage members"
  ON organization_members FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM organization_members om
      WHERE om.organization_id = organization_members.organization_id
      AND om.user_id = auth.uid()
      AND om.role IN ('SUPER_ADMIN', 'ORG_ADMIN')
      AND om.is_active = true
    )
  );

-- Employees policies
CREATE POLICY "Organization members can view employees"
  ON employees FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM organization_members
      WHERE organization_members.organization_id = employees.organization_id
      AND organization_members.user_id = auth.uid()
      AND organization_members.is_active = true
    )
  );

CREATE POLICY "HR and admins can manage employees"
  ON employees FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM organization_members
      WHERE organization_members.organization_id = employees.organization_id
      AND organization_members.user_id = auth.uid()
      AND organization_members.role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR')
      AND organization_members.is_active = true
    )
  );

-- Departments policies
CREATE POLICY "Organization members can view departments"
  ON departments FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM organization_members
      WHERE organization_members.organization_id = departments.organization_id
      AND organization_members.user_id = auth.uid()
      AND organization_members.is_active = true
    )
  );

CREATE POLICY "HR and admins can manage departments"
  ON departments FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM organization_members
      WHERE organization_members.organization_id = departments.organization_id
      AND organization_members.user_id = auth.uid()
      AND organization_members.role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'HR')
      AND organization_members.is_active = true
    )
  );

-- Create triggers for updated_at
CREATE TRIGGER update_organizations_updated_at
  BEFORE UPDATE ON organizations
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organization_members_updated_at
  BEFORE UPDATE ON organization_members
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employees_updated_at
  BEFORE UPDATE ON employees
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_departments_updated_at
  BEFORE UPDATE ON departments
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
