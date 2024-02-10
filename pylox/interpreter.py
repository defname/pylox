"""Implements Interpreter"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union
from .expr import Expr, Literal, Grouping, Binary, Unary, Ternery, Variable, \
        Assign, Logical, Call, Function, Get, Set, This, Super
from .stmt import Stmt, Expression, Print, Var, Block, If, While, Break, \
        FunDef, Return, Class
from .lexer import TokenType, Token
from .callable import LoxCallable, LoxFunction
from .loxclass import LoxClass
from .environment import Environment, UNINITIALIZED
from . import errors
from . import builtin
from . import loxclass

if TYPE_CHECKING:
    from .pylox import ErrorReporter


class GlobalEnvironment:
    values: dict[str, Any]

    def __init__(self):
        self.values = {}

        for name, lox_function in builtin.FUNCTIONS.items():
            self.define(Token(None, name, None),
                        lox_function)

    def define(self, name: Token, value: Any = UNINITIALIZED):
        self.values[name.lexeme] = value

    def get(self, name: Token):
        """
        Return the value of the variable with 'name' if it is defined.
        Raise RuntimeError otherwise.
        """
        if name.lexeme in self.values:
            if self.values[name.lexeme] is UNINITIALIZED:
                raise errors.LoxRuntimeError(
                        name,
                        "Uninitialized variable '" + name.lexeme + "'.")
            return self.values[name.lexeme]
        raise errors.LoxRuntimeError(
                name,
                "Undefined variable '" + name.lexeme + "'.")

    def assign(self, name: Token, value: Any):
        """
        Assign a value to a variable.
        Raise RuntimeError if the variable doesn't exist.
        """
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        raise errors.LoxRuntimeError(
                name,
                "Undefined variable '" + name.lexeme + "'.")


class Interpreter(Expr.Visitor, Stmt.Visitor):
    error_reporter: ErrorReporter
    global_environment: GlobalEnvironment
    environment: Optional[Environment]
    local_definitions: dict[int, Tuple[int, int]]  # Tuple[depth, index]

    def __init__(self, error_reporter: ErrorReporter):
        self.error_reporter = error_reporter
        self.global_environment = GlobalEnvironment()
        self.environment = None
        self.local_definitions = {}

    def interpret(self, statements: list[Stmt]):
        try:
            for stmt in statements:
                self.execute(stmt)
        except errors.LoxRuntimeError as error:
            self.error_reporter.report_runtime(error.token.position,
                                               error.message)

    def execute(self, stmt: Stmt):
        stmt.accept(self)

    def execute_block(self,
                      statements: list[Stmt],
                      environment: Environment):
        previous_environment: Optional[Environment] = self.environment

        try:
            self.environment = environment

            for stmnt in statements:
                self.execute(stmnt)
        finally:
            self.environment = previous_environment

    def resolve(self, node: Union[Expr, Stmt], depth: int, index: int):
        self.local_definitions[id(node)] = (depth, index)

    def __lookup_variable(self, name: Token, expr: Expr):
        distance, index = self.local_definitions.get(id(expr), (None, None))
        if distance is not None \
                and index is not None \
                and self.environment is not None:
            return self.environment.get_at(distance, index, name.lexeme)
        return self.global_environment.get(name)

    def __assign_variable(self,
                          name: Token,
                          expr: Union[Expr, Stmt],
                          value: Any):
        distance, index = self.local_definitions.get(id(expr), (None, None))
        if distance is not None \
                and index is not None \
                and self.environment is not None:
            return self.environment.assign_at(
                    distance, index, name, value
                )
        return self.global_environment.assign(name, value)


    def stringify(self, value: Any):
        if value is None:
            return "nil"
        return str(value)

    def __check_number_operand(self, operator: Token, operand: object):
        if isinstance(operand, float):
            return
        raise errors.LoxRuntimeError(operator, "Operand must be a number.")

    def __check_number_operands(self,
                                operator: Token,
                                left: object,
                                right: object):
        if isinstance(left, float) and isinstance(right, float):
            return
        raise errors.LoxRuntimeError(operator, "Both operands mus be numbers.")

    def __is_truthy(self, operand: object):
        if operand is None or (isinstance(operand, bool) and not operand):
            return False
        return True

    def __is_equal(self, left: object, right: object):
        return left == right

    def evaluate(self, expr: Expr):
        return expr.accept(self)

    ###########################################################################
    # Expr.Visitor
    def visit_literal_expr(self, expr: Literal):
        return expr.value

    def visit_grouping_expr(self, expr: Grouping):
        return self.evaluate(expr.expression)

    def visit_call_expr(self, expr: Call):
        callee = self.evaluate(expr.callee)
        arguments: list = []
        for arg in expr.arguments:
            arguments.append(self.evaluate(arg))

        if not isinstance(callee, LoxCallable):
            raise errors.LoxRuntimeError(
                    expr.paren,
                    "Can only call functions and classes.")

        function: LoxCallable = callee
        if len(arguments) != function.arity():
            raise errors.LoxRuntimeError(
                    expr.paren,
                    "Expected " + str(function.arity())
                    + " arguments, but got "
                    + str(len(arguments)) + "."
                )

        return function.call(self, arguments)

    def visit_get_expr(self, expr: Get):
        obj: Any = self.evaluate(expr.object)
        if isinstance(obj, loxclass.LoxInstance):
            return obj.get(expr.name)

        raise errors.LoxRuntimeError(
                expr.name,
                "Only class instances have properties.")

    def visit_set_expr(self, expr: Set):
        obj: Any = self.evaluate(expr.object)
        if isinstance(obj, loxclass.LoxInstance):
            value = self.evaluate(expr.value)
            return obj.set(expr.name, value)

        raise errors.LoxRuntimeError(
                expr.name,
                "Only instances of classes have fields.")

    def visit_function_expr(self, expr: Function):
        return LoxFunction(None, expr, self.environment)

    def visit_unary_expr(self, expr: Unary):
        right: Any = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.MINUS:
                self.__check_number_operand(expr.operator, right)
                return -float(right)
            case TokenType.BANG:
                return not self.__is_truthy(right)

        return None

    def visit_binary_expr(self, expr: Binary):
        left: Any = self.evaluate(expr.left)
        right: Any = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.EQUAL_EQUAL:
                return self.__is_equal(left, right)
            case TokenType.BANG_EQUAL:
                return not self.__is_equal(left, right)
            case TokenType.GREATER:
                self.__check_number_operands(expr.operator, left, right)
                return left > right
            case TokenType.GREATER_EQUAL:
                self.__check_number_operands(expr.operator, left, right)
                return left >= right
            case TokenType.LESS:
                self.__check_number_operands(expr.operator, left, right)
                return left < right
            case TokenType.LESS_EQUAL:
                self.__check_number_operands(expr.operator, left, right)
                return left <= right
            case TokenType.PLUS:
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                if isinstance(left, float) and isinstance(right, float):
                    return left + right
                # implicit str conversion
                if isinstance(left, float) and isinstance(right, str):
                    try:
                        return str(left) + right
                    except ValueError:
                        raise errors.LoxRuntimeError(
                                expr.operator,
                                "Cannot convert '"+str(left)+"' to string.")
                if isinstance(left, str) and isinstance(right, float):
                    try:
                        return left + str(right)
                    except ValueError:
                        raise errors.LoxRuntimeError(
                                expr.operator,
                                "Cannot convert '"+str(right)+"' to str.")
                raise errors.LoxRuntimeError(
                        expr.operator,
                        "Both operands have to be strings or numbers."
                    )
            case TokenType.MINUS:
                self.__check_number_operands(expr.operator, left, right)
                return float(left) - float(right)
            case TokenType.STAR:
                self.__check_number_operands(expr.operator, left, right)
                return float(left) * float(right)
            case TokenType.SLASH:
                self.__check_number_operands(expr.operator, left, right)
                if right == 0:
                    raise errors.LoxRuntimeError(
                            expr.operator,
                            "Do not divide by zero!")
                return float(left) / float(right)

    def visit_ternery_expr(self, expr: Ternery):
        condition = self.evaluate(expr.condition)
        if self.__is_truthy(condition):
            return self.evaluate(expr.then_expr)
        return self.evaluate(expr.else_expr)

    def visit_variable_expr(self, expr: Variable):
        return self.__lookup_variable(expr.name, expr)

    def visit_assign_expr(self, expr: Assign):
        value = self.evaluate(expr.value)
        self.__assign_variable(expr.name, expr, value)
        return value

    def visit_logical_expr(self, expr: Logical):
        left = self.evaluate(expr.left)
        if expr.operator.type == TokenType.OR:
            if self.__is_truthy(left):
                return left
        else:
            if not self.__is_truthy(left):
                return left
        return self.evaluate(expr.right)

    def visit_this_expr(self, expr: This):
        return self.__lookup_variable(expr.keyword, expr)
    
    def visit_super_expr(self, expr: Super):
        distance, index = self.local_definitions.get(id(expr), (None, None))
        if self.environment is None or distance is None or index is None:
            # Cannot happen, since it is ensured, that 'super' is only used
            # in subclasses
            raise RuntimeError("Impossible situation")
        mapping: dict[str, int] = self.environment.get_at(distance, 0, "super")
        this: LoxClass = self.environment.get_at(distance-1, 0, "this")
        superclass_index: int = 0
        if expr.superclass is not None:
            i = mapping.get(expr.superclass.lexeme, None)
            if i is None:
                raise errors.LoxRuntimeError(
                        expr.superclass,
                        "'" + expr.superclass.lexeme + "' is not a superclass "
                        + "of '" + this.klass.name + "'.")
            superclass_index = i
        superclasses: list[LoxClass] = this.klass.superclasses
        method: Optional[LoxFunction] = \
            superclasses[superclass_index].find_method(expr.method)

        if method is None:
            raise errors.LoxRuntimeError(
                    expr.method,
                    "Class '" + superclasses[superclass_index].name
                    + "' has no method '"
                    + expr.method.lexeme + "'.")

        return method.bind(this)

    ###########################################################################
    # Stmt.Visitor
    def visit_expression_stmt(self, stmt: Expression):
        self.evaluate(stmt.expression)

    def visit_if_stmt(self, stmt: If):
        condition = self.evaluate(stmt.condition)
        if self.__is_truthy(condition):
            self.execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self.execute(stmt.else_branch)

    def visit_while_stmt(self, stmt: While):
        try:
            while self.__is_truthy(self.evaluate(stmt.condition)):
                self.execute(stmt.body)
        except errors.LoxBreak:
            pass

    def visit_print_stmt(self, stmt: Print):
        print(self.stringify(self.evaluate(stmt.expression)))

    def visit_var_stmt(self, stmt: Var):
        value = UNINITIALIZED
        if stmt.initializer is not None:
            value = self.evaluate(stmt.initializer)
        if self.environment is not None:
            self.environment.define(stmt.name, value)
        else:
            self.global_environment.define(stmt.name, value)

    def visit_fundef_stmt(self, stmt: FunDef):
        function: LoxFunction = LoxFunction(
                stmt.name.lexeme,
                stmt.function,
                self.environment)
        if self.environment is not None:
            self.environment.define(stmt.name, function)
        else:
            self.global_environment.define(stmt.name, function)

    def visit_block_stmt(self, stmt: Block):
        self.execute_block(stmt.statements,
                           Environment(self.environment))

    def visit_break_stmt(self, stmt: Break):
        raise errors.LoxBreak()

    def visit_return_stmt(self, stmt: Return):
        if stmt.value is None:
            raise errors.LoxReturn(None)
        value = self.evaluate(stmt.value)
        raise errors.LoxReturn(value)

    def visit_class_stmt(self, klass: Class):
        superclasses: list[LoxClass] = []
        superclasses_mapping: dict[str, int] = {}
        for pos, superclass_name in enumerate(klass.superclasses):
            superclass = self.evaluate(superclass_name)
            if not isinstance(superclass, LoxClass):
                raise errors.LoxRuntimeError(
                        superclass_name.name,
                        "'" + superclass_name.name.lexeme + "' is not "
                        + "a class. Can only inherit from class.")
            superclasses.append(superclass)
            superclasses_mapping[superclass_name.name.lexeme] = pos

        if self.environment is not None:
            self.environment.define(klass.name)
        else:
            self.global_environment.define(klass.name)

        if len(klass.superclasses) > 0:
            # create environment for super
            self.environment = Environment(self.environment)
            # define 'super' (name is not needed since Resolver handles it)
            # the actual superclass is found by vist_super_expe by
            # taking the correct entry fom this's klass superclasses list
            self.environment.define(None, superclasses_mapping)

        methods: dict[str, LoxFunction] = {}
        for method in klass.methods:
            is_initializer = method.name.lexeme == "init"
            function: LoxFunction = LoxFunction(
                    method.name.lexeme,
                    method.function,
                    self.environment,
                    is_initializer)
            methods[method.name.lexeme] = function

        static_methods: dict[str, LoxFunction] = {}
        for static_method in klass.static_methods:
            sfunction: LoxFunction = LoxFunction(
                    static_method.name.lexeme,
                    static_method.function,
                    self.environment)
            static_methods[static_method.name.lexeme] = sfunction

        if len(klass.superclasses) > 0:
            if self.environment is None:
                # it's created above...
                raise RuntimeError("This cannot happen!")
            # leave environment for 'super'
            self.environment = self.environment.enclosing

        k = LoxClass(klass.name.lexeme, superclasses, methods, static_methods)

        self.__assign_variable(klass.name, klass, k)
