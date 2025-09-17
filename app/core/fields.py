"""
Custom encrypted fields for Django models.
"""
import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class EncryptedFieldMixin:
    """Mixin for encrypted fields."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fernet = None
    
    @property
    def fernet(self):
        """Get or create Fernet instance."""
        if self._fernet is None:
            key = getattr(settings, 'PII_ENCRYPTION_KEY', None)
            if not key:
                raise ValueError("PII_ENCRYPTION_KEY setting is required for encrypted fields")
            
            # Ensure key is properly formatted
            if isinstance(key, str):
                key = key.encode()
            
            # If key is not base64 encoded, encode it
            try:
                base64.urlsafe_b64decode(key)
            except Exception:
                key = base64.urlsafe_b64encode(key[:32].ljust(32, b'0'))
            
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt_value(self, value):
        """Encrypt a value."""
        if value is None or value == '':
            return value
        
        if isinstance(value, str):
            value = value.encode('utf-8')
        
        encrypted = self.fernet.encrypt(value)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_value(self, value):
        """Decrypt a value."""
        if value is None or value == '':
            return value
        
        try:
            encrypted_bytes = base64.b64decode(value.encode('utf-8'))
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception:
            # If decryption fails, return the original value
            # This handles cases where data might not be encrypted yet
            return value
    
    def from_db_value(self, value, expression, connection):
        """Convert database value to Python value."""
        if value is None:
            return value
        return self.decrypt_value(value)
    
    def to_python(self, value):
        """Convert value to Python type."""
        if value is None:
            return value
        
        # If it's already decrypted, return as is
        if hasattr(value, '_decrypted'):
            return value
        
        # Try to decrypt
        decrypted = self.decrypt_value(value)
        
        # Mark as decrypted to avoid double decryption
        if hasattr(decrypted, '__dict__'):
            decrypted._decrypted = True
        
        return decrypted
    
    def get_prep_value(self, value):
        """Convert Python value to database value."""
        if value is None or value == '':
            return value
        
        # If already encrypted, return as is
        if hasattr(value, '_encrypted'):
            return value
        
        encrypted = self.encrypt_value(value)
        
        # Mark as encrypted
        if hasattr(encrypted, '__dict__'):
            encrypted._encrypted = True
        
        return encrypted


class EncryptedTextField(EncryptedFieldMixin, models.TextField):
    """Encrypted text field."""
    
    description = _("Encrypted text field")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EncryptedEmailField(EncryptedFieldMixin, models.EmailField):
    """Encrypted email field."""
    
    description = _("Encrypted email field")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def validate(self, value, model_instance):
        """Validate email format after decryption."""
        if value is None:
            return
        
        # Decrypt for validation
        decrypted_value = self.decrypt_value(value) if value else value
        
        # Create a temporary EmailField for validation
        temp_field = models.EmailField()
        temp_field.validate(decrypted_value, model_instance)


class EncryptedCharField(EncryptedFieldMixin, models.CharField):
    """Encrypted char field."""
    
    description = _("Encrypted char field")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)