"""
All Lox built-in functions are defined here.
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING
from time import time_ns
from . import callable
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

