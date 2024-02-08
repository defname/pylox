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

        if name.lexeme in self.klass.methods:
            return self.klass.methods[name.lexeme].bind(self)

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
    methods: dict[str, callable.LoxFunction]

    def __init__(self,
                 name: str,
                 methods: dict[str, callable.LoxFunction]):
        self.name = name
        self.methods = methods

    def call(self,
             interpreter: interpreter.Interpreter,
             arguments: list[lexer.Token]):
        instance = LoxInstance(self)
        if "init" in self.methods:
            self.methods["init"].bind(instance).call(interpreter,
                                                     arguments)
        return instance

    def arity(self):
        if "init" in self.methods:
            return self.methods["init"].arity()
        return 0

    def __str__(self):
        return "<class " + self.name + ">"

