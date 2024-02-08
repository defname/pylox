from __future__ import annotations
from typing import Any, TYPE_CHECKING, Optional
from abc import ABC, abstractmethod
from . import environment
from . import errors

if TYPE_CHECKING:
    from .interpreter import Interpreter
    from .expr import Function
    from .lexer import Token
    from .environment import Environment
    from .loxclass import LoxInstance


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
    name: Optional[str]
    declaration: Function
    closure: Optional[Environment]
    is_initializer: bool
    __arity: int

    def __init__(self,
                 name: Optional[str],
                 declaration: Function,
                 closure: Optional[Environment],
                 is_initializer: bool = False):
        self.name = name
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer
        self.__arity = len(declaration.params)

    def call(self, interpreter: Interpreter, arguments: list[Any]):
        env: Environment = environment.Environment(self.closure)

        for i, arg in enumerate(arguments):
            env.define(self.declaration.params[i], arg)

        try:
            interpreter.execute_block(self.declaration.body, env)
        except errors.LoxReturn as lox_return:
            if self.is_initializer:
                if self.closure is None:
                    print("SHOULD NOT HAPPEN! in callable.py")
                    return
                return self.closure.get_at(0, 0, "this")
            return lox_return.value

        if self.is_initializer:
            if self.closure is None:
                print("SHOULD NOT HAPPEN! in callable.py")
                return
            return self.closure.get_at(0, 0, "this")

    def arity(self):
        return self.__arity

    def bind(self, instance: LoxInstance):
        env = environment.Environment(self.closure)
        env.define(None, instance)  # name is defined in resolver class
        return LoxFunction(self.name,
                           self.declaration,
                           env,
                           self.is_initializer)

    def __str__(self):
        if self.name is not None:
            return "<fun " + self.name + ">"
        return "<fun>"
