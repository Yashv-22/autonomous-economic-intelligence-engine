"""
Core Domain Exceptions and Error Taxonomy for Autonomous AI Operating-Model Intelligence System.
"""


class BaseSystemError(Exception):
    """Base exception for all system-level errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(BaseSystemError):
    """Raised when configuration validation or loading fails."""
    pass


class SecurityViolationError(BaseSystemError):
    """Raised when security boundaries, SSRF filters, or prompt injection defenses trigger."""
    pass


class NetworkAccessError(BaseSystemError):
    """Raised when external HTTP requests fail or violate rate/domain limits."""
    pass


class IngestionError(BaseSystemError):
    """Raised when document parsing or span generation fails."""
    pass


class ProvenanceVerificationError(BaseSystemError):
    """Raised when cryptographic hashes or Merkle trees fail verification."""
    pass


class ClaimExtractionError(BaseSystemError):
    """Raised when claim extraction or normalization fails."""
    pass


class ContradictionDetectionError(BaseSystemError):
    """Raised when contradiction detection fails."""
    pass


class StorageError(BaseSystemError):
    """Raised when database or file storage operations fail."""
    pass


class ModelGatewayError(BaseSystemError):
    """Raised when model calls, routing, rate limits, or context windows fail."""
    pass


class ToolExecutionError(BaseSystemError):
    """Raised when a tool execution fails or violates permissions."""
    pass


class OrchestrationError(BaseSystemError):
    """Raised when agent workflows or orchestrator state fails."""
    pass
