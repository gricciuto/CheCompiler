import CheNodosAST as ast

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
    @_('bloque')
    def programa(self,p):
        return p[0]
    @_('instruccion')
    def programa(self,p):
        return [p.instruccion]
    @_('instruccion', 'instrucciones instruccion')
    def instrucciones(self,p):
        if len(p) == 1:
            return [p.instruccion]
        else:
            p.instrucciones.append(p.instruccion)
            return p.instrucciones
    @_('BEGIN instrucciones END')
    def bloque(self,p):
        return p.instrucciones
    @_('declaracion PUNTO_Y_COMA', 'invocacion PUNTO_Y_COMA', 'asignacion PUNTO_Y_COMA', 'seleccion', 'iteracion PUNTO_Y_COMA', 'imprimir PUNTO_Y_COMA')
    def instruccion (self,p):
        return p[0]
    @_('IMPRIMIR PARENTESIS_IZQ expresion PARENTESIS_DER')
    def imprimir(self,p):
        return ast.Imprimir(p.expresion, lineno = p.lineno)
    @_('IMPRIMIR PARENTESIS_IZQ CADENA PARENTESIS_DER')
    def imprimir(self,p):
        # con [1:-1] se les saca las comillas que trae de el lexer
        return ast.Imprimir(ast.Valor(p.CADENA[1:-1], 'cadena', lineno= p.lineno), lineno = p.lineno)
    @_('DECLARO TIPO LAS_VARIABLES listavariables')
    def declaracion(self,p):
        return ast.Declaracion(p.TIPO,p.listavariables, lineno= p.lineno)
    @_('TIPO')
    def tipo(self,p):
        return p.TIPO
    @_('ID', 'listavariables ID')
    def listavariables(self, p):
        if len(p) == 1:
            return [p.ID]
        else:
            p.listavariables.append(p.ID)
            return p.listavariables
    @_('INVOCO ID CON_PARAMETROS PARENTESIS_IZQ expresion PARENTESIS_DER')
    def invocacion(self,p):
        return ast.Invocacion(p.ID,p.expresion, lineno = p.lineno) #ESTE LINENO es para contar las lineas.

    @_('ID ASIGNACION expresion')
    def asignacion(self,p):
        return ast.Asignacion(p.ID,p.expresion, lineno= p.lineno)
    @_(' IF comparacion THEN bloque PUNTO_Y_COMA ELSE bloque PUNTO_Y_COMA')
    def seleccion(self,p):
        return ast.InstruccionSi(p.comparacion,p.bloque0,p.bloque1,lineno=p.lineno)
    @_('IF comparacion THEN bloque PUNTO_Y_COMA')
    def seleccion (self,p):
        return ast.InstruccionSi(p.comparacion,p.bloque,[], lineno=p.lineno)
    @_('WHILE comparacion bloque')
    def iteracion(self,p):
        return ast.InstruccionMientras(p.comparacion,p.bloque, lineno=p.lineno)
    @_('expresionsimple', 'comparacion')
    def expresion(self,p):
        return p[0]
    @_('expresionsimple comparador expresionsimple')
    def comparacion(self,p):
        return ast.BinOp(p.expresionsimple0,p[1],p.expresionsimple1, lineno=p.expresionsimple0.lineno)
    @_('MENOR','MAYOR','IGUAL','MENOR_IGUAL','DISTINTO','MAYOR_IGUAL')
    def comparador(self,p):
        return p[0]
    @_('termino')
    def expresionsimple(self,p):
        return p.termino
    @_('termino MAS factor','termino MENOS factor')
    def termino(self,p):
        return ast.BinOp(p.termino, p[1], p.factor, lineno=p.lineno)
    @_('factor')
    def termino(self,p):
        return p.factor
    @_('atomo')
    def factor(self,p):
        return p.atomo
    @_('invocacion')
    def factor(self,p):
        return p.invocacion
    @_('factor POR atomo','factor DIVISION atomo')
    def factor(self,p):
        return ast.BinOp(p.factor,p[1],p.atomo, lineno= p.lineno)
    @_('ID')
    def atomo(self,p):
        return ast.Variable(p.ID, lineno = p.lineno)
    @_('MENOS atomo')
    def atomo(self,p):
        return ast.Negativo(p.atomo,lineno = p.lineno)
    @_('PARENTESIS_IZQ expresion PARENTESIS_DER')
    def atomo(self, p):
        return p.expresion
    @_('NUMERO')
    def atomo(self,p):
        tipo = 'entero' if isinstance(p.NUMERO, int) else 'flotante'
        return ast.Valor(p.NUMERO,tipo,lineno = p.lineno)
    @_('NUMERO PUNTO NUMERO')
    def atomo(self,p):
        valor = float(f"{p.NUMERO0}.{p.NUMERO1}")
        return ast.Valor(valor,'flotante',lineno = p.lineno)
    def error(self,p):
        if p:
            raise SyntaxError(f"Error de sintaxis en '{p.value}' (linea {p.lineno})")
        raise SyntaxError("Error de sintaxis: fin de archivo inesperado")
    




