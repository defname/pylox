from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING
from . import errors
from . import lexer

if TYPE_CHECKING:
    from .lexer import Token
    from .errors import LoxRuntimeError


UNINITIALIZED = object()


class Environment:
    """An environment holding variables and their values"""
    values_array: list[Any]
    enclosing: Optional[Environment]

    def __init__(self, enclosing: Optional[Environment] = None):
        self.values_array = []
        self.enclosing = enclosing

    def define(self, name: Optional[Token], value: Any = UNINITIALIZED):
        """Define a new variable and initialize it with 'value'"""
        self.values_array.append(value)

    def get_at(self, distance: int, index: int, name: str):
        return self.ancestor(distance).values_array[index]

    def ancestor(self, distance: int) -> Environment:
        environment: Environment = self
        for _ in range(distance):
            if environment.enclosing is None:
                raise errors.LoxRuntimeError(
                        lexer.Token(lexer.TokenType.NIL,
                                    "",
                                    lexer.SourcePosition()),
                        "This should not happen!! (inside Environment)")
            environment = environment.enclosing

        return environment

    def assign_at(self, distance: int, index: int, name: Token, value: Any):
        self.ancestor(distance).values_array[index] = value
