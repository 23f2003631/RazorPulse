"""
Custom exceptions for the RazorPulse application.

Provides a structured exception hierarchy so callers can handle
different failure modes (configuration, database, external services,
validation) independently.
"""


class RazorPulseError(Exception):
    """Base exception for all RazorPulse application errors."""

    def __init__(self, message: str = "An unexpected error occurred"):
        self.message = message
        super().__init__(self.message)


class ConfigurationError(RazorPulseError):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message)


class DatabaseError(RazorPulseError):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message)


class ExternalServiceError(RazorPulseError):
    """Raised when an external service (Exa, Gemini, Razorpay) call fails."""

    def __init__(self, service_name: str, message: str = "External service error"):
        self.service_name = service_name
        super().__init__(f"[{service_name}] {message}")


class ExaServiceError(ExternalServiceError):
    """Raised when the Exa AI service fails."""

    def __init__(self, message: str = "Exa service error"):
        super().__init__(service_name="Exa", message=message)


class GeminiServiceError(ExternalServiceError):
    """Raised when the Google Gemini service fails."""

    def __init__(self, message: str = "Gemini service error"):
        super().__init__(service_name="Gemini", message=message)


class RiskEventValidationError(RazorPulseError):
    """Raised when risk event input data fails validation."""

    def __init__(self, message: str = "Risk event validation failed"):
        super().__init__(message)


class ResourceNotFoundError(RazorPulseError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} not found: {resource_id}")
