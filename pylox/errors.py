from typing import Any
from .lexer import Token
from . import environment

class LoxRuntimeError(Exception):
    def __init__(self,
                 token: Token,
                 message: str,
                 *args: object):
        super().__init__(message, args)
        self.token = token
        self.message = message


class LoxReturn(Exception):
    def __init__(self, value: Any = None):
        super().__init__()
        self.value = value


