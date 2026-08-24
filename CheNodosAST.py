class Nodo:
    pass

class Valor(Nodo):
    def __init__(self,valor):
        self.valor = valor

class BinOp(Nodo):
    def __init__(self,valora, operador, valorb):
        self.valora = valora
        self.valorb = valorb
        self.operador = operador
class InstruccionMientras (Nodo):
    def __init__(self,condicion,cuerpo):
        self.condicion = condicion
        self.cuerpo = cuerpo
class InstruccionSi (Nodo):
    def __init__(self,condicion,bloqueverdadero,bloquefalso):
        self.condicion = condicion
        self.bloqueverdadero = bloqueverdadero
        self.bloquefalso = bloquefalso
class Asignacion(Nodo):
    def __init__(self,id,valor):
        self.id = id
        self.valor = valor
class Invocacion(Nodo):
    def __init__(self,nombre,argumento):
        self.nombre = nombre
        self.argumento = argumento
class Declaracion (Nodo):
    def __init__(self,tipo, lista_variables):
        self.tipo = tipo
        self.lista_variables = lista_variables
class Imprimir(Nodo):
    def __init__(self,valor):
        self.valor = valor
class Variable(Nodo):
    def __init__(self, nombre):
        self.nombre = nombre

