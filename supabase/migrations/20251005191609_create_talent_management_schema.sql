/*
  # Talent Management Platform Schema

  ## Overview
  This migration creates the complete database schema for a talent management platform
  that serves both recruiters and companies.

  ## New Tables

  ### 1. `profiles`
  User profiles extending Supabase auth.users with additional information:
  - `id` (uuid, FK to auth.users) - Primary key linked to authentication
  - `email` (text) - User email address
  - `full_name` (text) - User's full name
  - `role` (text) - User role: 'recruiter' or 'company'
  - `company_name` (text, nullable) - Company name for company users
  - `phone` (text, nullable) - Contact phone number
  - `avatar_url` (text, nullable) - Profile picture URL
  - `created_at` (timestamptz) - Account creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### 2. `talents`
  Comprehensive talent profiles managed by recruiters:
  - `id` (uuid) - Primary key
  - `recruiter_id` (uuid, FK) - Reference to recruiter who added this talent
  - `email` (text, unique) - Talent's email (unique constraint prevents duplicates)
  - `full_name` (text) - Talent's full name
  - `phone` (text, nullable) - Contact phone number
  - `location` (text, nullable) - Current location/city
  - `job_title` (text, nullable) - Current or desired job title
  - `experience_level` (text, nullable) - Experience level: 'entry', 'mid', 'senior', 'lead', 'executive'
  - `linkedin_url` (text, unique, nullable) - LinkedIn profile URL (unique to prevent duplicates)
  - `github_url` (text, nullable) - GitHub profile URL
  - `portfolio_url` (text, nullable) - Personal portfolio/website URL
  - `resume_url` (text, nullable) - Stored resume file URL
  - `skills` (text[], nullable) - Array of skills/technologies
  - `salary_expectation` (text, nullable) - Expected salary range
  - `availability` (text, nullable) - Availability status: 'immediate', 'two_weeks', 'one_month', 'not_available'
  - `work_preference` (text, nullable) - Work preference: 'remote', 'hybrid', 'onsite'
  - `education` (jsonb, nullable) - Education history as JSON array
  - `work_experience` (jsonb, nullable) - Work experience as JSON array
  - `notes` (text, nullable) - Recruiter's private notes about the talent
  - `status` (text) - Current status: 'active', 'placed', 'archived'
  - `created_at` (timestamptz) - Record creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### 3. `talent_documents`
  Documents and files associated with talents:
  - `id` (uuid) - Primary key
  - `talent_id` (uuid, FK) - Reference to talent
  - `document_type` (text) - Type: 'resume', 'cover_letter', 'certificate', 'other'
  - `file_name` (text) - Original file name
  - `file_url` (text) - Storage URL for the document
  - `file_size` (integer, nullable) - File size in bytes
  - `mime_type` (text, nullable) - MIME type of the file
  - `uploaded_at` (timestamptz) - Upload timestamp

  ## Security
  
  - Enable Row Level Security (RLS) on all tables
  - Profiles: Users can read and update their own profile only
  - Talents: Recruiters can only access talents they created
  - Documents: Access controlled through talent ownership

  ## Indexes
  
  - Unique indexes on talent email and linkedin_url for fast duplicate checking
  - Indexes on recruiter_id and status for efficient filtering
  - Index on talent email for search performance
*/

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text NOT NULL,
  full_name text NOT NULL,
  role text NOT NULL CHECK (role IN ('recruiter', 'company')),
  company_name text,
  phone text,
  avatar_url text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create talents table
CREATE TABLE IF NOT EXISTS talents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  recruiter_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  email text NOT NULL UNIQUE,
  full_name text NOT NULL,
  phone text,
  location text,
  job_title text,
  experience_level text CHECK (experience_level IN ('entry', 'mid', 'senior', 'lead', 'executive')),
  linkedin_url text UNIQUE,
  github_url text,
  portfolio_url text,
  resume_url text,
  skills text[],
  salary_expectation text,
  availability text CHECK (availability IN ('immediate', 'two_weeks', 'one_month', 'not_available')),
  work_preference text CHECK (work_preference IN ('remote', 'hybrid', 'onsite')),
  education jsonb,
  work_experience jsonb,
  notes text,
  status text DEFAULT 'active' CHECK (status IN ('active', 'placed', 'archived')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create talent_documents table
CREATE TABLE IF NOT EXISTS talent_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  talent_id uuid NOT NULL REFERENCES talents(id) ON DELETE CASCADE,
  document_type text NOT NULL CHECK (document_type IN ('resume', 'cover_letter', 'certificate', 'other')),
  file_name text NOT NULL,
  file_url text NOT NULL,
  file_size integer,
  mime_type text,
  uploaded_at timestamptz DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_talents_recruiter_id ON talents(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_talents_status ON talents(status);
CREATE INDEX IF NOT EXISTS idx_talents_email ON talents(email);
CREATE INDEX IF NOT EXISTS idx_talents_linkedin_url ON talents(linkedin_url) WHERE linkedin_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_talent_documents_talent_id ON talent_documents(talent_id);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE talents ENABLE ROW LEVEL SECURITY;
ALTER TABLE talent_documents ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view their own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
  ON profiles FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);

-- Talents policies (recruiters can only access their own talents)
CREATE POLICY "Recruiters can view their own talents"
  ON talents FOR SELECT
  TO authenticated
  USING (recruiter_id = auth.uid());

CREATE POLICY "Recruiters can insert their own talents"
  ON talents FOR INSERT
  TO authenticated
  WITH CHECK (recruiter_id = auth.uid());

CREATE POLICY "Recruiters can update their own talents"
  ON talents FOR UPDATE
  TO authenticated
  USING (recruiter_id = auth.uid())
  WITH CHECK (recruiter_id = auth.uid());

CREATE POLICY "Recruiters can delete their own talents"
  ON talents FOR DELETE
  TO authenticated
  USING (recruiter_id = auth.uid());

-- Talent documents policies (access through talent ownership)
CREATE POLICY "Users can view documents for their talents"
  ON talent_documents FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM talents
      WHERE talents.id = talent_documents.talent_id
      AND talents.recruiter_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert documents for their talents"
  ON talent_documents FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM talents
      WHERE talents.id = talent_documents.talent_id
      AND talents.recruiter_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete documents for their talents"
  ON talent_documents FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM talents
      WHERE talents.id = talent_documents.talent_id
      AND talents.recruiter_id = auth.uid()
    )
  );

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_talents_updated_at
  BEFORE UPDATE ON talents
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
