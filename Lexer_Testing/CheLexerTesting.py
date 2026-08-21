import pytest
from CheLexer import CheLexer

def tokenizar(codigo):
    lexer = CheLexer()
    return list(lexer.tokenize(codigo))

def test_tokens_basicos():
    tokens = tokenizar("comienza entero a le asigno 10")
    tipos = [t.type for t in tokens]
    assert tipos == ["BEGIN", "TIPO", "ID", "ASIGNACION", "NUMERO"]

def test_tokens_operaciones():
    tokens = tokenizar("a mas b multiplicado c")
    tipos = [t.type for t in tokens]
    assert tipos == ["ID", "MAS", "ID", "POR", "ID"]

def test_tokens_condicion():
    tokens = tokenizar("si a mayor 10 entonces")
    tipos = [t.type for t in tokens]
    assert tipos == ["IF", "ID", "MAYOR", "NUMERO", "THEN"]

def test_tokens_imprimir():
    tokens = tokenizar("imprimo a")
    tipos = [t.type for t in tokens]
    assert tipos == ["IMPRIMIR", "ID"]

def test_tokens_cadena():
    tokens = tokenizar('"hola mundo"')
    tipos = [t.type for t in tokens]
    assert tipos == ["CADENA"]

def test_tokens_ignora_espacios():
    tokens = tokenizar("   a   mas   b   ")
    tipos = [t.type for t in tokens]
    assert tipos == ["ID", "MAS", "ID"]

def test_tokens_ignora_saltos():
    tokens = tokenizar("a\n\nmas\n\nb")
    tipos = [t.type for t in tokens]
    assert tipos == ["ID", "MAS", "ID"]

def test_tokens_error():
    with pytest.raises(SyntaxError):
        tokenizar("a @ b")
