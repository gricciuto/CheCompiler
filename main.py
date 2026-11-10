if __name__ == "__main__":
    import sys
    from CheLexer import CheLexer
    from CheParser import CheParser
    from CheChecker import check_program, SemanticError
    from CheGenCodIR import CodeGenerator

    lexer = CheLexer()
    parser = CheParser()
    generador = CodeGenerator()

    codigo = '''comienza
      declaro entero las variables a b c punto y coma
      a le asigno 10 punto y coma
      b le asigno "hola" punto y coma
      c le asigno a mas b multiplicado 2 punto y coma
      si c mayor 15 entonces comienza
        a le asigno 1 punto y coma
      termina punto y coma
      sino comienza
        b le asigno 2 punto y coma
      termina punto y coma
      mientras a mayor b comienza
        a le asigno a menos 1 punto y coma
      termina punto y coma
      imprimo abro parentesis a cierro parentesis punto y coma
    termina'''

    def mostrar_ast(nodo, indent=0):
        prefijo = "  " * indent
        nombre = type(nodo).__name__
        
        tipo_str = f" [tipo: {nodo.tipo}]" if getattr(nodo, "tipo", None) else ""

        if nombre == "Valor":
            nodo.imprimir(prefijo)
        elif nombre == "Variable":
            print(f"{prefijo}Variable({nodo.nombre}){tipo_str}")
        elif nombre == "Negativo":
            print(f"{prefijo}Negativo{tipo_str}")
            mostrar_ast(nodo.valor, indent + 1)
        elif nombre == "BinOp":
            print(f"{prefijo}BinOp({nodo.operador}){tipo_str}")
            mostrar_ast(nodo.valora, indent + 1)
            mostrar_ast(nodo.valorb, indent + 1)
        elif nombre == "Declaracion":
            print(f"{prefijo}Declaracion({nodo.tipo})")
            for v in nodo.lista_variables:
                print(f"{prefijo}  {v}")
        elif nombre == "Asignacion":
            print(f"{prefijo}Asignacion({nodo.id}){tipo_str}")
            mostrar_ast(nodo.valor, indent + 1)
        elif nombre == "InstruccionSi":
            print(f"{prefijo}Si")
            print(f"{prefijo}  Condicion:")
            mostrar_ast(nodo.condicion, indent + 2)
            print(f"{prefijo}  Entonces:")
            for inst in nodo.bloqueverdadero:
                mostrar_ast(inst, indent + 3)
            print(f"{prefijo}  Sino:")
            for inst in nodo.bloquefalso:
                mostrar_ast(inst, indent + 3)
        elif nombre == "InstruccionMientras":
            print(f"{prefijo}Mientras")
            print(f"{prefijo}  Condicion:")
            mostrar_ast(nodo.condicion, indent + 2)
            print(f"{prefijo}  Cuerpo:")
            for inst in nodo.cuerpo:
                mostrar_ast(inst, indent + 3)
        elif nombre == "Imprimir":
            print(f"{prefijo}Imprimir{tipo_str}")
            if isinstance(nodo.valor, str):
                print(f"{prefijo}  {nodo.valor}")
            else:
                mostrar_ast(nodo.valor, indent + 1)
        elif nombre == "Invocacion":
            print(f"{prefijo}Invocacion({nodo.nombre}){tipo_str}")
            mostrar_ast(nodo.argumento, indent + 1)
        else:
            print(f"{prefijo}{nombre}({nodo})")

    # Construimos el AST
    
    ast = parser.parse(lexer.tokenize(codigo))

    # realizamos el chequeo semantico
    try:
        tabla_simbolos = check_program(ast)
        print("Análisis semántico exitoso.")
        print("Variables en tabla de símbolos:", {k: v.tipo for k, v in tabla_simbolos.items()})
        print("=" * 50)
    except SemanticError as e:
        print("ERRORES SEMÁNTICOS ENCONTRADOS:")
        print(e)
        sys.exit(1)  # Cortamos la ejecucion para que no genere codigo si hay errores semanticos

    # Mostramos el AST 
    print("AST Resultante:")
    print("=" * 50)
    for inst in ast:
        mostrar_ast(inst)
        print()

    # Generacion de codigo IR
    
    module = generador.generar_programa(ast)
    print("LLVM IR Generado:")
    print("=" * 50)
    print(module)