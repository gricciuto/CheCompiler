import ast

from sly import Parser
from CheLexer import CheLexer

class CheParser(Parser):
    #Lista de tokens
    tokens = CheLexer.tokens
    #Precedencia
    precedence = (
        ('left', MENOR, MAYOR, IGUAL, MAYOR_IGUAL, MENOR_IGUAL, DISTINTO),
        ('left', MAS, MENOS),
        ('left', POR, DIVISION)
    )
    @_('termino MAS factor','termino MENOS factor')
    def termino(self,p):
        return ast.BinOp(p.termino, p[1], p.factor)
    @_('factor')
    def termino(self,p):
        return p.factor

    @_('factor POR atomo','factor DIVISION atomo')
    def factor(self,p):
        return ast.BinOp(p.factor,p[1],p.atomo)

    @_('MENOS atomo')
    def atomo(self,p):
        return -p.atomo
    @_('NUMERO')
    def atomo(self,p):
        return ast.Valor(p.NUMERO)




