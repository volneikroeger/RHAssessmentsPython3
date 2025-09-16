# Enable Row Level Security for organizations app
from django.db import migrations
from core.db import execute_rls_migration


def enable_rls_for_organizations(apps, schema_editor):
    """Enable RLS for all organization-related tables."""
    tables = [
        'organizations_membership',
        'organizations_organizationinvite', 
        'organizations_department',
        'organizations_position',
        'organizations_employee',
    ]
    
    for table in tables:
        execute_rls_migration(table)


def reverse_rls_for_organizations(apps, schema_editor):
    """Disable RLS (reverse migration)."""
    with schema_editor.connection.cursor() as cursor:
        tables = [
            'organizations_membership',
            'organizations_organizationinvite',
            'organizations_department', 
            'organizations_position',
            'organizations_employee',
        ]
        
        for table in tables:
            cursor.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
            cursor.execute(f"DROP POLICY IF EXISTS tenant_iso_select ON {table}")
            cursor.execute(f"DROP POLICY IF EXISTS tenant_iso_write ON {table}")


class Migration(migrations.Migration):
    
    dependencies = [
        ('organizations', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(
            enable_rls_for_organizations,
            reverse_rls_for_organizations
        ),
    ]