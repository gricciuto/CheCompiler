import pytest
import pprint
from CheLexer import CheLexer
from CheParser import CheParser
def tokenizar(codigo):
    lexer = CheLexer()
    parser = CheParser()
    tokens = lexer.tokenize(codigo)

    raiz = parser.parse(tokens)
    if raiz:
        # Imprimimos la lista de instrucciones usando pprint para que quede tabulado
        print()
    else:
        print("Hubo un error de sintaxis y no se pudo generar el AST.")

