from CheNodosAST import *

class SemanticError(Exception):
    pass


class CheckProgramVisitor(NodeVisitor):

    def __init__(self):
        # Tabla de símbolos: { nombre_variable: nodo_Declaracion }
        self.symbols = {}
        self.errores = []

        # Tipos permitidos según tu CheLexer
        self.tipos_validos = {"entero", "flotante", "doble", "cadena"}
        self.tipos_numericos = {"entero", "flotante", "doble"}

    def registrar_error(self, lineno, mensaje):
        if lineno is not None:
            self.errores.append(f"Error semántico (línea {lineno}): {mensaje}")
        else:
            self.errores.append(f"Error semántico: {mensaje}")

    # =========================================================
    # 1. Declaración y Asignación
    # =========================================================

    def visit_Declaracion(self, node):
        if node.tipo not in self.tipos_validos:
            self.registrar_error(node.lineno, f"Tipo de dato desconocido '{node.tipo}'.")
            return

        for nombre in node.lista_variables:
            if nombre in self.symbols:
                decl_previa = self.symbols[nombre]
                msg_linea = f" en la línea {decl_previa.lineno}" if decl_previa.lineno else ""
                self.registrar_error(
                    node.lineno,
                    f"La variable '{nombre}' ya fue declarada previamente como '{decl_previa.tipo}'{msg_linea}."
                )
            else:
                self.symbols[nombre] = node

    def visit_Asignacion(self, node):
        # Primero visitamos el lado derecho para que calcule su node.valor.tipo
        self.visit(node.valor)
        node.tipo = None

        if node.id not in self.symbols:
            self.registrar_error(node.lineno, f"La variable '{node.id}' no fue declarada antes de asignarle un valor.")
            return

        tipo_var = self.symbols[node.id].tipo
        tipo_val = getattr(node.valor, "tipo", None)

        # Si tipo_val es None, hubo un error previo en la expresión y ya se reportó
        if tipo_val is not None:
            if tipo_var == tipo_val:
                node.tipo = tipo_var
            # Permitimos asignar un entero a una variable flotante o doble
            elif tipo_var in ("flotante", "doble") and tipo_val in ("entero", "flotante", "doble"):
                node.tipo = tipo_var
            else:
                self.registrar_error(
                    node.lineno,
                    f"No se puede asignar un valor de tipo '{tipo_val}' a la variable '{node.id}' de tipo '{tipo_var}'."
                )

    # =========================================================
    # 2. Expresiones: Valores, Variables, Negativo y BinOp
    # =========================================================

    def visit_Valor(self, node):
        # Si en el parser le pasaron tipo=None, lo deducimos del valor de Python
        if not node.tipo:
            if isinstance(node.valor, int):
                node.tipo = "entero"
            elif isinstance(node.valor, float):
                node.tipo = "flotante"
            elif isinstance(node.valor, str):
                node.tipo = "cadena"

    def visit_Variable(self, node):
        if node.nombre not in self.symbols:
            node.tipo = None
            self.registrar_error(node.lineno, f"La variable '{node.nombre}' no fue declarada.")
        else:
            node.tipo = self.symbols[node.nombre].tipo

    def visit_Negativo(self, node):
        self.visit(node.valor)
        node.tipo = None

        tipo_hijo = getattr(node.valor, "tipo", None)
        if tipo_hijo is not None:
            if tipo_hijo in self.tipos_numericos:
                node.tipo = tipo_hijo
            else:
                self.registrar_error(
                    node.lineno,
                    f"No se puede aplicar el operador negativo ('menos') a un valor de tipo '{tipo_hijo}'."
                )

    def visit_BinOp(self, node):
        self.visit(node.valora)
        self.visit(node.valorb)
        node.tipo = None

        t_izq = getattr(node.valora, "tipo", None)
        t_der = getattr(node.valorb, "tipo", None)

        # Si alguno de los operandos falló antes, cortamos acá para no tirar errores en cascada
        if t_izq is None or t_der is None:
            return

        op = node.operador.lower()

        # Operaciones aritméticas
        if op in ("mas", "menos", "multiplicado", "dividido"):
            if t_izq in self.tipos_numericos and t_der in self.tipos_numericos:
                # Chequeo de división por cero literal (ej: x dividido 0)
                if op == "dividido" and isinstance(node.valorb, Valor) and node.valorb.valor == 0:
                    self.registrar_error(node.lineno, "División por cero detectada.")
                    return

                # Promoción de tipos: doble > flotante > entero
                if "doble" in (t_izq, t_der):
                    node.tipo = "doble"
                elif "flotante" in (t_izq, t_der):
                    node.tipo = "flotante"
                else:
                    node.tipo = "entero"
            else:
                self.registrar_error(
                    node.lineno,
                    f"Operación '{op}' no soportada entre '{t_izq}' y '{t_der}'."
                )

        # Operaciones de comparación
        elif op in ("menor", "mayor", "igual", "menor igual", "mayor igual", "distinto"):
            if t_izq in self.tipos_numericos and t_der in self.tipos_numericos:
                node.tipo = "booleano"
            elif op in ("igual", "distinto") and t_izq == "cadena" and t_der == "cadena":
                node.tipo = "booleano"
            else:
                self.registrar_error(
                    node.lineno,
                    f"Comparación '{op}' no soportada entre '{t_izq}' y '{t_der}'."
                )
        else:
            self.registrar_error(node.lineno, f"Operador desconocido '{node.operador}'.")

    # =========================================================
    # 3. Control de Flujo, Imprimir e Invocación
    # =========================================================

    def visit_InstruccionSi(self, node):
        self.visit(node.condicion)
        cond_tipo = getattr(node.condicion, "tipo", None)

        if cond_tipo is not None and cond_tipo != "booleano":
            self.registrar_error(
                node.lineno,
                f"La condición del 'si' debe ser booleana, pero se obtuvo '{cond_tipo}'."
            )

        self.visit(node.bloqueverdadero)
        if node.bloquefalso:
            self.visit(node.bloquefalso)

    def visit_InstruccionMientras(self, node):
        self.visit(node.condicion)
        cond_tipo = getattr(node.condicion, "tipo", None)

        if cond_tipo is not None and cond_tipo != "booleano":
            self.registrar_error(
                node.lineno,
                f"La condición del 'mientras' debe ser booleana, pero se obtuvo '{cond_tipo}'."
            )

        self.visit(node.cuerpo)

    def visit_Imprimir(self, node):
        # Si desde el parser mandaron un string crudo (CADENA), es válido directo
        if isinstance(node.valor, str):
            node.tipo = "cadena"
        else:
            # Si es una variable o expresión (ej: a mas b), la visitamos para validar que exista
            self.visit(node.valor)
            node.tipo = getattr(node.valor, "tipo", None)

    def visit_Invocacion(self, node):
        self.visit(node.argumento)
        # Como la gramática aún no tiene declaración de funciones, asumimos retorno entero por defecto
        node.tipo = "entero"


# =========================================================
# Función auxiliar para llamarlo desde main.py
# =========================================================

def check_program(ast):
    checker = CheckProgramVisitor()
    checker.visit(ast)
    if checker.errores:
        raise SemanticError("\n".join(checker.errores))
    return checker.symbols