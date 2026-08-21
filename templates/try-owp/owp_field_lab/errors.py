class FieldLabError(Exception):
    """Base domain error."""


class ValidationError(FieldLabError):
    pass


class QueueFull(FieldLabError):
    pass


class DuplicateSubmission(FieldLabError):
    pass


class NotFound(FieldLabError):
    pass


class Unauthorized(FieldLabError):
    pass


class InvalidTransition(FieldLabError):
    pass
