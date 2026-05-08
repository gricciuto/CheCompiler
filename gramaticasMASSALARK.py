#
# This example shows how to write a basic calculator with variables.
#

from lark import Lark, Transformer, v_args


try:
    input = raw_input   # For Python2 compatibility
except NameError:
    pass

### Reglas quitadas de la gramatica
#     ?expresion: termino
#          | NAME "=" termino    
#?atomo: NUMBER           
#         | "-" atomo         
#         | NAME             
#         | "(" termino ")"



calc_grammar = """
    
    ?start: programa 
    ?programa: instruccion 
              | bloque 
    ?instrucciones: instruccion | instrucciones instruccion
    ?bloque: "_comienza_bloque_" instrucciones "_termina_bloque_" 
             
    ?instruccion: declaracion "_punto_y_coma_"
              | invocacion "_punto_y_coma_"
              | asignacion "_punto_y_coma_"              
              | seleccion "_punto_y_coma_"     
              | iteracion "_punto_y_coma_"         
    ?declaracion: "_se_declaran_con_el_tipo_" tipo "_las_variables_" listavariables
    ?tipo: "entero" | "largo" | "flotante" | "doble" | "cadena"
    ?listavariables: NAME | listavariables NAME                                 
    ?invocacion: "_se_llama_a" NAME "_con_parametros_" "_abre_parentesis_" expresion "_cierra_parentesis_"                
    ?asignacion: NAME "_se_vuelve_" expresion                                                                   
    ?seleccion: "_si_" comparacion "_entonces_" bloque "_punto_y_coma_" "_sino_" bloque
    ?iteracion: "_mientras_que_" comparacion bloque 
    ?expresion: expresionsimple | comparacion    
    ?comparacion: expresionsimple comparador expresionsimple 
    ?comparador: "_es_menor_que_" | "_es_mayor_que_" | "_es_igual_que_" | "_es_mayor_o_igual_que_" | "_es_menor_o_igual_que_" | "_es_distinto_"             
    ?expresionsimple: termino
    ?termino: factor
        | termino "_mas_" factor
        | termino "_menos_" factor   

    ?factor: atomo
        | factor "_por_" atomo  
        | factor "_dividido_" atomo
        | invocacion

    ?atomo: NUMBER           
         | "_menos_" atomo         
         | NAME          

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE

    %ignore WS_INLINE
"""

@v_args(inline=True)    # Affects the signatures of the methods
class CalculateTree(Transformer):
    from operator import add, sub, mul, truediv as div, neg
    number = float

    def __init__(self):
        self.vars = {}

    def assign_var(self, name, value):
        self.vars[name] = value
        return value

    def var(self, name):
        return self.vars[name]


calc_parser = Lark(calc_grammar, parser='lalr', transformer=CalculateTree())
calc = calc_parser.parse

def test():
    print(calc("_comienza_bloque_ _se_declaran_con_el_tipo_ entero _las_variables_ a b _punto_y_coma_ _se_declaran_con_el_tipo_ largo _las_variables_ c d _punto_y_coma_a _se_vuelve_ b _punto_y_coma_ b _se_vuelve_ c _mas_ 1 _punto_y_coma_ d _se_vuelve_ _se_llama_a f _con_parametros_ _abre_parentesis_ a _cierra_parentesis_ _punto_y_coma_ _si_ a _es_igual_que_ 2 _entonces_ _comienza_bloque_ a _se_vuelve_ 1 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _sino_ _comienza_bloque_ a _se_vuelve_ 2 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _mientras_que_ a _es_mayor_o_igual_que_ 1 _comienza_bloque_ d _se_vuelve_ d _mas_ 3 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _termina_bloque_"))    

    '''
    Programa 1    
    _comienza_bloque_ _se_declaran_con_el_tipo_ entero _las_variables_ a b c d _punto_y_coma_ a _se_vuelve_ b _punto_y_coma_ b _se_vuelve_ c _mas_ 1 _punto_y_coma_ d _se_vuelve_ _se_llama_a f _con_parametros_ _abre_parentesis_ a _cierra_parentesis_ _punto_y_coma_ _si_ a _es_igual_que_ 2 _entonces_ _comienza_bloque_ a _se_vuelve_ 1 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _sino_ _comienza_bloque_ a _se_vuelve_ 2 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _mientras_que_ a _es_mayor_o_igual_que_ 1 _comienza_bloque_ d _se_vuelve_ d _mas_ 3 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _termina_bloque_
    '''

    '''
    Programa 2
    _comienza_bloque_ _se_declaran_con_el_tipo_ flotante _las_variables_ e f g h _punto_y_coma_  g _se_vuelve_ h _menos_ 1 _punto_y_coma_ e _se_vuelve_ _se_llama_a z _con_parametros_ _abre_parentesis_ 2 _cierra_parentesis_ _punto_y_coma_ _mientras_que_ e _es_mayor_o_igual_que_ 2 _comienza_bloque_ h _se_vuelve_ e _por_ 7 _punto_y_coma_ f _se_vuelve_ 1 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _si_ e _es_igual_que_ f _entonces_ _comienza_bloque_ h _se_vuelve_ 3 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _sino_ _comienza_bloque_ e _se_vuelve_ 1 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _termina_bloque_
    '''

    '''
    Programa 3
    _comienza_bloque_ _se_declaran_con_el_tipo_ doble _las_variables_ a b _punto_y_coma_ _se_declaran_con_el_tipo_ entero _las_variables_ c d _punto_y_coma_ a _se_vuelve_ 5 _menos_ 1 _punto_y_coma_ b _se_vuelve_ _se_llama_a w _con_parametros_ _abre_parentesis_ b _cierra_parentesis_ _punto_y_coma_ _mientras_que_ a _es_mayor_o_igual_que_ b _comienza_bloque_ c _se_vuelve_ a _dividido_ 2 _punto_y_coma_ d _se_vuelve_ a _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _si_ b _es_igual_que_ a _entonces_ _comienza_bloque_ a _se_vuelve_ d _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _sino_ _comienza_bloque_ d _se_vuelve_ 2 _punto_y_coma_ _termina_bloque_ _punto_y_coma_ _termina_bloque_
    '''


if __name__ == '__main__':
    test()

