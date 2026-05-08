import ast_nodes as ast


class SemanticError(Exception):
    pass


class Checker:
    def __init__(self):
        # Entorno persistente: mapea nombre de variable -> tipo
        self.env = {}

    def visit(self, node):
        # Si el nodo es una lista (sucede en declaraciones), visitamos cada elemento
        if isinstance(node, list):
            for n in node:
                self.visit(n)
            return

        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        # Si el nodo no tiene un visit_ específico, no hacemos nada o tiramos error
        pass

    def visit_Bloque(self, node):
        for instruccion in node.instrucciones:
            self.visit(instruccion)

    def visit_Declaracion(self, node):
        # Ahora node.nombres es una LISTA (gracias al Parser y AST nuevos)
        for nombre in node.nombres:
            if nombre in self.env:
                raise SemanticError(f"Error Semántico: La variable '{nombre}' ya fue declarada.")

            # Guardamos el tipo (entero, flotante, etc.)
            self.env[nombre] = node.tipo
            print(f"[CHECKER] Variable '{nombre}' registrada como {node.tipo}")

    def visit_Asignacion(self, node):
        if node.nombre not in self.env:
            raise SemanticError(f"Error Semántico: La variable '{node.nombre}' no ha sido declarada.")

        # Validamos que la expresión que se asigna sea semánticamente correcta
        self.visit(node.valor)

    def visit_Variable(self, node):
        if node.nombre not in self.env:
            raise SemanticError(f"Error Semántico: Uso de variable '{node.nombre}' sin declarar.")
        return self.env[node.nombre]

    def visit_BinOp(self, node):
        # En un compilador real, aquí chequearías que los tipos sean compatibles
        # (ej: no sumar un string con un entero)
        self.visit(node.izq)
        self.visit(node.der)

    def visit_IfStatement(self, node):
        self.visit(node.condicion)
        self.visit(node.cuerpo)
        if node.cuerpo_sino:
            self.visit(node.cuerpo_sino)

    def visit_WhileStatement(self, node):
        self.visit(node.condicion)
        self.visit(node.cuerpo)

    def visit_Call(self, node):
        # Para el proyecto final, podrías verificar si la función existe.
        # Por ahora, solo validamos los argumentos que se le pasan.
        for arg in node.argumentos:
            self.visit(arg)

    def visit_Numero(self, node):
        # Los números siempre son válidos
        pass