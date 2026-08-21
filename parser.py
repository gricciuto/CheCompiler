from sly import Parser
from CheLexer import MiLexer
import ast_nodes as ast

class MiParser(Parser):
    # Traemos los tokens del Lexer
    tokens = MiLexer.tokens

    # Definimos la precedencia para evitar ambigüedades matemáticas
    precedence = (
        ('left', LT, GT, EQ, GE, LE, NE),
        ('left', MAS, MENOS),
        ('left', POR, DIVIDIDO),
        ('right', UMENOS), # Para números negativos
    )

    # --- Regla de Entrada ---
    @_('programa')
    def start(self, p):
        return p.programa

    @_('bloque', 'instruccion')
    def programa(self, p):
        return p[0]

    # --- Manejo de Bloques ---
    @_('COMIENZA instrucciones TERMINA')
    def bloque(self, p):
        return ast.Bloque(p.instrucciones)

    @_('instruccion', 'instrucciones instruccion')
    def instrucciones(self, p):
        if len(p) == 1:
            return [p.instruccion]
        else:
            p.instrucciones.append(p.instruccion)
            return p.instrucciones

    # --- Tipos de Instrucciones ---
    @_('declaracion PUNTO_Y_COMA',
       'asignacion PUNTO_Y_COMA',
       'seleccion PUNTO_Y_COMA',
       'iteracion PUNTO_Y_COMA',
       'invocacion PUNTO_Y_COMA',
       'expresion PUNTO_Y_COMA')
    def instruccion(self, p):
        return p[0]

    # --- Declaración de Variables ---
    # Soporta: _se_declaran_con_el_tipo_ entero _las_variables_ a b c
    @_('SE_DECLARAN TIPO LAS_VARIABLES lista_ids')
    def declaracion(self, p):
        # Retornamos un nodo de Declaración.
        # Si tu AST soporta múltiples IDs, pasamos la lista.
        return ast.Declaracion(p.TIPO, p.lista_ids)

    @_('NAME', 'lista_ids NAME')
    def lista_ids(self, p):
        if len(p) == 1:
            return [p.NAME]
        else:
            p.lista_ids.append(p.NAME)
            return p.lista_ids

    # --- Asignación ---
    @_('NAME SE_VUELVE expresion')
    def asignacion(self, p):
        return ast.Asignacion(p.NAME, p.expresion)

    # --- Control de Flujo (If y While) ---
    @_('SI expresion ENTONCES bloque SINO bloque')
    def seleccion(self, p):
        return ast.IfStatement(p.expresion, p.bloque0, p.bloque1)

    @_('MIENTRAS expresion bloque')
    def iteracion(self, p):
        return ast.WhileStatement(p.expresion, p.bloque)

    # --- Expresiones y Operaciones ---
    @_('expresion MAS expresion',
       'expresion MENOS expresion',
       'expresion POR expresion',
       'expresion DIVIDIDO expresion',
       'expresion LT expresion',
       'expresion GT expresion',
       'expresion EQ expresion',
       'expresion GE expresion',
       'expresion LE expresion',
       'expresion NE expresion')
    def expresion(self, p):
        # p[1] contiene el nombre del token del operador (ej: 'MAS')
        return ast.BinOp(p[1], p.expresion0, p.expresion1)

    # --- Invocación de Funciones ---
    @_('LLAMA_A NAME PARAMETROS ABRE_P expresion CIERRA_P')
    def invocacion(self, p):
        return ast.Call(p.NAME, [p.expresion])

    # --- Átomos (Valores base) ---
    @_('NUMBER')
    def expresion(self, p):
        return ast.Numero(p.NUMBER)

    @_('NAME')
    def expresion(self, p):
        return ast.Variable(p.NAME)

    @_('ABRE_P expresion CIERRA_P')
    def expresion(self, p):
        return p.expresion

    @_('MENOS expresion %prec UMENOS')
    def expresion(self, p):
        return ast.BinOp('MUL', ast.Numero(-1), p.expresion)

    # --- Manejo de Errores Sintácticos ---
    def error(self, p):
        if p:
            raise SyntaxError(f"Error de sintaxis en '{p.value}' (línea {p.lineno})")
        else:
            raise SyntaxError("Error de sintaxis: Fin de archivo inesperado")