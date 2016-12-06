#-------------------------------------------------------------------------
# lexer.py
# Analisador sintático e geração def uma árvore sintática abstrata para a
#   linguagem t++
# Autores: Leonardo Pontes Baiser
#-------------------------------------------------------------------------

from ply import yacc
from lexer import Lexer

class Tree:

    def __init__(self, type_node, child=[], value=" ", line=""):
        self.type = type_node
        self.child = child
        self.value = value
        self.line = line

    def __str__(self, level=0):
        # ret = "|"*level+repr(self.type)+"\n"
        # for c in self.child:
        #     ret += c.__str__(level+1) 
        return self.type

class Parser:

    def __init__(self, code):
        self.lex = Lexer()
        self.tokens = self.lex.tokens
        self.precedence = (
            ('left', 'EQ', 'MAIOR_EQ', 'MAIOR', 'MENOR_EQ', 'MENOR'),
            ('left', 'ADD', 'SUB'),
            ('left', 'MUL', 'DIV'),
        )
        parser = yacc.yacc(debug=False, module=self, optimize=False)
        self.ast = parser.parse(code)
        # print (lex.keywords)
        # self.lexer = lex.t_error(lex)

    def p_top_1(self, p):
        '''
        top : procedimento
        '''
        p[0] = Tree('top', [p[1]])

    def p_top_2(self, p):
        '''
        top : top procedimento
        '''
        p[0] = Tree('top', [p[1], p[2]])

    def p_procedimento(self, p):
        '''
        procedimento : declaracao
                     | funcao
        '''
        p[0] = Tree('procedimento', [p[1]])

    def p_tipo_1(self, p):
        'tipo : INTEIRO'
        p[0] = Tree('inteiro')

    def p_tipo_2(self, p):
        'tipo : FLUTUANTE'
        p[0] = Tree('flutuante')

    def p_funcao(self, p):
        '''
        funcao : prototipo corpo FIM
        '''
        p[0] = Tree('funcao', [p[1], p[2]])

    def p_prototipo(self, p):
        'prototipo : tipo ID LPAR declaracao_args RPAR'
        p[0] = Tree('prototipo', [p[1], p[4]], p[2])

    def p_declaracao(self, p):
        '''
        declaracao : tipo COLON ID
        '''
        p[0] = Tree('declaracao', [p[1]], p[3])


    def p_declaracao_args_1(self, p):
        '''
        declaracao_args : 
        '''

    def p_declaracao_args_2(self, p):
        'declaracao_args : declaracao'
        p[0] = Tree('declaracao_args', [p[1]])

    def p_declaracao_args_3(self, p):
        'declaracao_args : declaracao COMMA declaracao_args'
        p[0] = Tree('declaracao_args', [p[1], p[3]])

    def p_expressao_args_1(self, p):
        '''
        expressao_args : 
        '''

    def p_expressao_args_2(self, p):
        'expressao_args : expressao'
        p[0] = Tree('expressao_args', [p[1]])

    def p_expressao_args_3(self, p):
        'expressao_args : expressao COMMA expressao_args'
        p[0] = Tree('expressao_args', [p[1], p[3]])

    def p_expressao(self, p):
        '''
        expressao : expressao_calculo
                  | expressao_unaria
                  | expressao_numerica
                  | expressao_identificador
                  | expressao_parenteses
                  | chamada
        '''
        p[0] = Tree('expressao', [p[1]])


    def p_expressao_binaria(self, p):
        '''
        expressao_binaria : expressao_binaria_com_parenteses
                          | expressao_binaria_sem_parenteses
        '''
        p[0] = Tree('expressao_binaria', [p[1]])

    def p_expressao_binaria_sem_parenteses(self, p):
        '''
        expressao_binaria_sem_parenteses : expressao EQ expressao
                                         | expressao MAIOR_EQ expressao
                                         | expressao MAIOR expressao
                                         | expressao MENOR_EQ expressao
                                         | expressao MENOR expressao
        '''
        p[0] = Tree('expressao_binaria_sem_parenteses', [p[1], p[3]], p[2])

    def p_expressao_binaria_com_parenteses(self, p):
        '''
        expressao_binaria_com_parenteses : LPAR expressao_binaria RPAR
        '''
        p[0] = Tree('expressao_binaria_com_parenteses', [p[2]])

    def p_expressao_calculo(self, p):
        '''
        expressao_calculo : expressao ADD expressao
                          | expressao SUB expressao
                          | expressao MUL expressao
                          | expressao DIV expressao
        '''
        p[0] = Tree('expressao_calculo', [p[1], p[3]], p[2])

    def p_expressao_unaria(self, p):
        '''
        expressao_unaria : SUB expressao
                         | ADD expressao
        '''
        p[0] = Tree('expressao_unaria', [p[2]], value=p[1])

    def p_expressao_numerica(self, p):
        '''
        expressao_numerica : inteiro
                           | flutuante
        '''
        p[0] = Tree('expressao_numerica', [p[1]])

    def p_inteiro(self,p):
        'inteiro : NUM_INTEIRO'
        p[0] = Tree('num_inteiro', value=p[1])

    def p_flutuante(self, p):
        'flutuante : NUM_FLUTUANTE'
        p[0] = Tree('num_flutuante',value=p[1])

    def p_expressao_identificador(self, p):
        '''
        expressao_identificador : ID
        '''
        p[0] = Tree('expressao_identificador', [], p[1])

    def p_expressao_parenteses(self, p):
        '''
        expressao_parenteses : LPAR expressao RPAR
        '''
        p[0] = Tree('expressao_parenteses', [p[2]])

    def p_atribuicao(self, p):
        '''
        atribuicao : ID ATR expressao
        '''
        p[0] = Tree('atribuicao', [p[3]], p[1])        

    def p_chamada(self, p):
        '''
        chamada : ID LPAR expressao_args RPAR
        '''
        p[0] = Tree('chamada', [p[3]], p[1])

    def p_condicional_1(self, p):
        '''
        condicional : SE expressao_binaria ENTAO corpo FIM
        '''
        p[0] = Tree('condicional', [p[2], p[4]])

    def p_condicional_2(self, p):
        '''
        condicional : SE expressao_binaria ENTAO corpo SENAO corpo FIM
        '''
        p[0] = Tree('condicional', [p[2], p[4], p[6]])

    def p_repeticao(self, p):
        'repeticao : REPITA corpo ATE expressao_binaria' 
        p[0] = Tree('repeticao', [p[2], p[4]])

    
    def p_retorna(self, p):
        'retorna : RETORNA LPAR expressao RPAR' 
        p[0] = Tree('retorna', [p[3]])

    def p_corpo_1(self, p):
        'corpo : '

    def p_corpo_2(self, p):
        '''
        corpo : composicao corpo
        '''
        p[0] = Tree('corpo', [p[1], p[2]]) 

    def p_composicao(self, p):
        '''
        composicao : atribuicao
                   | declaracao
                   | chamada
                   | condicional
                   | repeticao
                   | retorna
                   | leia
                   | escreva
        '''
        p[0] = Tree('composicao', [p[1]])

    def p_leia(self, p):
        '''
        leia : LEIA LPAR expressao RPAR
        '''
        p[0] = Tree('leia', [p[3]])

    def p_escreva(self, p):
        '''
        escreva : ESCREVA LPAR expressao RPAR
        '''
        p[0] = Tree('escreva', [p[3]])


    def p_error(self, p):
        if p:
            print("Erro sintático: '%s', linha %d" % (p.value, p.lineno))
            exit(1)
        else:
            yacc.restart()
            print('Erro sintático: definições incompletas!')
            exit(1)

def print_tree(node, level="-"):
    if node != None:
        print("%s %s %s %s" %(level, node.type, node.value, node.line))
        for son in node.child:
            print_tree(son, level+"-")

if __name__ == '__main__':
    from sys import argv, exit
    f = open(argv[1])
    t = Parser(f.read())
    print_tree(t.ast)

