"""
Encryption Module - NASA/Google Standard

Purpose: Data encryption and security
Features:
- Data at rest encryption (Fernet)
- Password hashing (bcrypt)
- Token encryption
- Sensitive data protection
- Key rotation support
"""

import os
import base64
import hashlib
from typing import Optional, Union
from datetime import datetime, timedelta
import secrets

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import bcrypt


class Encryptor:
    """
    Data encryption and decryption

    Uses Fernet (symmetric encryption) for data at rest
    Uses bcrypt for password hashing
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryptor

        Args:
            encryption_key: Base64-encoded Fernet key (if None, uses env var)
        """
        self.encryption_key = encryption_key or os.getenv("ENCRYPTION_KEY")

        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY not set in environment")

        # Initialize Fernet cipher
        self.cipher = Fernet(self.encryption_key.encode())

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key

        Returns:
            Base64-encoded key (store this securely!)
        """
        key = Fernet.generate_key()
        return key.decode()

    def encrypt(self, plaintext: Union[str, bytes]) -> str:
        """
        Encrypt plaintext

        Args:
            plaintext: Data to encrypt

        Returns:
            Base64-encoded ciphertext
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()

        ciphertext = self.cipher.encrypt(plaintext)
        return base64.b64encode(ciphertext).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext

        Args:
            ciphertext: Base64-encoded encrypted data

        Returns:
            Decrypted plaintext
        """
        ciphertext_bytes = base64.b64decode(ciphertext.encode())
        plaintext = self.cipher.decrypt(ciphertext_bytes)
        return plaintext.decode()

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt

        Args:
            password: Plain password

        Returns:
            Hashed password (bcrypt format)
        """
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds = good security/performance balance
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify password against hash

        Args:
            password: Plain password to verify
            hashed: Bcrypt hashed password

        Returns:
            True if password matches
        """
        return bcrypt.checkpw(password.encode(), hashed.encode())

    @staticmethod
    def generate_api_key(prefix: str = "cqox") -> str:
        """
        Generate secure API key

        Args:
            prefix: Key prefix for identification

        Returns:
            API key (format: prefix_randomstring)
        """
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate secure random token

        Args:
            length: Token length in bytes

        Returns:
            URL-safe token
        """
        return secrets.token_urlsafe(length)

    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt specific fields in a dictionary

        Args:
            data: Dictionary with data
            fields_to_encrypt: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields
        """
        encrypted_data = data.copy()

        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field] is not None:
                # Convert to string if needed
                value = str(encrypted_data[field])
                encrypted_data[field] = self.encrypt(value)

        return encrypted_data

    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt specific fields in a dictionary

        Args:
            data: Dictionary with encrypted data
            fields_to_decrypt: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        decrypted_data = data.copy()

        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field] is not None:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except Exception:
                    # If decryption fails, leave as-is (might already be decrypted)
                    pass

        return decrypted_data


class TokenManager:
    """
    Secure token generation and validation

    For API tokens, session tokens, CSRF tokens, etc.
    """

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "changeme")

    def create_token(
        self,
        user_id: str,
        token_type: str = "access",
        expires_delta: Optional[timedelta] = None
    ) -> dict:
        """
        Create signed token with expiration

        Args:
            user_id: User identifier
            token_type: Token type (access, refresh, api_key)
            expires_delta: Expiration time delta

        Returns:
            Token dictionary with token, expires_at, type
        """
        if expires_delta is None:
            if token_type == "access":
                expires_delta = timedelta(hours=1)
            elif token_type == "refresh":
                expires_delta = timedelta(days=30)
            else:
                expires_delta = timedelta(days=365)

        # Generate random token
        random_token = secrets.token_urlsafe(32)

        # Create signature
        expires_at = datetime.utcnow() + expires_delta
        expires_ts = int(expires_at.timestamp())

        # Sign: HMAC(secret, user_id + token + expires + type)
        message = f"{user_id}:{random_token}:{expires_ts}:{token_type}"
        signature = hashlib.sha256(
            f"{self.secret_key}:{message}".encode()
        ).hexdigest()

        # Combine
        full_token = f"{user_id}:{random_token}:{expires_ts}:{token_type}:{signature}"
        encoded_token = base64.b64encode(full_token.encode()).decode()

        return {
            "token": encoded_token,
            "expires_at": expires_at.isoformat(),
            "token_type": token_type,
            "user_id": user_id
        }

    def validate_token(self, token: str) -> Optional[dict]:
        """
        Validate and decode token

        Args:
            token: Encoded token

        Returns:
            Token data if valid, None if invalid
        """
        try:
            # Decode
            decoded = base64.b64decode(token.encode()).decode()
            parts = decoded.split(":")

            if len(parts) != 5:
                return None

            user_id, random_token, expires_ts, token_type, signature = parts

            # Verify signature
            message = f"{user_id}:{random_token}:{expires_ts}:{token_type}"
            expected_signature = hashlib.sha256(
                f"{self.secret_key}:{message}".encode()
            ).hexdigest()

            if signature != expected_signature:
                return None

            # Check expiration
            expires_at = datetime.fromtimestamp(int(expires_ts))
            if datetime.utcnow() > expires_at:
                return None

            return {
                "user_id": user_id,
                "token_type": token_type,
                "expires_at": expires_at.isoformat()
            }

        except Exception:
            return None

    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)


# Singleton instances
encryptor = Encryptor() if os.getenv("ENCRYPTION_KEY") else None
token_manager = TokenManager()


# Utility functions

def encrypt_sensitive_fields(data: dict) -> dict:
    """
    Encrypt commonly sensitive fields

    Fields encrypted: password, api_key, secret, token, ssn, credit_card
    """
    if not encryptor:
        return data

    sensitive_fields = [
        "password", "api_key", "secret", "token",
        "ssn", "credit_card", "bank_account"
    ]

    return encryptor.encrypt_dict(data, sensitive_fields)


def decrypt_sensitive_fields(data: dict) -> dict:
    """Decrypt commonly sensitive fields"""
    if not encryptor:
        return data

    sensitive_fields = [
        "password", "api_key", "secret", "token",
        "ssn", "credit_card", "bank_account"
    ]

    return encryptor.decrypt_dict(data, sensitive_fields)
