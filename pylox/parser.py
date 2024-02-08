"""
Provides the Parser class.

The grammar is defined by:

    program     -> declaration* EOF

    declaration -> classDecl
                   | varDecl
                   | funDecl
                   | statement

    classDecl   -> "class" IDENTIFIER "{" function* "}"
    varDecl     -> "var" IDENTIFIER ("=" expression)? ";"
    funDecl     -> "fun" function
    function    -> IDENTIFIER "(" parameters? ")" block

    parameters  -> IDENTIFIER ( "," IDENTIFIER )*

    statement   -> exprStmt
                   | forStmt
                   | ifStmt
                   | printStmt
                   | whileStmt
                   | block
                   | breakStmt
                   | returnStmt

    exprStmt    -> expression ";"
    forStmt     -> "for" "(" (varDecl | exprStmt | ";")
                   expression? ";" expression? ")" statement
    ifStmt      -> "if" "(" expression ")" statement
                   ("else" statement)?
    printStmt   -> "print" expression ";"
    whileStmt   -> "while" "(" expression ")" statement
    block       -> "{" declaration* "}"
    breakStmt   -> "break" ";"
    returnStmt  -> "return" expression? ";"

    expression  -> assignment
    assignment  -> ( call "." )? IDENTIFIER "=" assignment
                   | logical_or
    logical_or  -> logical_and ("or" logical_and)*
    logical_and -> ternery ("and" ternery)*
    ternery     -> equality ("?" equality ":" ternery)?
    equality    -> comparision ( ("!=" | "==") comparision )*
    comparision -> term ( ( ">" | ">=" | "<" | "<=" ) term )*
    term        -> factor ( ( "-" | "+" ) factor )*
    factor      -> unary ( ( "/"  | "*" ) unary )*
    unary       -> ( "!" | "-" ) unary | call
    call        -> primary ( "(" arguments? ")" | "." IDENTIFIER )*
    arguments   -> expression ( "," expression )*

    primary     -> NUMBER | STRING
                   | "true" | "false" | "nil"
                   | "(" expression ")"
                   | "this"
                   | IDENTIFIER
"""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Optional
from .lexer import Token, TokenType
from .expr import Expr, Binary, Unary, Grouping, Literal, Ternery, Variable, \
        Assign, Logical, Call, Function, Get, Set, This
from .stmt import Stmt, Expression, Print, Var, Block, If, While, Break, \
        FunDef, Return, Class

if TYPE_CHECKING:
    from .pylox import ErrorReporter

BINARY_OPERATOR_TYPES = [
        TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL, TokenType.GREATER,
        TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL,
        TokenType.MINUS, TokenType.PLUS, TokenType.SLASH, TokenType.STAR
    ]


class ParseError(Exception):
    """Raised if Parser enters panic mode"""
    pass


