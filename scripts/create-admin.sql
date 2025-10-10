-- Script to create an admin account
--
-- INSTRUCTIONS:
-- 1. First, create a user in Supabase Authentication UI or via signup
-- 2. Get the user's UUID from the auth.users table
-- 3. Update the profile to make them an admin
-- 4. Optionally create an organization for them

-- Step 1: Find your user ID (run this first to see your user)
-- SELECT id, email FROM auth.users ORDER BY created_at DESC LIMIT 5;

-- Step 2: Update an existing user to admin role
-- Replace 'YOUR_USER_ID_HERE' with the actual UUID from step 1
-- UPDATE profiles
-- SET role = 'admin'
-- WHERE id = 'YOUR_USER_ID_HERE';

-- Step 3: (Optional) Create an admin organization
-- INSERT INTO organizations (name, kind, is_active)
-- VALUES ('Admin Organization', 'COMPANY', true)
-- RETURNING id;

-- Step 4: (Optional) Add user as organization member with SUPER_ADMIN role
-- Replace 'YOUR_USER_ID_HERE' and 'YOUR_ORG_ID_HERE' with actual UUIDs
-- INSERT INTO organization_members (organization_id, user_id, role, is_active)
-- VALUES ('YOUR_ORG_ID_HERE', 'YOUR_USER_ID_HERE', 'SUPER_ADMIN', true);
