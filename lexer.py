#-------------------------------------------------------------------------
# lexer.py
# Analisador léxico para a linguagem t++
# Autor: Leonardo Pontes Baiser
#-------------------------------------------------------------------------

import ply.lex as lex
import sys

class Lexer:

    def __init__(self):
        self.lexer = lex.lex(debug=False, module=self, optimize=False)

    keywords = {
        u'se': 'SE',
        u'então': 'ENTAO',
        u'senão': 'SENAO',
        u'fim': 'FIM',
        u'repita': 'REPITA',
        u'flutuante': 'FLUTUANTE',
        u'retorna': 'RETORNA',
        u'até': 'ATE',
        u'leia': 'LEIA',
        u'escreva': 'ESCREVA',
        u'inteiro': 'INTEIRO',
    }

    tokens = ['ADD', 'SUB', 'MUL', 'DIV', 'EQ', 'COMMA', 'ATR', 'MENOR', 'MAIOR',
                'MENOR_EQ', 'MAIOR_EQ', 'LPAR', 'RPAR', 'COLON', 'ID', 'NUM_INTEIRO', 'NUM_FLUTUANTE'] + list(keywords.values())

    t_ADD = r'\+'
    t_SUB = r'\-'
    t_MUL = r'\*'
    t_DIV = r'/'
    t_EQ = r'='
    t_COMMA = r','
    t_ATR = r':='
    t_MENOR = r'<'
    t_MAIOR = r'>'
    t_MENOR_EQ = r'<='
    t_MAIOR_EQ = r'>='
    t_LPAR = r'\('
    t_RPAR = r'\)'
    t_COLON = r':'
    t_NUM_INTEIRO = r'(\d+)'
    t_NUM_FLUTUANTE = r'(\d+(\.\d+)|\d+(\.\d+)?e(\+|\-)?\d+(\.\d+)?)'

    def t_ID(self, t):
        r'[a-zA-Zá-ñÁ-Ñà-źÀ-Ź][a-zA-Zá-ñÁ-Ñà-źÀ-Ź0-9]*'
        t.type = self.keywords.get(t.value, 'ID')
        return t

    def t_COMMENT(self, t):
        r'\{(.|\s)*?\}'

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    t_ignore = ' \t'

    def t_error(self, t):
        print("Item ilegal: '%s', linha %d, coluna %d" % (t.value[0],t.lineno, t.lexpos))
        t.lexer.skip(1)


    def test(self, code):
        lex.input(code)
        while True:
            tk = lex.token()
            if not tk:
                break
            print(tk)


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        lexer = Lexer() 
        f = open(sys.argv[1])
        lexer.test(f.read())            
    else:
        # print ('Erro')
        sys.stderr.write('Usage: python3 lexer.py example.tpp \n')
        sys.exit(1)