
import unittest

from llvmlite import binding

from CheGenCodIR import CodeGenerator
from CheNodosAST import (
    Valor,
    Variable,
    BinOp,
    Negativo,
    Declaracion,
    Asignacion,
    Imprimir,
    InstruccionSi,
    InstruccionMientras,
    Invocacion,
)


class TestCodeGenerator(unittest.TestCase):

    # =====================================================
    # HELPERS
    # =====================================================

    def setUp(self):
        self.cg = CodeGenerator()

    def valor(self, value, tipo="entero"):
        return Valor(value, tipo, 1)

    def variable(self, nombre):
        return Variable(nombre, 1)

    def binop(self, izq, operador, der):
        return BinOp(izq, operador, der, 1)

    def declarar(self, tipo, *nombres):
        self.cg.generar_declaracion(
            Declaracion(tipo, list(nombres), 1)
        )

    def asignar(self, nombre, valor):
        self.cg.generar_asignacion(
            Asignacion(nombre, valor, 1)
        )

    def generar(self, instrucciones):
        return self.cg.generar_programa(instrucciones)

    def verificar_ir(self, modulo=None):
        """Comprueba que LLVM pueda parsear y verificar el módulo."""
        if modulo is None:
            modulo = self.cg.module

        modulo_verificado = binding.parse_assembly(str(modulo))
        modulo_verificado.verify()
        return modulo_verificado

    def generar_expresion_y_verificar(self, expresion):
        self.cg.generar_expresion(expresion)

        if not self.cg.builder.block.is_terminated:
            self.cg.builder.ret(self.cg.i32(0))

        return self.verificar_ir()

    # =====================================================
    # 1. DECLARACIONES
    # =====================================================

    def test_declarar_entero(self):
        self.declarar("entero", "edad")

        self.assertIn("edad", self.cg.variables)
        self.assertEqual(self.cg.variables["edad"][1], self.cg.i32)

    def test_declarar_flotante(self):
        self.declarar("flotante", "altura")

        self.assertIn("altura", self.cg.variables)
        self.assertEqual(self.cg.variables["altura"][1], self.cg.float)

    def test_declarar_doble(self):
        self.declarar("doble", "distancia")

        self.assertIn("distancia", self.cg.variables)
        self.assertEqual(self.cg.variables["distancia"][1], self.cg.double)

    def test_declarar_varias_variables(self):
        self.declarar("entero", "a", "b", "c")

        self.assertEqual(
            set(self.cg.variables.keys()),
            {"a", "b", "c"}
        )

    def test_no_permitir_variable_duplicada(self):
        self.declarar("entero", "edad")

        with self.assertRaisesRegex(Exception, "Variable ya declarada"):
            self.declarar("entero", "edad")

    def test_tipo_no_soportado(self):
        with self.assertRaisesRegex(Exception, "Tipo no soportado"):
            self.declarar("booleano", "activo")

    # =====================================================
    # 2. CONSTANTES
    # =====================================================

    def test_constante_entera(self):
        resultado = self.cg.generar_expresion(
            self.valor(42, "entero")
        )

        self.assertEqual(resultado.type, self.cg.i32)
        self.assertEqual(resultado.constant, 42)

    def test_constante_flotante(self):
        resultado = self.cg.generar_expresion(
            self.valor(3.14, "flotante")
        )

        self.assertEqual(resultado.type, self.cg.float)

    def test_constante_doble(self):
        resultado = self.cg.generar_expresion(
            self.valor(3.14159, "doble")
        )

        self.assertEqual(resultado.type, self.cg.double)

    def test_constante_cadena(self):
        resultado = self.cg.generar_expresion(
            self.valor("Hola mundo", "cadena")
        )

        self.assertEqual(resultado.type, self.cg.i8.as_pointer())
        self.assertIn("str_1", str(self.cg.module))

    def test_tipo_de_constante_no_soportado(self):
        with self.assertRaisesRegex(Exception, "Tipo no soportado"):
            self.cg.generar_expresion(
                self.valor(True, "booleano")
            )

    # =====================================================
    # 3. VARIABLES Y ASIGNACIONES
    # =====================================================

    def test_leer_variable(self):
        self.declarar("entero", "numero")
        self.asignar("numero", self.valor(10))

        resultado = self.cg.generar_expresion(
            self.variable("numero")
        )

        self.assertEqual(resultado.type, self.cg.i32)

    def test_leer_variable_no_declarada(self):
        with self.assertRaisesRegex(Exception, "Variable no declarada"):
            self.cg.generar_expresion(
                self.variable("inexistente")
            )

    def test_asignacion_entera(self):
        self.declarar("entero", "numero")
        self.asignar("numero", self.valor(100))

        modulo = self.generar([])

        self.assertIn("store i32 100", str(modulo))
        self.verificar_ir(modulo)

    def test_asignacion_flotante(self):
        self.declarar("flotante", "numero")
        self.asignar("numero", self.valor(2.5, "flotante"))

        modulo = self.generar([])

        self.assertIn("store float", str(modulo))
        self.verificar_ir(modulo)

    def test_asignacion_doble(self):
        self.declarar("doble", "numero")
        self.asignar("numero", self.valor(2.5, "doble"))

        modulo = self.generar([])

        self.assertIn("store double", str(modulo))
        self.verificar_ir(modulo)

    def test_asignacion_a_variable_no_declarada(self):
        with self.assertRaisesRegex(Exception, "Variable no declarada"):
            self.asignar("inexistente", self.valor(10))

    def test_conversion_entero_a_flotante(self):
        self.declarar("flotante", "numero")
        self.asignar("numero", self.valor(10, "entero"))

        modulo = self.generar([])

        self.assertIn("sitofp", str(modulo))
        self.verificar_ir(modulo)

    def test_conversion_entero_a_doble(self):
        self.declarar("doble", "numero")
        self.asignar("numero", self.valor(10, "entero"))

        modulo = self.generar([])

        self.assertIn("sitofp", str(modulo))
        self.verificar_ir(modulo)

    def test_conversion_flotante_a_doble(self):
        self.declarar("doble", "numero")
        self.asignar("numero", self.valor(2.5, "flotante"))

        modulo = self.generar([])

        self.assertIn("fpext", str(modulo))
        self.verificar_ir(modulo)

    def test_conversion_doble_a_flotante(self):
        self.declarar("flotante", "numero")
        self.asignar("numero", self.valor(2.5, "doble"))

        modulo = self.generar([])

        self.assertIn("fptrunc", str(modulo))
        self.verificar_ir(modulo)

    def test_conversion_flotante_a_entero(self):
        self.declarar("entero", "numero")
        self.asignar("numero", self.valor(2.5, "flotante"))

        modulo = self.generar([])

        self.assertIn("fptosi", str(modulo))
        self.verificar_ir(modulo)

    # =====================================================
    # 4. OPERACIONES ARITMETICAS CON ENTEROS
    # =====================================================

    def test_suma_enteros(self):
        expresion = self.binop(
            self.valor(10),
            "mas",
            self.valor(5)
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.i32)
        self.generar([])

        self.assertIn("add i32", str(self.cg.module))
        self.verificar_ir()

    def test_resta_enteros(self):
        expresion = self.binop(
            self.valor(10),
            "menos",
            self.valor(5)
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.i32)
        self.generar([])

        self.assertIn("sub i32", str(self.cg.module))
        self.verificar_ir()

    def test_multiplicacion_enteros(self):
        expresion = self.binop(
            self.valor(10),
            "multiplicado",
            self.valor(5)
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.i32)
        self.generar([])

        self.assertIn("mul i32", str(self.cg.module))
        self.verificar_ir()

    @unittest.expectedFailure
    def test_division_enteros(self):
        """
        Este test debería generar una división float.
        Actualmente el generador convierte los operandos a float,
        pero conserva es_flotante = False.
        """
        expresion = self.binop(
            self.valor(10),
            "dividido",
            self.valor(2)
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.float)

        self.generar([])
        self.assertIn("fdiv float", str(self.cg.module))
        self.verificar_ir()

    # =====================================================
    # 5. OPERACIONES CON FLOTANTES
    # =====================================================

    def test_suma_flotantes(self):
        expresion = self.binop(
            self.valor(1.5, "flotante"),
            "mas",
            self.valor(2.5, "flotante")
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.float)
        self.generar([])

        self.assertIn("fadd float", str(self.cg.module))
        self.verificar_ir()

    def test_resta_flotantes(self):
        expresion = self.binop(
            self.valor(5.5, "flotante"),
            "menos",
            self.valor(2.5, "flotante")
        )

        self.cg.generar_expresion(expresion)
        self.generar([])

        self.assertIn("fsub float", str(self.cg.module))
        self.verificar_ir()

    def test_multiplicacion_flotantes(self):
        expresion = self.binop(
            self.valor(2.0, "flotante"),
            "multiplicado",
            self.valor(3.0, "flotante")
        )

        self.cg.generar_expresion(expresion)
        self.generar([])

        self.assertIn("fmul float", str(self.cg.module))
        self.verificar_ir()

    def test_division_flotantes(self):
        expresion = self.binop(
            self.valor(10.0, "flotante"),
            "dividido",
            self.valor(2.0, "flotante")
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.float)
        self.generar([])

        self.assertIn("fdiv float", str(self.cg.module))
        self.verificar_ir()

    # =====================================================
    # 6. PROMOCION DE TIPOS EN OPERACIONES
    # =====================================================

    def test_suma_entero_con_flotante(self):
        expresion = self.binop(
            self.valor(10, "entero"),
            "mas",
            self.valor(2.5, "flotante")
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.float)
        self.generar([])

        self.assertIn("sitofp", str(self.cg.module))
        self.assertIn("fadd float", str(self.cg.module))
        self.verificar_ir()

    def test_suma_entero_con_doble(self):
        expresion = self.binop(
            self.valor(10, "entero"),
            "mas",
            self.valor(2.5, "doble")
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.double)
        self.generar([])

        self.assertIn("fadd double", str(self.cg.module))
        self.verificar_ir()

    def test_suma_flotante_con_doble(self):
        expresion = self.binop(
            self.valor(1.5, "flotante"),
            "mas",
            self.valor(2.5, "doble")
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.double)
        self.generar([])

        self.assertIn("fpext", str(self.cg.module))
        self.assertIn("fadd double", str(self.cg.module))
        self.verificar_ir()

    # =====================================================
    # 7. COMPARACIONES
    # =====================================================

    def test_menor_que(self):
        expresion = self.binop(
            self.valor(5),
            "menor",
            self.valor(10)
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.i1)
        self.generar([])

        self.assertIn("icmp slt", str(self.cg.module))
        self.verificar_ir()

    def test_mayor_que(self):
        expresion = self.binop(
            self.valor(10),
            "mayor",
            self.valor(5)
        )

        self.cg.generar_expresion(expresion)
        self.generar([])

        self.assertIn("icmp sgt", str(self.cg.module))
        self.verificar_ir()

    def test_menor_igual(self):
        expresion = self.binop(
            self.valor(5),
            "menor igual",
            self.valor(10)
        )

        self.cg.generar_expresion(expresion)
        self.generar([])

        self.assertIn("icmp sle", str(self.cg.module))
        self.verificar_ir()

    def test_mayor_igual(self):
        expresion = self.binop(
            self.valor(10),
            "mayor igual",
            self.valor(5)
        )

        self.cg.generar_expresion(expresion)
        self.generar([])

        self.assertIn("icmp sge", str(self.cg.module))
        self.verificar_ir()

    def test_igual(self):
        expresion = self.binop(
            self.valor(10),
            "igual",
            self.valor(10)
        )

        self.cg.generar_expresion(expresion)
        self.generar([])

        self.assertIn("icmp eq", str(self.cg.module))
        self.verificar_ir()

    def test_distinto(self):
        expresion = self.binop(
            self.valor(10),
            "distinto",
            self.valor(5)
        )

        self.cg.generar_expresion(expresion)
        self.generar([])

        self.assertIn("icmp ne", str(self.cg.module))
        self.verificar_ir()

    def test_comparacion_flotantes(self):
        expresion = self.binop(
            self.valor(2.5, "flotante"),
            "mayor",
            self.valor(1.5, "flotante")
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.i1)
        self.generar([])

        self.assertIn("fcmp ogt", str(self.cg.module))
        self.verificar_ir()

    def test_comparacion_doble(self):
        expresion = self.binop(
            self.valor(2.5, "doble"),
            "menor",
            self.valor(3.5, "doble")
        )

        self.cg.generar_expresion(expresion)
        self.generar([])

        self.assertIn("fcmp olt", str(self.cg.module))
        self.verificar_ir()

    # =====================================================
    # 8. NEGATIVOS
    # =====================================================

    def test_negativo_entero(self):
        expresion = Negativo(self.valor(10), 1)

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.i32)
        self.generar([])

        self.assertIn("sub i32 0", str(self.cg.module))
        self.verificar_ir()

    def test_negativo_flotante(self):
        expresion = Negativo(
            self.valor(10.5, "flotante"),
            1
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.float)
        self.generar([])

        self.assertIn("fneg float", str(self.cg.module))
        self.verificar_ir()

    def test_negativo_doble(self):
        expresion = Negativo(
            self.valor(10.5, "doble"),
            1
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.double)
        self.generar([])

        self.assertIn("fneg double", str(self.cg.module))
        self.verificar_ir()

    def test_negativo_de_expresion(self):
        expresion = Negativo(
            self.binop(
                self.valor(10),
                "mas",
                self.valor(5)
            ),
            1
        )

        resultado = self.cg.generar_expresion(expresion)

        self.assertEqual(resultado.type, self.cg.i32)
        self.generar([])

        self.assertIn("sub i32 0", str(self.cg.module))
        self.verificar_ir()

    # =====================================================
    # 9. IMPRESION
    # =====================================================

    def test_imprimir_cadena_literal(self):
        modulo = self.generar([
            Imprimir("Hola mundo", 1)
        ])

        self.assertIn("Hola mundo", str(modulo))
        self.assertIn("call i32 (i8*, ...) @printf", str(modulo))
        self.verificar_ir(modulo)

    def test_imprimir_entero(self):
        modulo = self.generar([
            Imprimir(self.valor(42), 1)
        ])

        self.assertIn("@fmt_int", str(modulo))
        self.verificar_ir(modulo)

    def test_imprimir_flotante(self):
        modulo = self.generar([
            Imprimir(self.valor(3.14, "flotante"), 1)
        ])

        self.assertIn("@fmt_float", str(modulo))
        self.assertIn("fpext", str(modulo))
        self.verificar_ir(modulo)

    def test_imprimir_doble(self):
        modulo = self.generar([
            Imprimir(self.valor(3.14159, "doble"), 1)
        ])

        self.assertIn("@fmt_float", str(modulo))
        self.verificar_ir(modulo)

    def test_imprimir_variable(self):
        modulo = self.generar([
            Declaracion("entero", ["numero"], 1),
            Asignacion("numero", self.valor(42), 1),
            Imprimir(self.variable("numero"), 1)
        ])

        self.assertIn("cargar_numero", str(modulo))
        self.assertIn("@printf", str(modulo))
        self.verificar_ir(modulo)

    def test_imprimir_expresion(self):
        expresion = self.binop(
            self.valor(10),
            "mas",
            self.valor(20)
        )

        modulo = self.generar([
            Imprimir(expresion, 1)
        ])

        self.assertIn("add i32", str(modulo))
        self.assertIn("@printf", str(modulo))
        self.verificar_ir(modulo)

    # =====================================================
    # 10. CONDICIONAL IF
    # =====================================================

    def test_if_sin_else(self):
        condicion = self.binop(
            self.valor(10),
            "mayor",
            self.valor(5)
        )

        nodo = InstruccionSi(
            condicion,
            [Imprimir("Es mayor", 1)],
            None,
            1
        )

        modulo = self.generar([nodo])

        self.assertIn("if_true", str(modulo))
        self.assertIn("if_false", str(modulo))
        self.assertIn("if_end", str(modulo))
        self.verificar_ir(modulo)

    def test_if_con_else(self):
        condicion = self.binop(
            self.valor(10),
            "mayor",
            self.valor(5)
        )

        nodo = InstruccionSi(
            condicion,
            [Imprimir("Verdadero", 1)],
            [Imprimir("Falso", 1)],
            1
        )

        modulo = self.generar([nodo])

        self.assertIn("Verdadero", str(modulo))
        self.assertIn("Falso", str(modulo))
        self.verificar_ir(modulo)

    def test_if_con_asignaciones(self):
        condicion = self.binop(
            self.valor(10),
            "mayor",
            self.valor(5)
        )

        nodo = InstruccionSi(
            condicion,
            [Asignacion("x", self.valor(1), 1)],
            [Asignacion("x", self.valor(2), 1)],
            1
        )

        modulo = self.generar([
            Declaracion("entero", ["x"], 1),
            nodo
        ])

        self.assertIn("if_true", str(modulo))
        self.assertIn("if_false", str(modulo))
        self.verificar_ir(modulo)

    # =====================================================
    # 11. BUCLE WHILE
    # =====================================================

    def test_while_basico(self):
        condicion = self.binop(
            self.variable("i"),
            "menor",
            self.valor(10)
        )

        nodo = InstruccionMientras(
            condicion,
            [
                Asignacion(
                    "i",
                    self.binop(
                        self.variable("i"),
                        "mas",
                        self.valor(1)
                    ),
                    1
                )
            ],
            1
        )

        modulo = self.generar([
            Declaracion("entero", ["i"], 1),
            Asignacion("i", self.valor(0), 1),
            nodo
        ])

        self.assertIn("while_cond", str(modulo))
        self.assertIn("while_body", str(modulo))
        self.assertIn("while_end", str(modulo))
        self.verificar_ir(modulo)

    def test_while_sin_instrucciones(self):
        condicion = self.binop(
            self.valor(1),
            "menor",
            self.valor(2)
        )

        nodo = InstruccionMientras(condicion, [], 1)

        modulo = self.generar([nodo])

        self.assertIn("while_cond", str(modulo))
        self.verificar_ir(modulo)

    # =====================================================
    # 12. PROGRAMAS INTEGRALES
    # =====================================================

    def test_programa_completo(self):
        """
        Programa equivalente a:

        entero a, b, resultado
        a = 10
        b = 20
        resultado = a + b
        imprimir(resultado)
        """

        modulo = self.generar([
            Declaracion("entero", ["a", "b", "resultado"], 1),

            Asignacion("a", self.valor(10), 2),
            Asignacion("b", self.valor(20), 3),

            Asignacion(
                "resultado",
                self.binop(
                    self.variable("a"),
                    "mas",
                    self.variable("b")
                ),
                4
            ),

            Imprimir(self.variable("resultado"), 5)
        ])

        self.assertIn("add i32", str(modulo))
        self.assertIn("@printf", str(modulo))
        self.assertIn("ret i32 0", str(modulo))
        self.verificar_ir(modulo)

    def test_programa_con_if_y_while(self):
        condicion_if = self.binop(
            self.variable("contador"),
            "mayor",
            self.valor(0)
        )

        condicion_while = self.binop(
            self.variable("contador"),
            "menor",
            self.valor(5)
        )

        modulo = self.generar([
            Declaracion("entero", ["contador"], 1),

            Asignacion("contador", self.valor(0), 1),

            InstruccionMientras(
                condicion_while,
                [
                    Asignacion(
                        "contador",
                        self.binop(
                            self.variable("contador"),
                            "mas",
                            self.valor(1)
                        ),
                        1
                    )
                ],
                1
            ),

            InstruccionSi(
                condicion_if,
                [Imprimir("Mayor que cero", 1)],
                [Imprimir("Cero", 1)],
                1
            )
        ])

        self.assertIn("while_cond", str(modulo))
        self.assertIn("if_true", str(modulo))
        self.verificar_ir(modulo)

    def test_programa_con_expresiones_anidadas(self):
        """
        resultado = (10 + 5) * (20 - 3)
        """

        expresion = self.binop(
            self.binop(
                self.valor(10),
                "mas",
                self.valor(5)
            ),
            "multiplicado",
            self.binop(
                self.valor(20),
                "menos",
                self.valor(3)
            )
        )

        modulo = self.generar([
            Declaracion("entero", ["resultado"], 1),
            Asignacion("resultado", expresion, 1),
            Imprimir(self.variable("resultado"), 1)
        ])

        self.assertIn("add i32", str(modulo))
        self.assertIn("sub i32", str(modulo))
        self.assertIn("mul i32", str(modulo))
        self.verificar_ir(modulo)

    # =====================================================
    # 13. ERRORES Y CASOS NO SOPORTADOS
    # =====================================================

    def test_operador_desconocido(self):
        expresion = self.binop(
            self.valor(10),
            "potencia",
            self.valor(2)
        )

        with self.assertRaisesRegex(Exception, "Operador desconocido"):
            self.cg.generar_expresion(expresion)

    def test_expresion_no_soportada(self):
        with self.assertRaisesRegex(Exception, "Expresion no soportada"):
            self.cg.generar_expresion(None)

    def test_instruccion_no_soportada(self):
        with self.assertRaisesRegex(Exception, "Instruccion no soportada"):
            self.cg.generar_instruccion(
                Invocacion("funcion", [], 1)
            )

    # =====================================================
    # 14. ESTRUCTURA DEL MODULO LLVM
    # =====================================================

    def test_existe_funcion_main(self):
        modulo = self.generar([])

        self.assertIn("define i32 @main()", str(modulo))
        self.verificar_ir(modulo)

    def test_existe_printf(self):
        modulo = self.generar([])

        self.assertIn("declare i32 @printf", str(modulo))
        self.verificar_ir(modulo)

    def test_formatos_de_impresion(self):
        modulo = self.generar([])

        texto = str(modulo)

        self.assertIn("@fmt_int", texto)
        self.assertIn("@fmt_str", texto)
        self.assertIn("@fmt_float", texto)

        self.verificar_ir(modulo)

    def test_generar_programa_recibe_un_nodo_suelto(self):
        modulo = self.generar(
            Imprimir("Hola", 1)
        )

        self.assertIn("@printf", str(modulo))
        self.verificar_ir(modulo)

    def test_generar_programa_recibe_lista_vacia(self):
        modulo = self.generar([])

        self.assertIn("ret i32 0", str(modulo))
        self.verificar_ir(modulo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
