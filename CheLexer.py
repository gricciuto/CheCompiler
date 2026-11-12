from sly import Lexer 

class CheLexer(Lexer):
    # nombres de los tokens. 
    tokens = {MAS,MENOS,POR,DIVISION,IGUAL,PARENTESIS_IZQ,PARENTESIS_DER,
              NUMERO, PUNTO_Y_COMA, ASIGNACION, IF, ELSE,THEN, WHILE, FUNCION, MAYOR, MENOR,
              MAYOR_IGUAL,DISTINTO, MENOR_IGUAL, TIPO, LLAVE_IZQ, LLAVE_DER, CADENA, IMPRIMIR, BEGIN, END, ID, Y, INVOCO,CON_PARAMETROS,DECLARO,LAS_VARIABLES, PUNTO, COMA}
    ignore = ' \t' 
    ignore_comment = r'\#.*'
    @_(r'\bes\b|\bque\b')
    def FILLER(self, t):
        pass  # retorna None → el token se descarta
    # expresiones regulares de los tokens
    CON_PARAMETROS = r'\bcon\s+parametros\b'
    INVOCO = r'\b(?:invoco|llamo a)\b'
    DECLARO =r'\b(?:declaro|se declara|se presentan|aparecieron|se declaran)\b'
    LAS_VARIABLES =  r'\b(?:las variables|la variable)\b'
    Y = r'\by\b'
    MAS = r'\bmas\b'
    MENOS = r'\bmenos\b'
    POR = r'\bmultiplicado\b'
    DIVISION = r'\bdividido\b'
    IGUAL = r'\bigual\b'
    PARENTESIS_IZQ = r'\babro parentesis\b'
    PARENTESIS_DER =r'\bcierro parentesis\b'
    PUNTO_Y_COMA = r'\bpunto y coma\b'
    PUNTO = r'\bpunto\b'
    COMA = r'\bcoma\b'
    #Hay que corregir esto para que se reconozcan los flotantes
    @_(r'\d+')
    def NUMERO(self, t):
        t.value = int(t.value)
        return t

    ASIGNACION = r'\ble asigno\b'
    ELSE = r'\bsino\b'
    IF = r'\bsi\b'
    THEN = r'\bentonces\b'
    WHILE = r'\bmientras\b'
    FUNCION = r'\bfuncion\b'
    MAYOR_IGUAL = r'\bmayor igual\b'
    DISTINTO = r'\bdistinto\b'
    MENOR_IGUAL = r'\bmenor igual\b'
    MAYOR = r'\bmayor\b'
    MENOR = r'\bmenor\b'
    TIPO = r'\b(?:entero|flotante|cadena|doble)\b' # dejamos estos tipos nomas, estamos abierto a cambios .
    LLAVE_IZQ = r'\babro llave\b'
    LLAVE_DER = r'\bcierro llave\b'
    IMPRIMIR = r'\b(?:imprimo|lo pongo en la epson|mostrar por pantalla|pantalleame|escupi)\b'
    BEGIN = r'\bcomienza\b'
    END = r'\btermina\b'
    CADENA = r'"[^"]*"'
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Line number tracking
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print('Line %d: Bad character %r' % (self.lineno, t.value[0]))
        self.index += 1
        raise SyntaxError


    
    
 