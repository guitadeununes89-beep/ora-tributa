class ApplicationError(Exception):
    """Base error safe to translate into an HTTP problem response."""


class AuthenticationError(ApplicationError):
    pass


class AuthorizationError(ApplicationError):
    pass


class NotFoundError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass


class GovernanceError(ApplicationError):
    pass
