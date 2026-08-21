from CheLexer import CheLexer

def probar_lexer():
    lexer = CheLexer()

    with open("Lexer_Testing/Prueba1", "r", encoding="utf-8") as f:
        codigo = f.read()


    print("--- TOKENS ---")
    tokens = lexer.tokenize(codigo)
    for tok in tokens:
        print(tok)

if __name__ == "__main__":
    probar_lexer()