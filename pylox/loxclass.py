from __future__ import annotations
from typing import TYPE_CHECKING, Any
from . import callable
from . import errors

if TYPE_CHECKING:
    from . import interpreter
    from . import lexer


class LoxInstance:
    klass: LoxClass
    fields: dict[str, Any]

    def __init__(self, klass: LoxClass):
        self.klass = klass
        self.fields = {}

    def get(self, name: lexer.Token):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        raise errors.LoxRuntimeError(
                name,
                "Undefined property '" + name.lexeme + "'.")

    def set(self, name: lexer.Token, value: Any):
        self.fields[name.lexeme] = value
        return value

    def __str__(self):
        return "<instance " + self.klass.name + ">"


class LoxClass(callable.LoxCallable):
    name: str

    def __init__(self, name: str):
        self.name = name

    def call(self,
             interpreter: interpreter.Interpreter,
             arguments: list[lexer.Token]):
        return LoxInstance(self)

    def arity(self):
        return 0

    def __str__(self):
        return "<class " + self.name + ">"

