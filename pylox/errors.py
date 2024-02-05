from typing import Any
from .lexer import Token


class LoxRuntimeError(Exception):
    """Thrown when an error occures during runtime"""
    def __init__(self,
                 token: Token,
                 message: str,
                 *args: object):
        super().__init__(message, args)
        self.token = token
        self.message = message


class LoxReturn(Exception):
    """Thrown by return statements"""
    def __init__(self, value: Any = None):
        super().__init__()
        self.value = value


class LoxBreak(Exception):
    """Thrown by break statements"""
    def __init__(self):
        super().__init__()
