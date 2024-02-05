from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING
from . import errors

if TYPE_CHECKING:
    from . import lexer
    from .lexer import Token
    from .errors import LoxRuntimeError


UNINITIALIZED = object()


class Environment:
    """An environment holding variables and their values"""
    values: dict[str, Any]
    enclosing: Optional[Environment]

    def __init__(self, enclosing: Optional[Environment] = None):
        self.values = {}
        self.enclosing = enclosing

    def define(self, name: Token, value: Any = UNINITIALIZED):
        """Define a new variable and initialize it with 'value'"""
        self.values[name.lexeme] = value

    def get(self, name: Token):
        """
        Return the value of the variable with 'name' if it is defined.
        Raise RuntimeError otherwise.
        """
        if name.lexeme in self.values:
            if self.values[name.lexeme] is UNINITIALIZED:
                raise errors.LoxRuntimeError(
                        name,
                        "Uninitialized variable '" + name.lexeme + "'.")
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise RuntimeError(name, "Undefined variable '" + name.lexeme + "'.")

    def assign(self, name: Token, value: Any):
        """
        Assign a value to a variable.
        Raise RuntimeError if the variable doesn't exist.
        """
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise errors.LoxRuntimeError(
                name,
                "Undefined variable '" + name.lexeme + "'.")



