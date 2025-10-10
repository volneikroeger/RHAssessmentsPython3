-- Update the handle_new_user function to also create organization and membership
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
DECLARE
  v_organization_id uuid;
  v_organization_name text;
  v_organization_kind text;
  v_role_in_org text;
BEGIN
  -- Insert profile
  INSERT INTO public.profiles (id, email, full_name, role, company_name)
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', ''),
    COALESCE(new.raw_user_meta_data->>'role', 'recruiter'),
    new.raw_user_meta_data->>'company_name'
  );

  -- Determine organization details based on user role
  IF COALESCE(new.raw_user_meta_data->>'role', 'recruiter') = 'company' THEN
    v_organization_kind := 'COMPANY';
    v_organization_name := COALESCE(new.raw_user_meta_data->>'company_name', 'My Company');
    v_role_in_org := 'ORG_ADMIN';
  ELSE
    v_organization_kind := 'RECRUITER';
    v_organization_name := COALESCE(new.raw_user_meta_data->>'full_name', 'Recruiter') || '''s Workspace';
    v_role_in_org := 'ORG_ADMIN';
  END IF;

  -- Create organization for the user
  INSERT INTO public.organizations (name, kind, is_active)
  VALUES (v_organization_name, v_organization_kind, true)
  RETURNING id INTO v_organization_id;

  -- Create organization membership
  INSERT INTO public.organization_members (organization_id, user_id, role, is_active)
  VALUES (v_organization_id, new.id, v_role_in_org, true);

  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Recreate the trigger (it already exists, this ensures it uses the updated function)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();