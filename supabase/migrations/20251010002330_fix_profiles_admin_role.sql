/*
  # Fix Profiles Table to Support Admin Role

  ## Changes
  - Update the profiles table role constraint to include 'admin'
  
  ## Notes
  This fixes the constraint that was preventing admin role assignment
*/

-- Drop the existing check constraint
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_role_check;

-- Add the new check constraint with admin support
ALTER TABLE profiles ADD CONSTRAINT profiles_role_check
  CHECK (role IN ('recruiter', 'company', 'admin'));
