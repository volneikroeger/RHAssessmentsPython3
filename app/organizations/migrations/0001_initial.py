# Generated migration for organizations app
from django.db import migrations, models
import django.db.models.deletion
import uuid
import fernet_fields.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Create organizations table
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='slug')),
                ('kind', models.CharField(choices=[('COMPANY', 'Company (HR + PDI)'), ('RECRUITER', 'Recruiter (R&S)')], max_length=20, verbose_name='kind')),
                ('locale_default', models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese (Brazil)')], default='en', max_length=10, verbose_name='default locale')),
                ('timezone', models.CharField(default='UTC', max_length=50, verbose_name='timezone')),
                ('domain_primary', models.CharField(blank=True, max_length=255, verbose_name='primary domain')),
                ('subdomain', models.CharField(blank=True, max_length=100, unique=True, verbose_name='subdomain')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='contact email')),
                ('phone', fernet_fields.fields.EncryptedTextField(blank=True, verbose_name='phone number')),
                ('website', models.URLField(blank=True, verbose_name='website')),
                ('address_line1', fernet_fields.fields.EncryptedTextField(blank=True, verbose_name='address line 1')),
                ('address_line2', fernet_fields.fields.EncryptedTextField(blank=True, verbose_name='address line 2')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='city')),
                ('state', models.CharField(blank=True, max_length=100, verbose_name='state')),
                ('postal_code', models.CharField(blank=True, max_length=20, verbose_name='postal code')),
                ('country', models.CharField(blank=True, max_length=100, verbose_name='country')),
                ('tax_id', fernet_fields.fields.EncryptedTextField(blank=True, verbose_name='tax ID')),
                ('legal_name', models.CharField(blank=True, max_length=300, verbose_name='legal name')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('allow_self_registration', models.BooleanField(default=False, verbose_name='allow self registration')),
                ('logo', models.ImageField(blank=True, upload_to='org_logos/', verbose_name='logo')),
                ('primary_color', models.CharField(default='#007bff', max_length=7, verbose_name='primary color')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user')),
            ],
            options={
                'verbose_name': 'Organization',
                'verbose_name_plural': 'Organizations',
                'ordering': ['name'],
            },
        ),
        
        # Create memberships table  
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('SUPER_ADMIN', 'Super Admin'), ('ORG_ADMIN', 'Organization Admin'), ('MANAGER', 'Manager'), ('HR', 'HR'), ('RECRUITER', 'Recruiter'), ('MEMBER', 'Member'), ('VIEWER', 'Viewer')], default='MEMBER', max_length=20, verbose_name='role')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('is_primary', models.BooleanField(default=False, verbose_name='primary organization')),
                ('invited_at', models.DateTimeField(blank=True, null=True)),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invited_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_invitations', to='accounts.user')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='organizations.organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Membership',
                'verbose_name_plural': 'Memberships',
                'ordering': ['organization__name', 'user__email'],
            },
        ),
        
        # Create organization invites table
        migrations.CreateModel(
            name='OrganizationInvite',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, verbose_name='email address')),
                ('role', models.CharField(choices=[('SUPER_ADMIN', 'Super Admin'), ('ORG_ADMIN', 'Organization Admin'), ('MANAGER', 'Manager'), ('HR', 'HR'), ('RECRUITER', 'Recruiter'), ('MEMBER', 'Member'), ('VIEWER', 'Viewer')], default='MEMBER', max_length=20, verbose_name='role')),
                ('token', models.CharField(max_length=100, unique=True, verbose_name='token')),
                ('message', models.TextField(blank=True, verbose_name='personal message')),
                ('is_accepted', models.BooleanField(default=False, verbose_name='accepted')),
                ('accepted_at', models.DateTimeField(blank=True, null=True, verbose_name='accepted at')),
                ('expires_at', models.DateTimeField(verbose_name='expires at')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invited_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_invites_sent', to='accounts.user')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invites', to='organizations.organization')),
            ],
            options={
                'verbose_name': 'Organization Invite',
                'verbose_name_plural': 'Organization Invites',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create departments table
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_departments', to='accounts.user')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='departments', to='organizations.organization')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='organizations.department')),
            ],
            options={
                'verbose_name': 'Department',
                'verbose_name_plural': 'Departments',
                'ordering': ['name'],
            },
        ),
        
        # Create positions table
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='title')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('level', models.PositiveIntegerField(default=1, verbose_name='level')),
                ('required_skills', models.JSONField(blank=True, default=list, verbose_name='required skills')),
                ('preferred_skills', models.JSONField(blank=True, default=list, verbose_name='preferred skills')),
                ('min_experience_years', models.PositiveIntegerField(default=0, verbose_name='minimum experience (years)')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='organizations.department')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='organizations.organization')),
                ('reports_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.position')),
            ],
            options={
                'verbose_name': 'Position',
                'verbose_name_plural': 'Positions',
                'ordering': ['department__name', 'title'],
            },
        ),
        
        # Create employees table
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('employee_id', models.CharField(blank=True, max_length=50, verbose_name='employee ID')),
                ('hire_date', models.DateField(verbose_name='hire date')),
                ('termination_date', models.DateField(blank=True, null=True, verbose_name='termination date')),
                ('employment_type', models.CharField(choices=[('FULL_TIME', 'Full Time'), ('PART_TIME', 'Part Time'), ('CONTRACTOR', 'Contractor'), ('INTERN', 'Intern')], default='FULL_TIME', max_length=20, verbose_name='employment type')),
                ('salary', fernet_fields.fields.EncryptedTextField(blank=True, verbose_name='salary')),
                ('currency', models.CharField(default='USD', max_length=3, verbose_name='currency')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='organizations.department')),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='direct_reports', to='organizations.employee')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='organizations.organization')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='organizations.position')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employments', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Employee',
                'verbose_name_plural': 'Employees',
                'ordering': ['user__first_name', 'user__last_name'],
            },
        ),
        
        # Add constraints
        migrations.AddConstraint(
            model_name='membership',
            constraint=models.UniqueConstraint(fields=('user', 'organization'), name='unique_user_organization'),
        ),
        migrations.AddConstraint(
            model_name='organizationinvite',
            constraint=models.UniqueConstraint(fields=('organization', 'email'), name='unique_org_email_invite'),
        ),
        migrations.AddConstraint(
            model_name='department',
            constraint=models.UniqueConstraint(fields=('organization', 'name'), name='unique_org_department'),
        ),
        migrations.AddConstraint(
            model_name='position',
            constraint=models.UniqueConstraint(fields=('organization', 'department', 'title'), name='unique_org_dept_position'),
        ),
        migrations.AddConstraint(
            model_name='employee',
            constraint=models.UniqueConstraint(fields=('organization', 'user'), name='unique_org_user_employee'),
        ),
    ]