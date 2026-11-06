from CheNodosAST import *
from llvmlite import ir


class CodeGenerator:

    def __init__(self):
        # Modulo LLVM
        self.module = ir.Module(name="programa")

        # Tipos base
        self.i32 = ir.IntType(32)
        self.i8 = ir.IntType(8)
        self.i1 = ir.IntType(1)
        self.float = ir.FloatType()
        self.double = ir.DoubleType()
        self.string = ir.ArrayType()
        # Declarar printf externo (de C) para que funcione generar_imprimir
        voidptr_ty = self.i8.as_pointer()
        printf_ty = ir.FunctionType(self.i32, [voidptr_ty], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")

        # Funcion principal
        tipo_funcion = ir.FunctionType(self.i32, [])
        self.funcion = ir.Function(self.module, tipo_funcion, name="main")

        # Bloque inicial
        entry = self.funcion.append_basic_block("entry")
        self.builder = ir.IRBuilder(entry)

        # Tabla de simbolos: nombre -> direccion de memoria LLVM
        self.variables = {}
        self.contador_str = 0

        # Formatos globales para printf
        self.fmt_int = self._crear_constante_str("%d\n\0", "fmt_int")
        self.fmt_str = self._crear_constante_str("%s\n\0", "fmt_str")

    def _crear_constante_str(self, texto, nombre):
        bytes_val = bytearray(texto.encode("utf-8"))
        tipo_arr = ir.ArrayType(self.i8, len(bytes_val))
        var_global = ir.GlobalVariable(self.module, tipo_arr, name=nombre)
        var_global.linkage = "internal"
        var_global.global_constant = True
        var_global.initializer = ir.Constant(tipo_arr, bytes_val)
        return var_global

    # =====================================
    # Declaracion de variables
    # =====================================

    def generar_declaracion(self, nodo):
        for nombre in nodo.lista_variables:
            if nombre in self.variables:
                raise Exception(f"Variable ya declarada: {nombre}")

            # Siempre reservar en el bloque entry para evitar fallos en while/if
            with self.builder.goto_entry_block():
                direccion = self.builder.alloca(self.i32, name=nombre)

            self.variables[nombre] = direccion

    # =====================================
    # Generar expresiones
    # =====================================

    def generar_expresion(self, nodo):
        # Valor constante
        if isinstance(nodo, Valor):
            if nodo.tipo == 'entero':
                return ir.Constant(self.i32, nodo.valor)
            if nodo.tipo == 'flotante':
                return ir.Constant(self.float, nodo.valor)
            if nodo.tipo == 'doble':
                return ir.Constant(self.double, nodo.valor)
            if nodo.tipo == 'cadena':
                datos = bytearray(nodo.valor.encode("utf-8"))
                datos.append(0)

                tipo_string = ir.ArrayType(ir.IntType(8), len(datos))

                cadena = ir.GlobalVariable(
                    self.module,
                    tipo_string,
                    name="cadena"
                )

                cadena.global_constant = True
                return ir.Constant(tipo_string, datos)
            else:
                raise Exception(f"Tipo no soportado: {nodo.tipo}")
        # Variable
        elif isinstance(nodo, Variable):
            if nodo.nombre not in self.variables:
                raise Exception(f"Variable no declarada: {nodo.nombre}")

            direccion = self.variables[nodo.nombre]
            return self.builder.load(direccion, name=f"cargar_{nodo.nombre}")

        # Operacion binaria
        elif isinstance(nodo, BinOp):
            izquierda = self.generar_expresion(nodo.valora)
            derecha = self.generar_expresion(nodo.valorb)
            operador = nodo.operador.lower()  # .lower() por el 'MENOS' unario del parser

            # Operaciones aritmeticas (nombres exactos de CheLexer)
            if operador == "mas":
                return self.builder.add(izquierda, derecha)
            elif operador == "menos":
                return self.builder.sub(izquierda, derecha)
            elif operador == "multiplicado":
                return self.builder.mul(izquierda, derecha)
            elif operador in ("dividido", "/"):
                return self.builder.sdiv(izquierda, derecha)

            # Comparaciones (nombres exactos de CheLexer)
            elif operador == "menor":
                return self.builder.icmp_signed("<", izquierda, derecha)
            elif operador == "mayor":
                return self.builder.icmp_signed(">", izquierda, derecha)
            elif operador in ("menor igual", "<="):
                return self.builder.icmp_signed("<=", izquierda, derecha)
            elif operador in ("mayor igual", ">="):
                return self.builder.icmp_signed(">=", izquierda, derecha)
            elif operador in ("igual", "=="):
                return self.builder.icmp_signed("==", izquierda, derecha)
            elif operador in ("distinto", "!="):
                return self.builder.icmp_signed("!=", izquierda, derecha)
            else:
                raise Exception(f"Operador desconocido: {operador}")

        raise Exception(f"Expresion no soportada: {type(nodo).__name__}")

    # =====================================
    # Asignacion
    # =====================================

    def generar_asignacion(self, nodo):
        if nodo.id not in self.variables:
            raise Exception(f"Variable no declarada: {nodo.id}")

        valor = self.generar_expresion(nodo.valor)
        direccion = self.variables[nodo.id]
        self.builder.store(valor, direccion)

    # =====================================
    # Imprimir (printf)
    # =====================================

    def generar_imprimir(self, nodo):
        cero = ir.Constant(self.i32, 0)

        # Caso 1: Es una CADENA literal (ej: "hola")
        if isinstance(nodo.valor, str):
            texto = nodo.valor.strip('"') + "\0"
            self.contador_str += 1
            var_str = self._crear_constante_str(texto, f"str_{self.contador_str}")
            ptr_str = self.builder.gep(var_str, [cero, cero], inbounds=True)
            ptr_fmt = self.builder.gep(self.fmt_str, [cero, cero], inbounds=True)
            self.builder.call(self.printf, [ptr_fmt, ptr_str])

        # Caso 2: Es una expresion o variable
        else:
            valor = self.generar_expresion(nodo.valor)
            # Si imprimen una comparacion (i1), pasarla a i32 para printf
            if valor.type == self.i1:
                valor = self.builder.zext(valor, self.i32)
            ptr_fmt = self.builder.gep(self.fmt_int, [cero, cero], inbounds=True)
            self.builder.call(self.printf, [ptr_fmt, valor])

    # =====================================
    # Generar instrucciones y bloques
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
            raise Exception(f"Instruccion no soportada: {type(nodo).__name__}")

    def generar_bloque(self, instrucciones):
        for instruccion in instrucciones:
            if self.builder.block.is_terminated:
                break
            self.generar_instruccion(instruccion)

    # =====================================
    # Generar IF y WHILE
    # =====================================

    def generar_si(self, nodo):
        condicion = self.generar_expresion(nodo.condicion)

        bloque_true = self.funcion.append_basic_block("if_true")
        bloque_false = self.funcion.append_basic_block("if_false")
        bloque_end = self.funcion.append_basic_block("if_end")

        self.builder.cbranch(condicion, bloque_true, bloque_false)

        self.builder.position_at_end(bloque_true)
        self.generar_bloque(nodo.bloqueverdadero)
        if not self.builder.block.is_terminated:
            self.builder.branch(bloque_end)

        self.builder.position_at_end(bloque_false)
        if nodo.bloquefalso is not None:
            self.generar_bloque(nodo.bloquefalso)
        if not self.builder.block.is_terminated:
            self.builder.branch(bloque_end)

        self.builder.position_at_end(bloque_end)

    def generar_mientras(self, nodo):
        bloque_condicion = self.funcion.append_basic_block("while_cond")
        bloque_cuerpo = self.funcion.append_basic_block("while_body")
        bloque_end = self.funcion.append_basic_block("while_end")

        self.builder.branch(bloque_condicion)

        self.builder.position_at_end(bloque_condicion)
        condicion = self.generar_expresion(nodo.condicion)
        self.builder.cbranch(condicion, bloque_cuerpo, bloque_end)

        self.builder.position_at_end(bloque_cuerpo)
        self.generar_bloque(nodo.cuerpo)
        if not self.builder.block.is_terminated:
            self.builder.branch(bloque_condicion)

        self.builder.position_at_end(bloque_end)

    # =====================================
    # Generar programa
    # =====================================

    def generar_programa(self, instrucciones):
        # Si el parser devuelve un nodo suelto en vez de lista, lo envolvemos
        if not isinstance(instrucciones, list):
            instrucciones = [instrucciones]

        self.generar_bloque(instrucciones)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(self.i32, 0))

        return self.module