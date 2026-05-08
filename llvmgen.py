import llvmlite.ir as ir
import llvmlite.binding as llvm
import ast_nodes as ast
import ctypes


class LLVMGen:
    def __init__(self):
        # Configuración básica de LLVM
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        self.module = ir.Module(name="jit_module")
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        self.module.triple = llvm.get_process_triple()
        self.module.data_layout = target_machine.target_data

        # Diccionario persistente para variables
        self.globals = {}

        # Inicializamos el motor de ejecución
        backing_mod = llvm.parse_assembly("")
        self.engine = llvm.create_mcjit_compiler(backing_mod, target_machine)

    def generate_and_execute(self, node):
        """Envuelve el nodo en una función anónima y la ejecuta inmediatamente."""
        # Creamos un tipo de función que devuelve un entero de 32 bits
        func_type = ir.FunctionType(ir.IntType(32), [])
        func_name = f"anon_func_{id(node)}"
        func = ir.Function(self.module, func_type, name=func_name)

        block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)

        # Generamos el código IR visitando el nodo
        resultado = self.visit(node)

        # Aseguramos que toda función termine en un return
        if resultado is None or isinstance(resultado, ir.GlobalVariable):
            resultado = ir.Constant(ir.IntType(32), 0)

        # Si el resultado es un booleano de LLVM (i1), lo convertimos a i32 para el return
        if resultado.type == ir.IntType(1):
            resultado = self.builder.zext(resultado, ir.IntType(32))

        self.builder.ret(resultado)

        # --- JIT Compilation ---
        mod_obj = llvm.parse_assembly(str(self.module))
        mod_obj.verify()

        self.engine.add_module(mod_obj)
        self.engine.finalize_object()

        func_ptr = self.engine.get_function_address(func_name)
        c_func = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)

        res_final = c_func()

        # Limpieza: removemos el módulo del engine para poder agregar el siguiente con el estado actualizado
        self.engine.remove_module(mod_obj)

        return res_final

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        return None

    def visit_Numero(self, node):
        return ir.Constant(ir.IntType(32), int(node.valor))

    def visit_Declaracion(self, node):
        # Mapeamos los tipos de tu lenguaje a tipos de LLVM
        llvm_type = ir.IntType(32)  # Por defecto entero
        if node.tipo in ['flotante', 'doble']:
            llvm_type = ir.DoubleType()

        # Iteramos la lista de nombres que viene del nuevo Parser
        for nombre in node.nombres:
            var = ir.GlobalVariable(self.module, llvm_type, name=nombre)
            var.linkage = 'internal'
            var.initializer = ir.Constant(llvm_type, 0)
            self.globals[nombre] = var
        return None

    def visit_Variable(self, node):
        ptr = self.globals[node.nombre]
        return self.builder.load(ptr, name=node.nombre)

    def visit_Asignacion(self, node):
        val = self.visit(node.valor)
        ptr = self.globals[node.nombre]

        # Casting básico: si la variable es float y el valor int, convertimos
        if ptr.type.pointee == ir.DoubleType() and val.type == ir.IntType(32):
            val = self.builder.sitofp(val, ir.DoubleType())

        self.builder.store(val, ptr)
        return val

    def visit_BinOp(self, node):
        izq = self.visit(node.izq)
        der = self.visit(node.der)

        # Mapeo de operadores en español a instrucciones LLVM
        ops = {
            'MAS': self.builder.add,
            'MENOS': self.builder.sub,
            'POR': self.builder.mul,
            'DIVIDIDO': self.builder.sdiv,
            'LT': lambda a, b: self.builder.icmp_signed('<', a, b),
            'GT': lambda a, b: self.builder.icmp_signed('>', a, b),
            'EQ': lambda a, b: self.builder.icmp_signed('==', a, b),
            'GE': lambda a, b: self.builder.icmp_signed('>=', a, b),
            'LE': lambda a, b: self.builder.icmp_signed('<=', a, b),
            'NE': lambda a, b: self.builder.icmp_signed('!=', a, b),
            'MENOS_UNARIO': self.builder.sub
        }

        op_func = ops.get(node.op)
        if op_func:
            return op_func(izq, der)
        return None

    def visit_IfStatement(self, node):
        cond_val = self.visit(node.condicion)

        with self.builder.if_else(cond_val) as (then, otherwise):
            with then:
                self.visit(node.cuerpo)
            with otherwise:
                if node.cuerpo_sino:
                    self.visit(node.cuerpo_sino)
        return None

    def visit_WhileStatement(self, node):
        # Creamos bloques para el bucle
        current_func = self.builder.function
        loop_cond = current_func.append_basic_block(name="loop_cond")
        loop_body = current_func.append_basic_block(name="loop_body")
        loop_end = current_func.append_basic_block(name="loop_end")

        # Salto inicial a la condición
        self.builder.branch(loop_cond)

        # Bloque de condición
        self.builder.position_at_end(loop_cond)
        cond_val = self.visit(node.condicion)
        self.builder.cbranch(cond_val, loop_body, loop_end)

        # Bloque de cuerpo
        self.builder.position_at_end(loop_body)
        self.visit(node.cuerpo)
        self.builder.branch(loop_cond)

        # Continuar tras el loop
        self.builder.position_at_end(loop_end)
        return None

    def visit_Bloque(self, node):
        for instr in node.instrucciones:
            self.visit(instr)
        return None