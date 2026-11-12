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
        self.string = ir.ArrayType(self.i8, 0)
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
        self.fmt_float = self._crear_constante_str("%g\n\0", "fmt_float")

    def _convertir_a_tipo(self, valor, tipo_destino):
        """Convierte un valor LLVM (ej: i32) al tipo_destino (ej: float o double) si no coinciden."""
        if valor.type == tipo_destino:
            return valor
        # De entero (i32) a float o double
        if valor.type == self.i32 and tipo_destino in (self.float, self.double):
            return self.builder.sitofp(valor, tipo_destino, name="int_a_float")
        # De float (32 bits) a double (64 bits)
        if valor.type == self.float and tipo_destino == self.double:
            return self.builder.fpext(valor, self.double, name="float_a_double")
        # De double (64 bits) a float (32 bits)
        if valor.type == self.double and tipo_destino == self.float:
            return self.builder.fptrunc(valor, self.float, name="double_a_float")
        return valor

    def _obtener_tipo_llvm(self, tipo_str):
        if tipo_str == "entero":
            return self.i32
        elif tipo_str == "flotante":
            return self.float
        elif tipo_str == "doble":
            return self.double
        else:
            raise Exception(f"Tipo no soportado en LLVM: {tipo_str}")

    def _igualar_tipos_binop(self, izq, der):
        """Si se opera entre int y float/double, promueve ambos al tipo más grande."""
        if izq.type == der.type:
            return izq, der
        if self.double in (izq.type, der.type):
            return self._convertir_a_tipo(izq, self.double), self._convertir_a_tipo(der, self.double)
        if self.float in (izq.type, der.type):
            return self._convertir_a_tipo(izq, self.float), self._convertir_a_tipo(der, self.float)
        return izq, der

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
        tipo_llvm = self._obtener_tipo_llvm(nodo.tipo)
        for nombre in nodo.lista_variables:
            if nombre in self.variables:
                raise Exception(f"Variable ya declarada: {nombre}")

            # Siempre reservar en el bloque entry para evitar fallos en while/if
            # A CHUSMEAR POR ACA EE cuando se pasa una variable como operando no reconoce el tipo
            #todo
            with self.builder.goto_entry_block():
                direccion = self.builder.alloca(tipo_llvm, name=nombre)

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
            izquierda, derecha = self._igualar_tipos_binop(izquierda, derecha)
            es_flotante = izquierda.type in (self.float, self.double)
            operador = nodo.operador.lower()
            print(izquierda.type)
            print(derecha.type)
            # En el caso de que sea una operacion entre flotantes hay que crear otro builder
            if es_flotante :
                if operador == "mas":
                    return self.builder.fadd(izquierda, derecha)
                elif operador == "menos":
                    return self.builder.fsub(izquierda, derecha)
                elif operador == "multiplicado":
                    return self.builder.fmul(izquierda, derecha)
                elif operador in ("dividido", "/"):
                    return self.builder.fdiv(izquierda, derecha)
            else:

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
            mapa_cmp = {
                "menor": "<",
                "mayor": ">",
                "menor igual": "<=", "<=": "<=",
                "mayor igual": ">=", ">=": ">=",
                "igual": "==", "==": "==",
                "distinto": "!=", "!=": "!="
            }
            if operador in mapa_cmp:
                simbolo = mapa_cmp[operador]
                if es_flotante:
                    return self.builder.fcmp_ordered(simbolo, izquierda, derecha)
                else:
                    return self.builder.icmp_signed(simbolo, izquierda, derecha)
            else:
                raise Exception(f"Operador desconocido: {operador}")
        elif isinstance(nodo, Negativo):
            val = self.generar_expresion(nodo.valor)
            if val.type in (self.float, self.double):
                return self.builder.fneg(val)
            return self.builder.neg(val)

        raise Exception(f"Expresion no soportada: {type(nodo).__name__}")

    # =====================================
    # Asignacion
    # =====================================

    def generar_asignacion(self, nodo):
        if nodo.id not in self.variables:
            raise Exception(f"Variable no declarada: {nodo.id}")

        valor = self.generar_expresion(nodo.valor)
        direccion = self.variables[nodo.id]
        tipo_variable = direccion.type.pointee
        if valor.type == self.i32 and tipo_variable in (self.float, self.double):
            valor = self.builder.sitofp(valor, tipo_variable)
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
            if valor.type in (self.float, self.double):
                if valor.type == self.float:
                    valor = self.builder.fpext(valor, self.double)
                ptr_fmt = self.builder.gep(self.fmt_float, [cero, cero], inbounds=True)
                self.builder.call(self.printf, [ptr_fmt, valor])
            else:
                # Lo que ya tenías para enteros:
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