class Parser:
    """Class to parse the gramma defined above"""
    tokens: list[Token]
    current: int
    error_reporter: ErrorReporter
    nested_loops: int

    def __init__(self, tokens: list[Token], error_reporter: ErrorReporter):
        self.tokens = tokens
        self.current = 0
        self.error_reporter = error_reporter
        self.nested_loops = 0

    def parse(self) -> list[Stmt]:
        """
        Parse tokens and return a list of statements.
        If parser enters panic mode and has to synchronize discard
        this statement.
        """
        statements: list[Stmt] = []
        self.nested_loops = 0

        while not self.__is_at_end():
            stmt = self.__declaration()
            if stmt is not None:
                statements.append(stmt)
        return statements

    def __peek(self) -> Token:
        """Return current token"""
        return self.tokens[self.current]

    def __previous(self) -> Token:
        """Return previous token"""
        return self.tokens[self.current - 1]

    def __is_at_end(self) -> bool:
        """Return True if current token is EOF"""
        return self.__peek().type == TokenType.EOF

    def __advance(self) -> Token:
        """Return current token and increment current"""
        if not self.__is_at_end():
            self.current += 1
        return self.__previous()

    def __check(self, typ: TokenType):
        """Check if current token has type 'typ'"""
        if self.__is_at_end():
            return False
        return self.__peek().type == typ

    def __check_next(self, typ: TokenType):
        """Check if the next token has type 'typ'"""
        if self.__is_at_end():
            return False
        if self.tokens[self.current+1].type == TokenType.EOF:
            return False
        return self.tokens[self.current+1].type == typ

    def __match(self, types: list[TokenType]):
        """Check if current tokens type if one of types"""
        for typ in types:
            if self.__check(typ):
                self.__advance()
                return True
        return False

    ###########################################################################
    # Statement productions
    def __declaration(self) -> Optional[Stmt]:
        try:
            # Variable declaration
            if self.__match([TokenType.VAR]):
                return self.__var_decl()
            # Function declaration
            if self.__check(TokenType.FUN) \
                    and self.__check_next(TokenType.IDENTIFIER):
                # since token type is already checked consume will never
                # raise an error, so msg is irrelevant
                self.__consume(TokenType.FUN, "")
                return self.__function("function")
            if self.__match([TokenType.CLASS]):
                return self.__class_decl()
            return self.__statement()
        except ParseError:
            self.__synchronize()
            return None

    def __class_decl(self) -> Stmt:
        class_name = self.__consume(TokenType.IDENTIFIER,
                                    "Expect class name.")
        self.__consume(TokenType.LEFT_BRACE,
                       "Expect '{' before class body.")
        methods: list[FunDef] = []
        while not self.__check(TokenType.RIGHT_BRACE) \
                and not self.__is_at_end():
            methods.append(self.__function("method"))
        self.__consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")
        return Class(class_name, methods)

    def __var_decl(self) -> Stmt:
        var_name = self.__consume(TokenType.IDENTIFIER,
                                  "Expect variable name.")
        initializer: Optional[Expr] = None
        if self.__match([TokenType.EQUAL]):
            initializer = self.__expression()

        self.__consume(TokenType.SEMICOLON,
                       "Expect ';' after variable declaration.")
        return Var(var_name, initializer)

    def __function(self, kind: str) -> FunDef:
        """
        Helper function to produce function definition statement.
        Used for function or class methods.
        :param kind: 'function' or 'method'
        """
        fun_name = self.__consume(TokenType.IDENTIFIER,
                                  "Expect " + kind + " name.")

        function: Function = self.__function_body(kind)

        return FunDef(fun_name, function)

    def __function_body(self, kind: str) -> Function:
        """
        Helper function to produce the function body.
        """
        self.__consume(TokenType.LEFT_PAREN,
                       "Expect '(' after " + kind + " name.")
        parameters: list[Token] = []

        if not self.__check(TokenType.RIGHT_PAREN):
            parameters.append(self.__consume(
                    TokenType.IDENTIFIER,
                    "Expect parameter name.")
                )
            while self.__match([TokenType.COMMA]):
                parameters.append(self.__consume(
                    TokenType.IDENTIFIER,
                    "Expect parameter name.")
                )
            if len(parameters) > 255:
                self.__error(self.__peek(),
                             "Can't have more than 255 parameters")
        self.__consume(TokenType.RIGHT_PAREN,
                       "Expect ')' after parameter list.")

        self.__consume(TokenType.LEFT_BRACE,
                       "Expect '{' before " + kind + " body.")

        body: list[Stmt] = self.__block()

        return Function(parameters, body)

    def __statement(self) -> Stmt:
        if self.__match([TokenType.IF]):
            return self.__if_statement()

        if self.__match([TokenType.WHILE]):
            return self.__while_statement()

        if self.__match([TokenType.FOR]):
            return self.__for_statement()

        if self.__match([TokenType.PRINT]):
            return self.__print_statement()

        if self.__match([TokenType.LEFT_BRACE]):
            return Block(self.__block())

        if self.__match([TokenType.BREAK]):
            return self.__break_statement()

        if self.__match([TokenType.RETURN]):
            return self.__return_statement()

        return self.__expression_statement()

    def __if_statement(self) -> Stmt:
        self.__consume(TokenType.LEFT_PAREN,
                       "Expect '(' after 'if'.")
        condition: Expr = self.__expression()
        self.__consume(TokenType.RIGHT_PAREN,
                       "Expect ')' after 'if' condition.")

        then_branch: Stmt = self.__statement()
        else_branch: Optional[Stmt] = None

        if self.__match([TokenType.ELSE]):
            else_branch = self.__statement()

        return If(condition, then_branch, else_branch)

    def __while_statement(self) -> Stmt:
        self.__consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition: Expr = self.__expression()
        self.__consume(TokenType.RIGHT_PAREN, "Expect ')' after 'while'.")
        try:
            self.nested_loops += 1
            body: Stmt = self.__statement()

            return While(condition, body)
        finally:
            self.nested_loops -= 1

    def __for_statement(self) -> Stmt:
        self.__consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")
        initializer: Optional[Stmt] = None
        if self.__match([TokenType.SEMICOLON]):
            initializer = None
        elif self.__match([TokenType.VAR]):
            initializer = self.__var_decl()
        else:
            initializer = self.__expression_statement()

        condition: Optional[Expr] = None
        if not self.__check(TokenType.SEMICOLON):
            condition = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment: Optional[Expr] = None
        if not self.__check(TokenType.RIGHT_PAREN):
            increment = self.__expression()
        self.__consume(TokenType.RIGHT_PAREN,
                       "Expect ')' after for clause.")

        try:
            self.nested_loops += 1
            body: Stmt = self.__statement()

            # Build while loop
            if increment is not None:
                body = Block([body, Expression(increment)])

            if condition is None:
                condition = Literal(True)

            body = While(condition, body)

            if initializer is not None:
                body = Block([initializer, body])

            return body
        finally:
            self.nested_loops -= 1

    def __print_statement(self) -> Stmt:
        value: Expr = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Print(value)

    def __expression_statement(self) -> Stmt:
        value: Expr = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(value)

    def __block(self) -> list[Stmt]:
        statements: list[Stmt] = []
        while not self.__check(TokenType.RIGHT_BRACE) \
                and not self.__is_at_end():
            stmt = self.__declaration()
            if stmt is not None:
                statements.append(stmt)

        self.__consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def __break_statement(self) -> Stmt:
        if self.nested_loops == 0:
            raise self.__error(self.__previous(),
                               "'break' is only allowed inside loops")
        keyword: Token = self.__previous()
        self.__consume(TokenType.SEMICOLON,
                       "Expect ';' after 'break'.")
        return Break(keyword)

    def __return_statement(self) -> Stmt:
        keyword: Token = self.__previous()
        value: Optional[Expr] = None
        if not self.__check(TokenType.SEMICOLON):
            value = self.__expression()
        self.__consume(TokenType.SEMICOLON,
                       "Expect ';' after 'return'")
        return Return(keyword, value)

    ###########################################################################
    # Expression productions
    def __binary_expression(
            self,
            operand: Callable[[], Expr],
            operator_types: list[TokenType]) -> Expr:
        """Generic helper method, for all binary expression productions"""
        expr: Expr = operand()

        while self.__match(operator_types):
            operator: Token = self.__previous()
            right: Expr = operand()

            expr = Binary(expr, operator, right)

        return expr

    def __expression(self) -> Expr:
        return self.__assignment()

    def __assignment(self) -> Expr:
        expr: Expr = self.__or()

        if self.__match([TokenType.EQUAL]):
            equals: Token = self.__previous()
            value: Expr = self.__assignment()
            if isinstance(expr, Variable):
                var: Variable = expr
                return Assign(var.name, value)
            elif isinstance(expr, Get):
                get: Get = expr
                return Set(get.object, get.name, value)

            self.__error(equals, "Invalid assignment target.")
        return expr

    def __or(self) -> Expr:
        left: Expr = self.__and()

        while self.__match([TokenType.OR]):
            operator: Token = self.__previous()
            right: Expr = self.__and()

            left = Logical(left, operator, right)

        return left

    def __and(self) -> Expr:
        left: Expr = self.__ternery()

        while self.__match([TokenType.AND]):
            operator: Token = self.__previous()
            right: Expr = self.__ternery()

            left = Logical(left, operator, right)

        return left

    def __ternery(self) -> Expr:
        expr: Expr = self.__equality()

        if self.__match([TokenType.QUESTIONMARK]):
            then_expr: Expr = self.__ternery()

            if self.__match([TokenType.COLON]):
                else_expr: Expr = self.__ternery()

            else:
                self.__advance()
                self.error_reporter.report_parser(self.__peek().position,
                                                  "Expect ':'.")
                return self.__ternery()

            expr = Ternery(expr, then_expr, else_expr)

        return expr

    def __equality(self) -> Expr:
        return self.__binary_expression(
                self.__comparision,
                [TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL])

    def __comparision(self) -> Expr:
        return self.__binary_expression(
                self.__term,
                [
                    TokenType.LESS,
                    TokenType.LESS_EQUAL,
                    TokenType.GREATER,
                    TokenType.GREATER_EQUAL
                ])

    def __term(self) -> Expr:
        return self.__binary_expression(
                self.__factor,
                [TokenType.PLUS, TokenType.MINUS])

    def __factor(self) -> Expr:
        return self.__binary_expression(
                self.__unary,
                [TokenType.STAR, TokenType.SLASH])

    def __unary(self) -> Expr:

        if self.__match([TokenType.BANG, TokenType.MINUS]):
            operator: Token = self.__previous()
            right: Expr = self.__unary()
            return Unary(operator, right)

        return self.__call()

    def __call(self) -> Expr:
        expr: Expr = self.__primary()

        while True:
            if self.__match([TokenType.LEFT_PAREN]):
                expr = self.__finish_call(expr)
            elif self.__match([TokenType.DOT]):
                name: Token = self.__consume(
                        TokenType.IDENTIFIER,
                        "Expect property name after '.'.")
                expr = Get(expr, name)
            else:
                break
        return expr

    def __finish_call(self, callee: Expr) -> Expr:
        arguments: list[Expr] = []
        paren: Optional[Token] = None

        if not self.__check(TokenType.RIGHT_PAREN):
            arguments.append(self.__expression())

            while self.__match([TokenType.COMMA]):
                arguments.append(self.__expression())

                if len(arguments) > 255:
                    self.__error(self.__peek(),
                                 "Can't have more than 255 arguments.")
        paren = self.__consume(TokenType.RIGHT_PAREN,
                               "Expect ')' after arguments.")

        return Call(callee, paren, arguments)

    def __primary(self) -> Expr:
        if self.__match([TokenType.FALSE]):
            return Literal(False)
        if self.__match([TokenType.TRUE]):
            return Literal(True)

        if self.__match([TokenType.NIL]):
            return Literal(None)

        if self.__match([TokenType.NUMBER, TokenType.STRING]):
            return Literal(self.__previous().literal)

        if self.__match([TokenType.LEFT_PAREN]):
            expr: Expr = self.__expression()
            self.__consume(TokenType.RIGHT_PAREN,
                           "Expect ')' after expression.")
            return Grouping(expr)

        if self.__match([TokenType.IDENTIFIER]):
            return Variable(self.__previous())

        if self.__match([TokenType.FUN]):
            return self.__function_body("function")

        if self.__match([TokenType.THIS]):
            return This(self.__previous())

        # check for a faulty positioned binary operator
        if self.__match(BINARY_OPERATOR_TYPES):
            self.error_reporter.report_parser(self.__previous().position,
                                              "Left hand operand expected.")
            return self.__primary()

        raise self.__error(self.__peek(), "Expect expression.")

    def __error(self, token: Token, message: str) -> ParseError:
        """Report error with 'message' and return ParseError object"""
        self.error_reporter.report_parser(token.position, message)
        return ParseError()

    def __consume(self, typ: TokenType, message: str) -> Token:
        """
        If current token is of type 'typ' return it and increment current
        :param typ: token type to check for
        :param message: message for ErrorReporter is check fails
        :return: current token (if it has the type 'typ')
        :raiseis: ParseError if type check fails
        """
        if self.__check(typ):
            return self.__advance()

        raise self.__error(self.__peek(), message)

    def __synchronize(self):
        """Skip everything until next expression to resynchronize parser"""
        self.__advance()

        while not self.__is_at_end():
            if self.__previous().type == TokenType.SEMICOLON:
                return

            match self.__peek():
                case TokenType.CLASS:
                    return
                case TokenType.FUN:
                    return
                case TokenType.VAR:
                    return
                case TokenType.FOR:
                    return
                case TokenType.IF:
                    return
                case TokenType.WHILE:
                    return
                case TokenType.PRINT:
                    return
                case TokenType.RETURN:
                    return
            self.__advance()
