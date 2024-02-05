from __future__ import annotations
from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod
from . import environment
from . import errors

if TYPE_CHECKING:
    from .interpreter import Interpreter
    from .stmt import Function
    from .lexer import Token
    from .environment import Environment


class LoxCallable(ABC):
    @abstractmethod
    def call(self, interpreter: Interpreter, arguments: list[Any]):
        pass

    @abstractmethod
    def arity(self) -> int:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class LoxFunction(LoxCallable):
    declaration: Function
    closure: Environment
    __arity: int

    def __init__(self, declaration: Function, closure: Environment):
        self.declaration = declaration
        self.closure = closure
        self.__arity = len(declaration.params)

    def call(self, interpreter: Interpreter, arguments: list[Any]):
        env: Environment = environment.Environment(self.closure)

        for i, arg in enumerate(arguments):
            env.define(self.declaration.params[i], arg)

        try:
            interpreter.execute_block(self.declaration.body, env)
        except errors.LoxReturn as lox_return:
            return lox_return.value

    def arity(self):
        return self.__arity

    def __str__(self):
        return "<fun " + self.declaration.name.lexeme + ">"
