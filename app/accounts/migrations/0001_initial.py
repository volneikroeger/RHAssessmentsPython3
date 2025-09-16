# Generated migration for accounts app
from django.db import migrations, models
import django.contrib.auth.models
import uuid
import fernet_fields.fields
from accounts.managers import UserManager


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('first_name', models.CharField(max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(max_length=150, verbose_name='last name')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='date joined')),
                ('phone', fernet_fields.fields.EncryptedTextField(blank=True, verbose_name='phone number')),
                ('preferred_language', models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese (Brazil)')], default='en', max_length=10, verbose_name='preferred language')),
                ('timezone', models.CharField(default='UTC', max_length=50, verbose_name='timezone')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'accounts_user',
            },
            managers=[
                ('objects', UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_of_birth', models.DateField(blank=True, null=True, verbose_name='date of birth')),
                ('gender', models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not_to_say', 'Prefer not to say')], max_length=20, verbose_name='gender')),
                ('job_title', models.CharField(blank=True, max_length=200, verbose_name='job title')),
                ('department', models.CharField(blank=True, max_length=200, verbose_name='department')),
                ('manager_email', fernet_fields.fields.EncryptedEmailField(blank=True, verbose_name='manager email')),
                ('email_notifications', models.BooleanField(default=True, verbose_name='email notifications')),
                ('sms_notifications', models.BooleanField(default=False, verbose_name='SMS notifications')),
                ('data_processing_consent', models.BooleanField(default=False, verbose_name='data processing consent')),
                ('marketing_consent', models.BooleanField(default=False, verbose_name='marketing consent')),
                ('consent_date', models.DateTimeField(blank=True, null=True, verbose_name='consent date')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='profile', to='accounts.user')),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
            },
        ),
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_key', models.CharField(max_length=40)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='sessions', to='accounts.user')),
            ],
            options={
                'verbose_name': 'User Session',
                'verbose_name_plural': 'User Sessions',
                'ordering': ['-last_activity'],
            },
        ),
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField()),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='password_reset_tokens', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Password Reset Token',
                'verbose_name_plural': 'Password Reset Tokens',
                'ordering': ['-created_at'],
            },
        ),
    ]