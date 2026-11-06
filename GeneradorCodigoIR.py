from CheNodosAST import *
from llvmlite import ir


class CodeGenerator:

    def __init__(self):

        # Modulo LLVM
        self.module = ir.Module(name="programa")

        # Tipo entero de 32 bits
        self.i32 = ir.IntType(32)

        # Tipo booleano
        self.i1 = ir.IntType(1)

        # Funcion principal
        tipo_funcion = ir.FunctionType(
            self.i32,
            []
        )

        self.funcion = ir.Function(
            self.module,
            tipo_funcion,
            name="main"
        )

        # Bloque inicial
        entry = self.funcion.append_basic_block("entry")

        self.builder = ir.IRBuilder(entry)

        # Tabla de simbolos:
        # nombre -> direccion de memoria LLVM
        self.variables = {}

    # =====================================
    # Declaracion de variables
    # =====================================

    def generar_declaracion(self, nodo):

        for nombre in nodo.lista_variables:

            if nombre in self.variables:
                raise Exception(
                    f"Variable ya declarada: {nombre}"
                )

            direccion = self.builder.alloca(
                self.i32,
                name=nombre
            )

            self.variables[nombre] = direccion

    # =====================================
    # Generar expresiones
    # =====================================

    def generar_expresion(self, nodo):

        # Valor constante
        if isinstance(nodo, Valor):

            return ir.Constant(
                self.i32,
                int(nodo.valor)
            )

        # Variable
        elif isinstance(nodo, Variable):

            if nodo.nombre not in self.variables:
                raise Exception(
                    f"Variable no declarada: {nodo.nombre}"
                )

            direccion = self.variables[nodo.nombre]

            return self.builder.load(
                direccion,
                name=f"cargar_{nodo.nombre}"
            )

        # Operacion binaria
        elif isinstance(nodo, BinOp):

            izquierda = self.generar_expresion(
                nodo.valora
            )

            derecha = self.generar_expresion(
                nodo.valorb
            )

            operador = nodo.operador

            # Operaciones aritmeticas
            if operador == "mas":
                return self.builder.add(
                    izquierda, derecha
                )

            elif operador == "menos":
                return self.builder.sub(
                    izquierda, derecha
                )

            elif operador == "multiplicado":
                return self.builder.mul(
                    izquierda, derecha
                )

            elif operador == "/":
                return self.builder.sdiv(
                    izquierda, derecha
                )

            # Comparaciones
            elif operador == "menor":
                return self.builder.icmp_signed(
                    "<", izquierda, derecha
                )

            elif operador == "mayor":
                return self.builder.icmp_signed(
                    ">", izquierda, derecha
                )

            elif operador == "<=":
                return self.builder.icmp_signed(
                    "<=", izquierda, derecha
                )

            elif operador == ">=":
                return self.builder.icmp_signed(
                    ">=", izquierda, derecha
                )

            elif operador == "==":
                return self.builder.icmp_signed(
                    "==", izquierda, derecha
                )

            elif operador == "!=":
                return self.builder.icmp_signed(
                    "!=", izquierda, derecha
                )

            else:
                raise Exception(
                    f"Operador desconocido: {operador}"
                )

        raise Exception(
            f"Expresion no soportada: {type(nodo).__name__}"
        )

    # =====================================
    # Asignacion
    # =====================================

    def generar_asignacion(self, nodo):

        if nodo.id not in self.variables:
            raise Exception(
                f"Variable no declarada: {nodo.id}"
            )

        valor = self.generar_expresion(
            nodo.valor
        )

        direccion = self.variables[nodo.id]

        self.builder.store(
            valor,
            direccion
        )

    # =====================================
    # Generar instrucciones
    # =====================================

    def generar_instruccion(self, nodo):

        if isinstance(nodo, Declaracion):

            self.generar_declaracion(nodo)

        elif isinstance(nodo, Asignacion):

            self.generar_asignacion(nodo)

        elif isinstance(nodo, InstruccionSi):

            self.generar_si(nodo)

        elif isinstance(nodo, InstruccionMientras):

            self.generar_mientras(nodo)

        elif isinstance(nodo, Imprimir):
            self.generar_imprimir(nodo)
        else:

            raise Exception(
                f"Instruccion no soportada: {type(nodo).__name__}"
            )
    def generar_imprimir(self, nodo):
        pass

    # =====================================
    # Generar bloques de instrucciones
    # =====================================

    def generar_bloque(self, instrucciones):

        for instruccion in instrucciones:

            # Si el bloque ya termino, no generar mas
            if self.builder.block.is_terminated:
                break

            self.generar_instruccion(instruccion)

    # =====================================
    # Generar IF
    # =====================================

    def generar_si(self, nodo):

        condicion = self.generar_expresion(
            nodo.condicion
        )

        bloque_true = self.funcion.append_basic_block(
            "if_true"
        )

        bloque_false = self.funcion.append_basic_block(
            "if_false"
        )

        bloque_end = self.funcion.append_basic_block(
            "if_end"
        )

        self.builder.cbranch(
            condicion,
            bloque_true,
            bloque_false
        )

        # Rama verdadera
        self.builder.position_at_end(
            bloque_true
        )

        self.generar_bloque(
            nodo.bloqueverdadero
        )

        if not self.builder.block.is_terminated:

            self.builder.branch(
                bloque_end
            )

        # Rama falsa
        self.builder.position_at_end(
            bloque_false
        )

        if nodo.bloquefalso is not None:

            self.generar_bloque(
                nodo.bloquefalso
            )

        if not self.builder.block.is_terminated:

            self.builder.branch(
                bloque_end
            )

        # Continuacion
        self.builder.position_at_end(
            bloque_end
        )

    # =====================================
    # Generar WHILE
    # =====================================

    def generar_mientras(self, nodo):

        bloque_condicion = self.funcion.append_basic_block(
            "while_cond"
        )

        bloque_cuerpo = self.funcion.append_basic_block(
            "while_body"
        )

        bloque_end = self.funcion.append_basic_block(
            "while_end"
        )

        # Entrada al ciclo
        self.builder.branch(
            bloque_condicion
        )

        # Evaluar condicion
        self.builder.position_at_end(
            bloque_condicion
        )

        condicion = self.generar_expresion(
            nodo.condicion
        )

        self.builder.cbranch(
            condicion,
            bloque_cuerpo,
            bloque_end
        )

        # Cuerpo
        self.builder.position_at_end(
            bloque_cuerpo
        )

        self.generar_bloque(
            nodo.cuerpo
        )

        # Volver a evaluar
        if not self.builder.block.is_terminated:

            self.builder.branch(
                bloque_condicion
            )

        # Continuacion
        self.builder.position_at_end(
            bloque_end
        )

    # =====================================
    # Generar programa
    # =====================================

    def generar_programa(self, instrucciones):

        self.generar_bloque(
            instrucciones
        )

        if not self.builder.block.is_terminated:

            self.builder.ret(
                ir.Constant(self.i32, 0)
            )

        return self.module
