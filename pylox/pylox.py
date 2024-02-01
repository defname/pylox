"""
Main module containing the PyLox class which puts together the whole
interpreter.
"""
from __future__ import annotations
from typing import Union
from .lexer import SourcePosition, Lexer
from .parser import Parser
from .ast_printer import AstPrinter
from .stmt import Stmt
from .interpreter import Interpreter


class ErrorReporter:
    """
    Provide error reporting functions for different parts of the compiler.
    """
    source: str
    had_error: bool
    had_runtime_error: bool

    def __init__(self, source: str = ""):
        self.source = source
        self.had_error = False
        self.had_runtime_error = False

    def update_source(self, source: str):
        self.source = source

    def reset_errors(self):
        self.had_error = False
        self.had_runtime_error = False

    def __report(self, position: SourcePosition, typ: str, message: str):
        """Print error message and set had_error to True"""
        self.had_error = True

        line_start = self.source[:position.start].rfind("\n")
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1  # skip \n
        line_end = self.source[line_start+1:].find("\n")
        if line_end == -1:
            line_end = len(self.source)
        else:
            line_end += line_start + 1
        line = self.source[line_start:line_end]

        position_indicator = " "*(position.start-line_start) + \
            "^"*(position.current-position.start)

        print(f'{typ} error at {position}: {message}')
        print(line)
        print(position_indicator)

    def report_lex(self, position: SourcePosition, message: str):
        """Reporting method to be used by the Lexer"""
        self.__report(position, "Lexing", message)

    def report_parser(self, position: SourcePosition, message: str):
        """Reporting method to be used by the Parser"""
        self.__report(position, "Parsing", message)

    def report_runtime(self, position: SourcePosition, message: str):
        self.had_runtime_error = True
        self.__report(position, "Runtime", message)


class PyLox:
    """
    PyLox interpreter.

    Combine the Lexer, etc. to a working interpreter.
    """
    error_reporter: ErrorReporter
    interpreter: Interpreter

    def __init__(self):
        self.error_reporter = ErrorReporter()
        self.interpreter = Interpreter(self.error_reporter)

    def run_file(self, filename: str):
        """Read the specified file and run it."""
        try:
            file = open(filename)
        except FileNotFoundError:
            return 66
        with file:
            source = file.read()
            return self.run(source)

    def run_prompt(self):
        """Read from stdin and run the input until EOF."""
        while True:
            try:
                line = input("> ")
                self.run(line)
                self.error_reporter.reset_errors()
            except EOFError:
                return 0
        return 0

    def run(self, source: str):
        """Run the given sourcecode."""
        self.error_reporter.update_source(source)

        lexer = Lexer(source, self.error_reporter)
        lexer.scan()

        parser = Parser(lexer.tokens, self.error_reporter)
        statements: list[Stmt] = parser.parse()

        if self.error_reporter.had_error:
            return 65

        self.interpreter.interpret(statements)

        if self.error_reporter.had_runtime_error:
            return 70

        return 0
