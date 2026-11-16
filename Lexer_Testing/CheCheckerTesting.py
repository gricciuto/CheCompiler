
import unittest

from CheChecker import CheckProgramVisitor, SemanticError, check_program
from CheNodosAST import *


class CheCheckerTester(unittest.TestCase):

    def setUp(self):
        self.checker = CheckProgramVisitor()

    # =====================================================
    # Declaraciones
    # =====================================================
    def valor(self, valor):
        return Valor(valor, None)

    def variable(self, nombre):
        return Variable(nombre, 1)
    def test_declaracion_valida(self):
        nodo = Declaracion("entero", ["a", "b"])
        self.checker.visit(nodo)

        self.assertIn("a", self.checker.symbols)
        self.assertIn("b", self.checker.symbols)
        self.assertEqual(len(self.checker.errores), 0)

    def test_declaracion_tipo_invalido(self):
        nodo = Declaracion("booleano", ["a"])
        self.checker.visit(nodo)

        self.assertEqual(len(self.checker.errores), 1)

    def test_variable_duplicada(self):
        self.checker.visit(Declaracion("entero", ["a"]))
        self.checker.visit(Declaracion("flotante", ["a"]))

        self.assertEqual(len(self.checker.errores), 1)
        self.assertIn("ya fue declarada", self.checker.errores[0])

    # =====================================================
    # Asignaciones
    # =====================================================

    def test_asignacion_valida(self):
        self.checker.visit(Declaracion("entero", ["a"]))

        nodo = Asignacion("a", self.valor(10))
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "entero")
        self.assertEqual(len(self.checker.errores), 0)

    def test_asignacion_variable_no_declarada(self):
        nodo = Asignacion("a", self.valor(10))
        self.checker.visit(nodo)

        self.assertEqual(len(self.checker.errores), 1)
        self.assertIsNone(nodo.tipo)

    def test_asignacion_tipo_incompatible(self):
        self.checker.visit(Declaracion("entero", ["a"]))

        nodo = Asignacion("a", self.valor("hola"))
        self.checker.visit(nodo)

        self.assertEqual(len(self.checker.errores), 1)

    def test_promocion_entero_a_flotante(self):
        self.checker.visit(Declaracion("flotante", ["a"]))

        nodo = Asignacion("a", self.valor(10))
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "flotante")
        self.assertEqual(len(self.checker.errores), 0)

    # =====================================================
    # Expresiones
    # =====================================================

    def test_valor_entero(self):
        nodo = self.valor(10)
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "entero")

    def test_valor_flotante(self):
        nodo = self.valor(10.5)
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "flotante")

    def test_valor_cadena(self):
        nodo = self.valor("hola")
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "cadena")

    def test_variable_no_declarada(self):
        nodo = self.variable("x")
        self.checker.visit(nodo)

        self.assertIsNone(nodo.tipo)
        self.assertEqual(len(self.checker.errores), 1)

    def test_variable_declarada(self):
        self.checker.visit(Declaracion("entero", ["x"]))

        nodo = self.variable("x")
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "entero")

    def test_operacion_suma(self):
        nodo = BinOp(self.valor(10), "mas", self.valor(20))
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "entero")
        self.assertEqual(len(self.checker.errores), 0)

    def test_promocion_binop_flotante(self):
        nodo = BinOp(self.valor(10), "mas", self.valor(10.5))
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "flotante")

    def test_promocion_binop_doble(self):
        a = self.valor(10)
        a.tipo = "doble"

        nodo = BinOp(a, "mas", self.valor(2))
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "doble")

    def test_operacion_tipos_incompatibles(self):
        nodo = BinOp(self.valor(10), "mas", self.valor("hola"))
        self.checker.visit(nodo)

        self.assertIsNone(nodo.tipo)
        self.assertEqual(len(self.checker.errores), 1)

    def test_division_por_cero(self):
        nodo = BinOp(self.valor(10), "dividido", self.valor(0))
        self.checker.visit(nodo)

        self.assertIsNone(nodo.tipo)
        self.assertIn("División por cero", self.checker.errores[0])

    def test_comparacion_numerica(self):
        nodo = BinOp(self.valor(10), "menor", self.valor(20))
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "booleano")

    def test_comparacion_cadenas(self):
        nodo = BinOp(self.valor("hola"), "igual", self.valor("hola"))
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "booleano")

    def test_comparacion_cadena_numero(self):
        nodo = BinOp(self.valor("hola"), "igual", self.valor(10))
        self.checker.visit(nodo)

        self.assertIsNone(nodo.tipo)
        self.assertEqual(len(self.checker.errores), 1)

    def test_negativo_numerico(self):
        nodo = Negativo(self.valor(10))
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "entero")

    def test_negativo_cadena(self):
        nodo = Negativo(self.valor("hola"))
        self.checker.visit(nodo)

        self.assertIsNone(nodo.tipo)
        self.assertEqual(len(self.checker.errores), 1)

    # =====================================================
    # Control de flujo
    # =====================================================

    def test_condicion_si_booleana(self):
        condicion = BinOp(self.valor(10), "mayor", self.valor(5))

        nodo = InstruccionSi(
            condicion,
            None,
            None
        )

        self.checker.visit(nodo)

        self.assertEqual(len(self.checker.errores), 0)

    def test_condicion_si_no_booleana(self):
        nodo = InstruccionSi(
            self.valor(10),
            None,
            None
        )

        self.checker.visit(nodo)

        self.assertEqual(len(self.checker.errores), 1)

    # =====================================================
    # Imprimir
    # =====================================================

    def test_imprimir_cadena(self):
        nodo = Imprimir("Hola mundo")
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "cadena")

    def test_imprimir_expresion(self):
        nodo = Imprimir(BinOp(self.valor(10), "mas", self.valor(20)))
        self.checker.visit(nodo)

        self.assertEqual(nodo.tipo, "entero")

    # =====================================================
    # Función auxiliar
    # =====================================================

    def test_check_program_correcto(self):
        ast = Declaracion("entero", ["a"])

        symbols = check_program(ast)

        self.assertIn("a", symbols)

    def test_check_program_error(self):
        ast = Declaracion("booleano", ["a"])

        with self.assertRaises(SemanticError):
            check_program(ast)


if __name__ == "__main__":
    unittest.main(verbosity=2)
