import time
import os
from lexer import MiLexer
import ast_nodes as ast
from parser import MiParser
from checker import Checker, SemanticError
from llvmgen import LLVMGen


def main():
    print("--- COMPILADOR JIT ---")
    print("Iniciando modo escucha de 'codigo.txt'...")

    lexer = MiLexer()
    parser = MiParser()
    checker = Checker()
    llvm_gen = LLVMGen()

    archivo = "codigo.txt"

    if not os.path.exists(archivo):
        with open(archivo, 'w') as f:
            pass

    print(f"Escribe en '{archivo}' y guarda para ejecutar. (Ctrl+C para salir)")

    # Para llevar la cuenta de qué ya procesamos
    ultima_posicion = 0

    while True:
        try:
            with open(archivo, 'r') as f:
                # Nos movemos a lo último que leímos
                f.seek(ultima_posicion)
                lineas = f.readlines()
                ultima_posicion = f.tell()

            if not lineas:
                time.sleep(0.7)
                continue

            # Unimos las líneas nuevas por si escribiste un bloque completo
            codigo_nuevo = "".join(lineas).strip()
            if not codigo_nuevo:
                continue

            # META-COMANDOS
            if codigo_nuevo.lower() in ['salir', 'exit', 'terminar']:
                archivo_salida = "salida_compilada.ll"
                with open(archivo_salida, 'w') as f_out:
                    f_out.write(str(llvm_gen.module))
                print(f"\n[SISTEMA] Código LLVM final guardado en '{archivo_salida}'.")
                break

            print(f"\n[PROCESANDO] ->\n{codigo_nuevo}")

            try:
                # 1. Lexer
                tokens = lexer.tokenize(codigo_nuevo)

                # 2. Parser
                ast_nodo = parser.parse(tokens)

                if ast_nodo is None:
                    print("[PARSER] Esperando más código para completar la estructura...")
                    continue

                print(f"[PARSER] -> Nodo detectado: {type(ast_nodo).__name__}")

                # 3. Checker (Análisis Semántico)
                checker.visit(ast_nodo)

                # 4. LLVM JIT
                resultado = llvm_gen.generate_and_execute(ast_nodo)

                # 5. Output
                print("\n--- CÓDIGO LLVM IR GENERADO ---")
                # Mostramos solo las últimas líneas del módulo para no llenar la pantalla
                ir_completo = str(llvm_gen.module).strip()
                print("\n".join(ir_completo.splitlines()[-15:]))
                print("-------------------------------\n")

                if isinstance(ast_nodo, ast.Declaracion):
                    print(f"[EJECUCIÓN] -> Variables {ast_nodo.nombres} creadas.")
                else:
                    print(f"[EJECUCIÓN] -> Resultado: {resultado}")

            except SyntaxError as e:
                print(f"[ERROR SINTAXIS] {e}")
            except SemanticError as e:
                print(f"[ERROR SEMÁNTICO] {e}")
            except Exception as e:
                print(f"[ERROR] {e}")
                # Si hay error, reseteamos la posición para intentar leer de nuevo si el usuario corrige
                # ultima_posicion -= len(codigo_nuevo)

        except KeyboardInterrupt:
            print("\nApagando...")
            break


if __name__ == '__main__':
    main()