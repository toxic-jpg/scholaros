"""Custom exceptions for ScholarOS."""


class ScholarOSException(Exception):
    """Base exception for all ScholarOS errors."""


class ValidationError(ScholarOSException):
    """Input validation failed."""


class StorageError(ScholarOSException):
    """Database or storage operation failed."""


class GPACalculationError(ScholarOSException):
    """GPA computation encountered an error."""


class ImportParseError(ScholarOSException):
    """Data import failed."""


class ExportError(ScholarOSException):
    """Data export failed."""