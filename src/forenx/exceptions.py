"""
Custom exception hierarchy for ForenX forensics operations.
"""

class ForenXError(Exception):
    """Base exception for all ForenX errors."""

class DatabaseError(ForenXError):
    """Raised on application or forensic database connection/query failures."""

class CaseNotFoundError(ForenXError):
    """Raised when a requested case ID is not found."""

class EvidenceError(ForenXError):
    """Raised when evidence handling, copying, or access fails."""

class IntegrityVerificationError(EvidenceError):
    """Raised when cryptographic hash verification fails or evidence cannot be verified."""

class InconsistentEvidenceError(EvidenceError):
    """Raised when source file changes during copy acquisition."""

class CorruptDatabaseError(ForenXError):
    """Raised when an inspected browser SQLite database is corrupt or malformed."""

class UnsupportedSchemaError(ForenXError):
    """Raised when a browser database is missing expected tables/columns."""

class ParseError(ForenXError):
    """Raised when artifact record extraction fails."""

class TimestampConversionError(ForenXError):
    """Raised when a raw browser timestamp cannot be safely normalized."""

class ValidationError(ForenXError):
    """Raised when known-answer validation dataset format or matching fails."""

class ReportGenerationError(ForenXError):
    """Raised when report compilation or export fails."""

class SecurityViolationError(ForenXError):
    """Raised when path traversal, size limit breach, or unsafe input is detected."""
