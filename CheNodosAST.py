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

