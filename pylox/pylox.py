import sys
from .lexer import SourcePosition, Lexer


class ErrorReporter:
    """Provide reporting functions for different parts of the compiler."""
    def __init__(self, source: str):
        self.source: str = source
    
    def __report(self, position: SourcePosition, typ: str, message: str):
        line_start = self.source[:position.start].rfind("\n")
        if line_start == -1:
            line_start = 0
        line_end = self.source[line_start+1:].find("\n")
        if line_end == -1:
            line_end = len(self.source)
        else:
            line_end += line_start + 1
        line = self.source[line_start+1:line_end]
        
        position_indicator = " "*(position.start-line_start-1)+"^"*(position.current-position.start)

        print(f'{typ} error at {position}: {message}')
        print(line)
        print(position_indicator)
    
    def report_lex(self, position: SourcePosition, message: str):
        """Reporting function to be used by the Lexer"""
        self.__report(position, "Lexing", message)


class PyLox:
    def __init__(self):
        self.had_error = False
    
    def run_file(self, filename: str):
        try:
            file = open(filename)
        except FileNotFoundError:
            return 66
        else:
            with file:
                source = file.read()
                self.run(source)
                if self.had_error:
                    return 65
                return 0

    def run_prompt(self):
        while True:
            try:
                line = input("> ")
                self.run(line)
                self.had_error = 0
            except EOFError:
                return 0
        return 0

    def run(self, source: str):
        error_reporter = ErrorReporter(source)
        lexer = Lexer(source, error_reporter)
        lexer.scan()
        for token in lexer.tokens:
            print(token)