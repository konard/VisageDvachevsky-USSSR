"""
Custom application exceptions
"""


class ApplicationError(Exception):
    """Base application error"""

    pass


class LeaderNotFoundError(ApplicationError):
    """Leader not found error"""

    def __init__(self, leader_id: int):
        self.leader_id = leader_id
        super().__init__(f"Leader with id {leader_id} not found")


class UserNotFoundError(ApplicationError):
    """User not found error"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User with id {user_id} not found")


class UserAlreadyExistsError(ApplicationError):
    """User already exists error"""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email {email} already exists")


class InvalidCredentialsError(ApplicationError):
    """Invalid credentials error"""

    def __init__(self):
        super().__init__("Invalid email or password")


class UnauthorizedError(ApplicationError):
    """Unauthorized error"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class ForbiddenError(ApplicationError):
    """Forbidden error"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)
