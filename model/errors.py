"""Domain errors raised by the model."""


class PIMError(Exception):
    """Base class for every error raised by the model."""


class ValidationError(PIMError):
    """A value supplied for a record field is not acceptable."""


class RecordNotFoundError(PIMError):
    """No record exists with the requested ID."""


class InvalidFieldError(PIMError):
    """The requested field does not belong to that record type."""
