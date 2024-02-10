"""
All Lox built-in functions are defined here.
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING
from time import time_ns
import math
from . import callable
from . import loxclass
from . import lexer
from . import parser
from . import resolver
from .errors import LoxRuntimeError

if TYPE_CHECKING:
    from .interpreter import Interpreter


class LoxTime(callable.LoxCallable):
    def call(self, _: Interpreter, arguments: list[Any]):
        return time_ns()*1E-6

    def arity(self):
        return 0

    def __str__(self):
        return "<native-fun: time>"


class LoxInput(callable.LoxCallable):
    def call(self, _: Interpreter, arguments: list[Any]):
        return input()

    def arity(self):
        return 0

    def __str__(self):
        return "<native-fun: input>"


class LoxType(callable.LoxCallable):
    def call(self, _: Interpreter, arguments: list[Any]):
        arg = arguments[0]
        if isinstance(arg, str):
            return "string"
        if isinstance(arg, float):
            return "number"
        if isinstance(arg, callable.LoxFunction):
            return "fun"
        if isinstance(arg, loxclass.LoxClass):
            return "class"
        if isinstance(arg, loxclass.LoxInstance):
            return "instance"
        return "unknown"

    def arity(self):
        return 1

    def __str__(self):
        return "<native-fun: type>"

class LoxIsinstance(callable.LoxCallable):
    def call(self, _: Interpreter, arguments: list[Any]):
        inst = arguments[0]
        cls = arguments[1]
        if not isinstance(inst, loxclass.LoxInstance) \
                or not isinstance(cls, loxclass.LoxClass):
            return False

        return self.is_sub_class(inst.klass, cls)

    def is_sub_class(self, sub: loxclass.LoxClass, supi: loxclass.LoxClass):
        if sub == supi:
            return True
        for supersub in sub.superclasses:
            if self.is_sub_class(supersub, supi):
                return True
        return False

    def arity(self):
        return 2

    def __str__(self):
        return "<native-fun: isinstance>"


class LoxHasprop(callable.LoxCallable):
    def call(self, _: Interpreter, arguments: list[Any]):
        obj: loxclass.LoxInstance = arguments[0]
        prop: str = arguments[1]

        if not isinstance(obj, loxclass.LoxInstance):
            return False

        if not isinstance(prop, str):
            return False

        if prop in obj.fields:
            return True

        return False
    
    def arity(self):
        return 2

    def __str__(self):
        return "<native-fun: hasprop>"


class LoxTostring(callable.LoxCallable):
    def call(self, _: Interpreter, arguments: list[Any]):
        if not isinstance(arguments[0], float) \
                or not isinstance(arguments[1], float):
            return str(arguments[0])

        return f"{arguments[0]:.{int(arguments[1])}f}"

    def arity(self):
        return 2

    def __str__(self):
        return "<native-fun: tostring>"


class LoxTonumber(callable.LoxCallable):
    def call(self, _: Interpreter, arguments: list[Any]):
        try:
            return float(arguments[0])
        except ValueError:
            return None

    def arity(self):
        return 1

    def __str__(self):
        return "<native-fun: tonumber>"


class LoxRound(callable.LoxCallable):
    def call(self, _: Interpreter, arguments: list[Any]):
        if not isinstance(arguments[0], float) \
                or not isinstance(arguments[1], float):
            return None
        return round(arguments[0], int(arguments[1]))

    def arity(self):
        return 2

    def __str__(self):
        return "<native-fun: round>"


class LoxFloor(callable.LoxCallable):
    def call(self, _: Interpreter, arguments: list[Any]):
        if not isinstance(arguments[0], float): 
            return None
        return float(math.floor(arguments[0]))

    def arity(self):
        return 1

    def __str__(self):
        return "<native-fun: floor>"



class LoxInclude(callable.LoxCallable):
    def call(self, intpr: Interpreter, arguments: list[Any]):
        filename = arguments[0]
        dummy_token = lexer.Token(
                lexer.TokenType.FUN,
                "include",
                lexer.SourcePosition())
        try:
            file = open(filename)
        except FileNotFoundError:
            raise LoxRuntimeError(
                   dummy_token,
                   "File '" + filename + "' not found.")
        with file:
            source = file.read()
            orig_source = intpr.error_reporter.source

            intpr.error_reporter.update_source(source)

            lxer = lexer.Lexer(source, intpr.error_reporter)
            lxer.scan()

            prser = parser.Parser(lxer.tokens, intpr.error_reporter)
            statements = prser.parse()

            res = resolver.Resolver(intpr, intpr.error_reporter)
            res.resolve_stmt_list(statements)

            if intpr.error_reporter.had_error:
                raise LoxRuntimeError(
                        dummy_token,
                        "Errors found in included file '" + filename + "'.")

            intpr.interpret(statements)

            intpr.error_reporter.update_source(orig_source)

    def arity(self):
        return 1

    def __str__(self):
        return "<native-fun: include>"


FUNCTIONS = {
        "time": LoxTime(),
        "input": LoxInput(),
        "type": LoxType(),
        "isinstance": LoxIsinstance(),
        "hasprop": LoxHasprop(),
        "tostring": LoxTostring(),
        "tonumber": LoxTonumber(),
        "round": LoxRound(),
        "floor": LoxFloor(),
        "include": LoxInclude()
        }
