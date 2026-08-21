from sly import Lexer 

class CheLexer(Lexer):
    # nombres de los tokens. 
    tokens = {MAS,MENOS,POR,DIVISION,IGUAL,PARENTESIS_IZQ,PARENTESIS_DER,
              NUMERO, PUNTO_Y_COMA, ASIGNACION, IF, ELSE,THEN, WHILE, FUNCION, MAYOR, MENOR,
              MAYOR_IGUAL,DISTINTO, MENOR_IGUAL, TIPO, LLAVE_IZQ, LLAVE_DER, CADENA, IMPRIMIR, BEGIN, END, ID}
    ignore = ' \t' 
    ignore_comment = r'\#.*'
    ignore_newline = r'\n+'
    # expresiones regulares de los tokens
    MAS = "mas"
    MENOS = "menos"
    POR = "multiplicado"
    DIVISION = "dividido"
    IGUAL = "igual"
    PARENTESIS_IZQ = "abro parentesis"
    PARENTESIS_DER ="cierro parentesis"
    @_(r'\d+')
    def NUMERO(self, t):
        t.value = int(t.value)
        return t
    PUNTO_Y_COMA = "punto y coma"
    ASIGNACION = "le asigno"
    IF = "si"
    ELSE = "sino"
    THEN = "entonces"
    WHILE = "mientras"
    FUNCION = "funcion"
    MAYOR = "mayor"
    MENOR = "menor"
    MAYOR_IGUAL = "mayor igual"
    DISTINTO = "distinto"
    MENOR_IGUAL = "menor igual"
    TIPO = r'entero|flotante|cadena'
    LLAVE_IZQ = "abro llave"
    LLAVE_DER = "cierro llave"
    IMPRIMIR = r'imprimo|lo pongo en la epson|mostrar por pantalla|pantalleame|escupi'
    BEGIN = "comienza"
    END = "termina"
    CADENA = r'"[^"]*"'
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Line number tracking
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print('Line %d: Bad character %r' % (self.lineno, t.value[0]))
        raise SyntaxError
        self.index += 1


    
    
 