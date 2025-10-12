/*
  # Fix RLS Policies for User Signup

  1. Changes
    - Add service_role bypass policies for profiles, organizations, and organization_members
    - These policies allow the handle_new_user() trigger to insert data
    - Keep existing authenticated user policies intact

  2. Security
    - Service role can insert profiles during signup
    - Service role can create organizations during signup
    - Service role can create organization memberships during signup
    - All other operations still protected by existing RLS policies
*/

-- Drop existing policies if they exist to avoid duplicates
DROP POLICY IF EXISTS "Service role can insert profiles" ON profiles;
DROP POLICY IF EXISTS "Authenticated users can create organizations" ON organizations;
DROP POLICY IF EXISTS "Service role can insert organizations" ON organizations;
DROP POLICY IF EXISTS "Service role can insert organization members" ON organization_members;

-- Add policy to allow service role to insert profiles during signup
CREATE POLICY "Service role can insert profiles"
  ON profiles
  FOR INSERT
  TO service_role
  WITH CHECK (true);

-- Add policy to allow authenticated users to create organizations
CREATE POLICY "Authenticated users can create organizations"
  ON organizations
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Add policy to allow service role to insert organizations during signup
CREATE POLICY "Service role can insert organizations"
  ON organizations
  FOR INSERT
  TO service_role
  WITH CHECK (true);

-- Add policy to allow service role to insert organization members during signup
CREATE POLICY "Service role can insert organization members"
  ON organization_members
  FOR INSERT
  TO service_role
  WITH CHECK (true);