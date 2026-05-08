class Node:
    pass

class Numero(Node):
    def __init__(self, valor):
        self.valor = valor

class Variable(Node):
    def __init__(self, nombre):
        self.nombre = nombre

class BinOp(Node):
    def __init__(self, op, izq, der):
        self.op = op
        self.izq = izq
        self.der = der

class Declaracion(Node):
    def __init__(self, tipo, nombres):
        self.tipo = tipo
        self.nombres = nombres # Lista de IDs (ej: ['a', 'b'])

class Asignacion(Node):
    def __init__(self, nombre, valor):
        self.nombre = nombre
        self.valor = valor

class IfStatement(Node):
    def __init__(self, condicion, cuerpo, cuerpo_sino=None):
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.cuerpo_sino = cuerpo_sino

class WhileStatement(Node):
    def __init__(self, condicion, cuerpo):
        self.condicion = condicion
        self.cuerpo = cuerpo

class Bloque(Node):
    def __init__(self, instrucciones):
        self.instrucciones = instrucciones

class Call(Node):
    def __init__(self, nombre, argumentos):
        self.nombre = nombre
        self.argumentos = argumentos