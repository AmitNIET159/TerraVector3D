"""
Custom exceptions for the bhudrishti_identity_rights module.

All exceptions inherit from a common base so callers can catch broadly
or narrowly as needed.
"""


class VerticalIdError(Exception):
    """Base exception for all vertical-ID operations."""
    pass


class VerticalIdValidationError(VerticalIdError):
    """Raised when a vertical ID fails one or more validation rules."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or [message]


class ParsingError(VerticalIdError):
    """Raised when a vertical ID string cannot be parsed into components."""
    pass


class RightsValidationError(Exception):
    """Raised when a rights record fails validation."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or [message]
