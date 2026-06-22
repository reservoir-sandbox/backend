class AppException(Exception):
    """Base application exception"""

    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


# Register Exceptions
class UserAlreadyExists(AppException):
    status_code = 409
    detail = "User already exists"


# Authenticate Exceptions
class InvalidCredentials(AppException):
    status_code = 401
    detail = "Invalid username or password"


class TokenExpiredError(AppException):
    status_code = 401
    detail = "Token has expired"


class TokenInvalidError(AppException):
    status_code = 401
    detail = "Token is invalid"


# User Exceptions
class UserNotFound(AppException):
    status_code = 404
    detail = "User not found"


class AccessDenied(AppException):
    status_code = 403
    detail = "Access Denied"


class FileTooLargeError(AppException):
    status_code = 413
    detail = "File size exceeds the maximum limit."


class InvalidELFError(AppException):
    status_code = 400
    detail = "Invalid file format. Only ELF files are allowed."
