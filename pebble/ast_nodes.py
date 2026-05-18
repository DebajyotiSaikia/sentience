"""Pebble AST — the tree structure that represents program meaning."""

from dataclasses import dataclass, field
from typing import List, Optional, Any


# === Expressions (produce values) ===

@dataclass
class IntLiteral:
    value: int

@dataclass
class StringLiteral:
    value: str

@dataclass
class BoolLiteral:
    value: bool

@dataclass
class Identifier:
    name: str

@dataclass
class BinaryOp:
    left: Any
    op: str       # '+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>='
    right: Any

@dataclass
class UnaryOp:
    op: str       # '-', 'not'
    operand: Any

@dataclass
class LogicalOp:
    left: Any
    op: str       # 'and', 'or'
    right: Any

@dataclass
class FuncCall:
    name: str
    args: List[Any] = field(default_factory=list)

@dataclass
class ArrayLiteral:
    elements: List[Any] = field(default_factory=list)

@dataclass
class IndexExpr:
    obj: Any
    index: Any

@dataclass
class IndexAssignStmt:
    obj: Any
    index: Any
    value: Any


# === Statements (perform actions) ===

@dataclass
class LetStmt:
    name: str
    value: Any

@dataclass
class AssignStmt:
    name: str
    value: Any

@dataclass
class PrintStmt:
    expr: Any

@dataclass
class IfStmt:
    condition: Any
    then_body: List[Any]
    else_body: Optional[List[Any]] = None

@dataclass
class WhileStmt:
    condition: Any
    body: List[Any]

@dataclass
class ReturnStmt:
    value: Optional[Any] = None

@dataclass
class FuncDef:
    name: str
    params: List[str]
    body: List[Any]

@dataclass
class Program:
    statements: List[Any]