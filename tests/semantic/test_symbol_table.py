import pytest

from src.semantic.symbol import Symbol
from src.semantic.symbol_table import Scope, SymbolTable, SemanticError, BUILTIN_NAMES
from src.semantic.type import IntType, FloatType, MatrixType


#--- Scope --

def test_scope_starts_empty_without_parent():
    scope = Scope()
    assert scope.parent is None
    assert scope.symbols == {}


def test_scope_define_and_resolve_local():
    scope = Scope()
    x = Symbol("x", IntType(), 1)
    scope.define(x)
    assert scope.resolve_local("x") is x


def test_scope_resolve_local_ignores_parent():
    outer = Scope()
    outer.define(Symbol("x", IntType(), 1))
    inner = Scope(parent=outer)
    assert inner.resolve_local("x") is None


def test_scope_resolve_walks_to_parent():
    outer = Scope()
    x = Symbol("x", IntType(), 1)
    outer.define(x)
    inner = Scope(parent=outer)
    assert inner.resolve("x") is x


def test_scope_resolve_walks_several_levels():
    a = Scope()
    x = Symbol("x", IntType(), 1)
    a.define(x)
    b = Scope(parent=a)
    c = Scope(parent=b)
    assert c.resolve("x") is x


def test_scope_resolve_missing_returns_none():
    assert Scope(parent=Scope()).resolve("nope") is None


# --- declare / lookup ---
def test_declare_then_lookup():
    table = SymbolTable()
    x = Symbol("x", IntType(), 1)
    table.declare(x)
    assert table.lookup("x") is x


def test_lookup_undeclared_returns_none():
    assert SymbolTable().lookup("y") is None


def test_lookup_keeps_type():
    table = SymbolTable()
    table.declare(Symbol("A", MatrixType(2, 3), 1))
    found = table.lookup("A")
    assert isinstance(found.type, MatrixType)
    assert (found.type.rows, found.type.cols) == (2, 3)


def test_names_are_case_sensitive():
    table = SymbolTable()
    table.declare(Symbol("a", IntType(), 1))
    table.declare(Symbol("A", FloatType(), 2))   
    assert isinstance(table.lookup("a").type, IntType)
    assert isinstance(table.lookup("A").type, FloatType)


def test_redeclare_in_same_scope_is_error():
    table = SymbolTable()
    table.declare(Symbol("x", IntType(), 1))
    with pytest.raises(SemanticError) as err:
        table.declare(Symbol("x", FloatType(), 2))
    assert err.value.line == 2


def test_redeclare_with_same_type_is_still_error():
    table = SymbolTable()
    table.declare(Symbol("x", IntType(), 1))
    with pytest.raises(SemanticError):
        table.declare(Symbol("x", IntType(), 2))


def test_redeclare_in_same_inner_scope_is_error():
    table = SymbolTable()
    table.enter_scope()
    table.declare(Symbol("x", IntType(), 2))
    with pytest.raises(SemanticError):
        table.declare(Symbol("x", IntType(), 3))


@pytest.mark.parametrize("name", sorted(BUILTIN_NAMES))
def test_declaring_builtin_name_is_error(name):
    with pytest.raises(SemanticError):
        SymbolTable().declare(Symbol(name, IntType(), 1))


def test_builtin_names_match_spec():
    assert BUILTIN_NAMES == {"rows", "cols", "determinant", "inverse", "toFloat", "toInt"}


#--- nested scopes and shadowing ---

def test_inner_scope_sees_outer_variable():
    table = SymbolTable()
    x = Symbol("x", IntType(), 1)
    table.declare(x)
    table.enter_scope()
    assert table.lookup("x") is x


def test_shadowing_in_inner_scope_is_legal():
    table = SymbolTable()
    table.declare(Symbol("x", IntType(), 1))
    table.enter_scope()
    table.declare(Symbol("x", FloatType(), 2))   
    assert isinstance(table.lookup("x").type, FloatType)


def test_shadow_disappears_after_exit():
    table = SymbolTable()
    outer_x = Symbol("x", IntType(), 1)
    table.declare(outer_x)
    table.enter_scope()
    table.declare(Symbol("x", FloatType(), 2))
    table.exit_scope()
    assert table.lookup("x") is outer_x


def test_inner_variable_not_visible_after_exit():
    table = SymbolTable()
    table.enter_scope()
    table.declare(Symbol("y", IntType(), 2))
    table.exit_scope()
    assert table.lookup("y") is None


def test_lookup_current_only_checks_current_scope():
    table = SymbolTable()
    table.declare(Symbol("x", IntType(), 1))
    table.enter_scope()
    assert table.lookup_current("x") is None
    assert table.lookup("x") is not None


def test_sibling_scopes_do_not_share_names():
    table = SymbolTable()
    table.enter_scope()
    table.declare(Symbol("y", IntType(), 1))
    table.exit_scope()
    table.enter_scope()
    table.declare(Symbol("y", IntType(), 2))       
    assert table.lookup("y").line == 2


def test_spec_example_walkthrough():
    table = SymbolTable()
    table.declare(Symbol("x", IntType(), 1))
    table.enter_scope()
    table.declare(Symbol("x", FloatType(), 3))
    table.declare(Symbol("y", IntType(), 4))
    assert isinstance(table.lookup("x").type, FloatType)
    table.exit_scope()
    assert isinstance(table.lookup("x").type, IntType)
    assert table.lookup("y") is None


def test_enter_and_exit_restore_global_scope():
    table = SymbolTable()
    table.enter_scope()
    table.enter_scope()
    table.exit_scope()
    table.exit_scope()
    assert table.current_scope is table.global_scope


def test_exit_global_scope_is_rejected():
    with pytest.raises(RuntimeError):
        SymbolTable().exit_scope()


#--- SemanticError ---

def test_semantic_error_message_has_line():
    err = SemanticError("bad thing", 7)
    assert err.line == 7
    assert "line 7" in str(err)
