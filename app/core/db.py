"""
Database utilities for multi-tenant functionality.
"""
from typing import Any, Optional
from django.db import models, connection
from django.db.models import QuerySet
from core.middleware import get_current_tenant


class TenantQuerySet(QuerySet):
    """QuerySet that automatically filters by current tenant."""
    
    def filter(self, *args, **kwargs):
        tenant = get_current_tenant()
        if tenant and 'organization' not in kwargs and 'organization_id' not in kwargs:
            kwargs['organization'] = tenant
        return super().filter(*args, **kwargs)


class TenantManager(models.Manager):
    """Manager that uses TenantQuerySet."""
    
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
    
    def create(self, **kwargs):
        tenant = get_current_tenant()
        if tenant and 'organization' not in kwargs:
            kwargs['organization'] = tenant
        return super().create(**kwargs)


class BaseTenantModel(models.Model):
    """
    Abstract base model for all multi-tenant entities.
    
    Automatically includes organization foreign key and uses
    tenant-aware manager.
    """
    
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set'
    )
    
    objects = TenantManager()
    
    class Meta:
        abstract = True
    
    def clean(self):
        """Validate that organization matches current tenant."""
        super().clean()
        tenant = get_current_tenant()
        if tenant and self.organization_id and str(self.organization_id) != str(tenant.id):
            raise ValueError(f"Object organization {self.organization_id} doesn't match current tenant {tenant.id}")
    
    def save(self, *args, **kwargs):
        # Auto-set organization if not provided
        if not self.organization_id:
            tenant = get_current_tenant()
            if tenant:
                self.organization = tenant
        
        # Only validate tenant match if we have an organization set
        if self.organization_id:
            self.clean()
        
        super().save(*args, **kwargs)


def set_rls_tenant(tenant_id: str) -> None:
    """
    Set the PostgreSQL session variable for Row Level Security.
    
    Args:
        tenant_id: UUID of the tenant organization
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SET LOCAL app.current_tenant = %s",
            [tenant_id]
        )


def execute_rls_migration(table_name: str, schema: str = 'public') -> None:
    """
    Enable RLS and create policies for a tenant table.
    
    Args:
        table_name: Name of the table to enable RLS on
        schema: Schema name (default: public)
    """
    with connection.cursor() as cursor:
        # Enable RLS
        cursor.execute(f"ALTER TABLE {schema}.{table_name} ENABLE ROW LEVEL SECURITY")
        
        # Create SELECT policy
        cursor.execute(f"""
            CREATE POLICY tenant_iso_select ON {schema}.{table_name}
            FOR SELECT USING (organization_id::text = current_setting('app.current_tenant', true))
        """)
        
        # Create INSERT/UPDATE/DELETE policy
        cursor.execute(f"""
            CREATE POLICY tenant_iso_write ON {schema}.{table_name}
            FOR ALL USING (organization_id::text = current_setting('app.current_tenant', true))
            WITH CHECK (organization_id::text = current_setting('app.current_tenant', true))
        """)