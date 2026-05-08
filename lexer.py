from sly import Lexer


class MiLexer(Lexer):
    # Definimos el set de tokens que el Parser reconocerá
    tokens = {
        NAME, NUMBER, COMIENZA, TERMINA, PUNTO_Y_COMA,
        TIPO, LAS_VARIABLES, SE_DECLARAN, SE_VUELVE,
        SI, ENTONCES, SINO, MIENTRAS, LLAMA_A, PARAMETROS,
        ABRE_P, CIERRA_P, MAS, MENOS, POR, DIVIDIDO,
        LT, GT, EQ, GE, LE, NE
    }

    # Caracteres a ignorar (espacios y tabs)
    ignore = ' \t'

    # --- Palabras Clave y Delimitadores (Tokens Largos) ---
    # Es importante poner los más largos primero para que el Regex no matchee partes
    COMIENZA = r'_comienza_bloque_'
    TERMINA = r'_termina_bloque_'
    PUNTO_Y_COMA = r'_punto_y_coma_'
    SE_DECLARAN = r'_se_declaran_con_el_tipo_'
    LAS_VARIABLES = r'_las_variables_'
    SE_VUELVE = r'_se_vuelve_'
    SI = r'_si_'
    ENTONCES = r'_entonces_'
    SINO = r'_sino_'
    MIENTRAS = r'_mientras_que_'
    LLAMA_A = r'_se_llama_a'
    PARAMETROS = r'_con_parametros_'
    ABRE_P = r'_abre_parentesis_'
    CIERRA_P = r'_cierra_parentesis_'

    # --- Operadores Aritméticos ---
    MAS = r'_mas_'
    MENOS = r'_menos_'
    POR = r'_por_'
    DIVIDIDO = r'_dividido_'

    # --- Comparadores Lógicos ---
    GE = r'_es_mayor_o_igual_que_'
    LE = r'_es_menor_o_igual_que_'
    EQ = r'_es_igual_que_'
    NE = r'_es_distinto_'
    LT = r'_es_menor_que_'
    GT = r'_es_mayor_que_'

    # --- Tipos de Datos (Usamos Regex con pipe) ---
    TIPO = r'entero|largo|flotante|doble|cadena'

    # --- Identificadores (Nombres de variables) ---
    NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'

    # --- Números (Enteros y Flotantes) ---
    @_(r'\d+(\.\d+)?')
    def NUMBER(self, t):
        # Si tiene un punto, lo convertimos a float, si no a int
        if '.' in t.value:
            t.value = float(t.value)
        else:
            t.value = int(t.value)
        return t

    # --- Manejo de saltos de línea para reportar errores ---
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    # --- Manejo de Errores ---
    def error(self, t):
        # Levantamos una excepción que el main.py pueda atrapar
        raise SyntaxError(f"Carácter ilegal '{t.value[0]}' en la línea {self.lineno}")