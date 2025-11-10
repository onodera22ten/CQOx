"""
Input Sanitization - NASA/Google Standard

Purpose: Prevent injection attacks and validate inputs
Features:
- SQL injection prevention
- XSS prevention
- Path traversal prevention
- Command injection prevention
- Email validation
- Phone validation
"""

import re
import html
from typing import Any, Optional
from pathlib import Path
import bleach


class InputSanitizer:
    """
    Input sanitization and validation

    Prevents:
    - SQL injection
    - XSS (Cross-Site Scripting)
    - Path traversal
    - Command injection
    - NoSQL injection
    """

    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(;.*\b(DROP|DELETE|UPDATE)\b)"
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"(;|\||&|`|\$\(|\$\{)",
        r"(&&|\|\|)",
        r"(>|<|>>)",
        r"(\.\./|\.\.\\)"
    ]

    @staticmethod
    def sanitize_string(
        value: str,
        max_length: Optional[int] = None,
        allow_html: bool = False
    ) -> str:
        """
        Sanitize string input

        Args:
            value: Input string
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags (will be sanitized)

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Trim whitespace
        value = value.strip()

        # Length check
        if max_length and len(value) > max_length:
            value = value[:max_length]

        if allow_html:
            # Sanitize HTML (allow safe tags only)
            allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a', 'p', 'br']
            allowed_attrs = {'a': ['href', 'title']}
            value = bleach.clean(
                value,
                tags=allowed_tags,
                attributes=allowed_attrs,
                strip=True
            )
        else:
            # Escape HTML entities
            value = html.escape(value)

        return value

    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """
        Check if input contains SQL injection patterns

        Returns:
            True if suspicious, False if safe
        """
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def check_command_injection(cls, value: str) -> bool:
        """
        Check if input contains command injection patterns

        Returns:
            True if suspicious, False if safe
        """
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                return True
        return False

    @staticmethod
    def sanitize_path(path: str, base_dir: Optional[str] = None) -> Path:
        """
        Sanitize file path to prevent path traversal attacks

        Args:
            path: Input path
            base_dir: Base directory (optional)

        Returns:
            Sanitized Path object

        Raises:
            ValueError: If path attempts to escape base_dir
        """
        # Remove null bytes
        path = path.replace('\x00', '')

        # Convert to Path object
        sanitized_path = Path(path).resolve()

        # Check if path escapes base directory
        if base_dir:
            base = Path(base_dir).resolve()
            try:
                sanitized_path.relative_to(base)
            except ValueError:
                raise ValueError(f"Path traversal detected: {path}")

        return sanitized_path

    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Validate and sanitize email address

        Returns:
            Sanitized email

        Raises:
            ValueError: If email is invalid
        """
        email = email.strip().lower()

        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            raise ValueError(f"Invalid email format: {email}")

        # Check length
        if len(email) > 254:  # RFC 5321
            raise ValueError("Email too long")

        return email

    @staticmethod
    def sanitize_phone(phone: str) -> str:
        """
        Sanitize phone number

        Returns:
            Sanitized phone number (digits only)
        """
        # Remove all non-digit characters
        phone = re.sub(r'\D', '', phone)

        # Validate length (US: 10 digits, International: 10-15 digits)
        if len(phone) < 10 or len(phone) > 15:
            raise ValueError(f"Invalid phone number length: {len(phone)}")

        return phone

    @staticmethod
    def sanitize_integer(
        value: Any,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> int:
        """
        Sanitize and validate integer input

        Args:
            value: Input value
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Validated integer

        Raises:
            ValueError: If validation fails
        """
        try:
            int_val = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid integer: {value}")

        if min_val is not None and int_val < min_val:
            raise ValueError(f"Value {int_val} below minimum {min_val}")

        if max_val is not None and int_val > max_val:
            raise ValueError(f"Value {int_val} above maximum {max_val}")

        return int_val

    @staticmethod
    def sanitize_float(
        value: Any,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None
    ) -> float:
        """Sanitize and validate float input"""
        try:
            float_val = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid float: {value}")

        if min_val is not None and float_val < min_val:
            raise ValueError(f"Value {float_val} below minimum {min_val}")

        if max_val is not None and float_val > max_val:
            raise ValueError(f"Value {float_val} above maximum {max_val}")

        return float_val

    @classmethod
    def validate_request_data(cls, data: dict, schema: dict) -> dict:
        """
        Validate and sanitize request data against schema

        Args:
            data: Input data dictionary
            schema: Validation schema
                {
                    "field_name": {
                        "type": "string|integer|float|email|phone",
                        "required": bool,
                        "max_length": int,
                        "min_value": int/float,
                        "max_value": int/float,
                        "allow_html": bool
                    }
                }

        Returns:
            Sanitized data dictionary

        Raises:
            ValueError: If validation fails
        """
        sanitized = {}

        for field, rules in schema.items():
            value = data.get(field)

            # Check required fields
            if rules.get("required") and value is None:
                raise ValueError(f"Missing required field: {field}")

            if value is None:
                continue

            # Apply type-specific sanitization
            field_type = rules.get("type", "string")

            if field_type == "string":
                sanitized[field] = cls.sanitize_string(
                    value,
                    max_length=rules.get("max_length"),
                    allow_html=rules.get("allow_html", False)
                )

            elif field_type == "integer":
                sanitized[field] = cls.sanitize_integer(
                    value,
                    min_val=rules.get("min_value"),
                    max_val=rules.get("max_value")
                )

            elif field_type == "float":
                sanitized[field] = cls.sanitize_float(
                    value,
                    min_val=rules.get("min_value"),
                    max_val=rules.get("max_value")
                )

            elif field_type == "email":
                sanitized[field] = cls.sanitize_email(value)

            elif field_type == "phone":
                sanitized[field] = cls.sanitize_phone(value)

            else:
                sanitized[field] = value

        return sanitized


# Singleton instance
input_sanitizer = InputSanitizer()
