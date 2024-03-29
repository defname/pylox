from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
from . import callable
from . import errors
from . import lexer

if TYPE_CHECKING:
    from . import interpreter


class LoxInstance:
    klass: LoxClass
    fields: dict[str, Any]

    def __init__(self, klass: LoxClass):
        self.klass = klass
        self.fields = {}

    def get(self, name: lexer.Token):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method: Optional[callable.LoxFunction] = self.klass.find_method(name)
        if method is not None:
            return method.bind(self)

        raise errors.LoxRuntimeError(
                name,
                "Undefined property '" + name.lexeme + "'.")

    def set(self, name: lexer.Token, value: Any):
        self.fields[name.lexeme] = value
        return value

    def __str__(self):
        return "<instance " + self.klass.name + ">"


class LoxClass(callable.LoxCallable, LoxInstance):
    name: str
    token: lexer.Token
    superclasses: list[LoxClass]
    methods: dict[str, callable.LoxFunction]
    fields: dict[str, callable.LoxFunction]  # holds the static methods
    initializer: Optional[callable.LoxFunction]

    def __init__(self,
                 name: lexer.Token,
                 superclasses: list[LoxClass],
                 methods: dict[str, callable.LoxFunction],
                 static_methods: dict[str, callable.LoxFunction]):
        LoxInstance.__init__(self, self)
        self.name = name.lexeme
        self.token = name
        self.superclasses = superclasses
        self.methods = methods
        self.fields = static_methods
        """
        self.initializer = self.find_method(
                lexer.Token(lexer.TokenType.IDENTIFIER,
                            "init",
                            lexer.SourcePosition())
                )
        """
        self.initializer = None
        if "init" in self.methods:
            self.initializer = self.methods["init"]

    def call(self,
             interpreter: interpreter.Interpreter,
             arguments: list[lexer.Token]):
        instance = LoxInstance(self)
        if self.initializer is not None:
            self.initializer.bind(instance).call(interpreter,
                                                 arguments)
        else:  # try to call all superclass initializers
            for superclass in self.superclasses:
                if superclass.initializer is None:
                    continue
                if superclass.initializer.arity() != len(arguments):
                    raise errors.LoxRuntimeError(
                            self.token,
                            "Cannot initialize because the number of "
                            + "arguments passed to the initializer "
                            + "doesn't fit the number of parameters of "
                            + "the initializer of '" + superclass.name + "'. "
                            + "Consider adding an initializer method.")
                superclass.initializer \
                    .bind(instance) \
                    .call(interpreter, arguments)
        return instance

    def arity(self):
        if self.initializer is not None:
            return self.initializer.arity()
        return 0

    def get(self, name: lexer.Token, dont_raise_error: bool = False):
        """Find static method"""
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        static_method: Optional[callable.LoxFunction] = None
        for superclass in self.superclasses:
            static_method = superclass.get(name, True)
            if static_method is not None:
                return static_method

        if dont_raise_error:
            return None

        raise errors.LoxRuntimeError(
                name,
                "Class " + self.name + " has no static method '"
                + name.lexeme + "'.")

    def find_method(self, name: lexer.Token) -> Optional[callable.LoxFunction]:
        if name.lexeme in self.methods:
            return self.methods[name.lexeme]

        for superclass in self.superclasses:
            method = superclass.find_method(name)
            if method is not None:
                return method

        return None

    def set(self, name: lexer.Token, value: Any):
        raise errors.LoxRuntimeError(
                name,
                "Properties can only be defined on objects not on classes.")

    def __str__(self):
        return "<class " + self.name + ">"

