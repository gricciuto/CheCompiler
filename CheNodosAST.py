class Nodo:
    def imprimir(self):
        pass
    pass
class Valor(Nodo):
    def __init__(self,valor):
        self.valor = valor
    def imprimir(self,prefijo):
        print(f"{prefijo}VALOR: ",self.valor)
class BinOp(Nodo):
    def __init__(self,valora, operador, valorb):
        self.valora = valora
        self.valorb = valorb
        self.operador = operador
    def imprimir(self):
        print("OP BINARIA: ",self.valora, self.operador, self.valorb)
class InstruccionMientras (Nodo):
    def __init__(self,condicion,cuerpo):
        self.condicion = condicion
        self.cuerpo = cuerpo
    def imprimir(self):
        print("MIENTRAS: ",self.condicion, "HACER: ", self.cuerpo)
class InstruccionSi (Nodo):
    def __init__(self,condicion,bloqueverdadero,bloquefalso):
        self.condicion = condicion
        self.bloqueverdadero = bloqueverdadero
        self.bloquefalso = bloquefalso
    def imprimir(self):
        print("SI: ", self.condicion, "HACER: ", self.bloqueverdadero, "SINO: ", self.bloquefalso)
class Asignacion(Nodo):
    def __init__(self,id,valor):
        self.id = id
        self.valor = valor
    def imprimir(self):
        print("ASIGNACION A: ", self.id, " EL VALOR: ", self.valor)
class Invocacion(Nodo):
    def __init__(self,nombre,argumento, lineno=None):
        self.nombre = nombre
        self.argumento = argumento
        self.lineno = lineno
    def imprimir(self):
        print("INVOCO: ",self.nombre, "CON ARGUMENTOS: ", self.argumento)
class Declaracion (Nodo):
    def __init__(self,tipo, lista_variables):
        self.tipo = tipo
        self.lista_variables = lista_variables
    def imprimir(self):
        print("DECLARO TIPO: ", self.tipo, " VARIABLES: ", self.lista_variables)
class Imprimir(Nodo):
    def __init__(self,valor, lineno):
        self.lineno = lineno
        self.valor = valor
    def imprimir(self):
        print("IMPRESION: ",self.valor)
class Variable(Nodo):
    def __init__(self, nombre, lineno):
        self.lineno = lineno
        self.nombre = nombre
    def imprimir(self):
        print("VARIABLE: ", self.nombre)

