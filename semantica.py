#-------------------------------------------------------------------------
# semantica.py
# Analisador léxico para a linguagem t++
# Autor: Leonardo Pontes Baiser
#-------------------------------------------------------------------------

from parser import Parser
from ply import yacc
import pprint


class Semantica():

    def __init__(self, code):
        self.parser = Parser(code)
        self.table = {}
        self.scope = "global"
        self.tree = self.parser.ast  
        self.top(self.tree)
        self.verifica_variaveis_nao_utilizadas(self.table)
        self.verifica_funcao_principal(self.table)
        self.verifica_funcoes_nao_utilizadas(self.table)
        # print(self.parser.lex.t_error(self.parser.lex.test(code))

    def top(self, node):

        if len(node.child) == 1:
            self.procedimento(node.child[0])
        else:
            self.top(node.child[0])
            self.procedimento(node.child[1])

    def procedimento(self, node):
        if (node.child[0].type == "declaracao"):
            self.declaracao(node.child[0])
        if (node.child[0].type == "funcao"):
            self.scope = node.child[0].child[0].value 
            self.funcao(node.child[0])
            self.scope = "global"

    def declaracao(self, node):
        tipo = node.child[0].type
        if self.scope+"@"+node.value in self.table.keys():
            print("Warning. Variavel '"+node.value + "' já declarada")
            exit(1)

        if node.value in self.table.keys():
            print("Erro Semântico. '"+node.value + "' é um procedimento," +
                  " não pode criar variaveis com o mesmo nodeme do procedimento")
            exit(1)
                                                #classe, nome variavel, utilizada, atribuida, tipo
        self.table[self.scope+"@"+node.value] = ["variavel", node.value, False, False, tipo, 0]

    def funcao(self, node):
        self.prototipo(node.child[0])
        self.corpo(node.child[1])

    def prototipo(self, node):
        tipo = node.child[0].type
        nome_func = node.value
        if nome_func in self.table.keys():
            print("Erro Semântico. Procedimento '"+nome_func + "' já declarado")
            exit(1)
                                #classe, nome_func, argumentos, utilizada, tipo
        argumentos = self.declaracao_args(node.child[1])
        self.table[nome_func] = ['funcao', nome_func, argumentos, False, tipo, 0]

    def declaracao_args(self, node):
        if node == None:
            return []
        else:
            tipo_args = []
            nome = self.scope+"@"+node.child[0].value
            tipo = node.child[0].child[0].type
                               #classe, nome, utilizada, tipo, escopo
            self.table[nome] = ["parametro", node.child[0].value, False, self.scope, tipo, 0]
            tipo_args.append(tipo)
            if len(node.child) == 2:
                tipo_args = tipo_args + self.declaracao_args(node.child[1])
            return tipo_args


    def corpo(self, node):
        if node == None:
            return
        elif len(node.child) == 1:
            self.composicao(node.child[0])
        elif len(node.child) == 2:
            self.composicao(node.child[0])
            self.corpo(node.child[1])

    def composicao(self, node):
        comp = node.child[0].type
        if (comp == "atribuicao"):
            self.atribuicao(node.child[0])
        elif (comp == "declaracao"):
            self.declaracao(node.child[0])
        elif (comp == "chamada"):
            self.chamada(node.child[0])
        elif (comp == "condicional"):
            self.condicional(node.child[0])
        elif (comp == "repeticao"):
            self.repeticao(node.child[0])
        elif (comp == "retorna"):
            self.retorna(node.child[0])
        elif (comp == "leia"):
            self.leia(node.child[0])
        elif (comp == "escreva"):
            self.escreva(node.child[0])
       
    def atribuicao(self, node):
        nome = self.scope+"@"+node.value
        if nome not in self.table.keys():
            nome = "global@"+node.value
            if nome not in self.table.keys():
                print ("Erro Semântico. Variavel '" + node.value + "' não declarada ")
                exit(1)
        tipo = self.table[nome][4]
        tipo_exp = self.expressao(node.child[0])
        self.table[nome][2] = True
        self.table[nome][3] = True
        if (tipo != tipo_exp):
            print ("Warning Semântico. Coerção implícita de tipos (inteiro<->flutuante) -  atribuicao")

    def condicional(self, node):
        self.expressao_binaria(node.child[0])
        self.corpo(node.child[1])
        if len(node.child) == 3:
            self.corpo(node.child[2])

    def repeticao(self, node):
        self.corpo(node.child[0])
        self.expressao_binaria(node.child[1])

    def retorna(self, node):
        tipo_expressao = self.expressao(node.child[0])
        tipo_esperado = self.table[self.scope][4]
        if tipo_esperado != tipo_expressao:
            print("Warning Semântico. Coerção implícita de tipos. É esperado: "+tipo_esperado+". Tipo recebido: "+tipo_expressao)

    def leia(self, node):
        self.expressao(node.child[0])

    def escreva(self, node):
        self.expressao(node.child[0])

    def expressao(self, node):
        exp = node.child[0].type  
        if (exp == "expressao_calculo"):
           return self.expressao_calculo(node.child[0])
        elif (exp == "chamada"):
            return self.chamada(node.child[0])
        elif (exp == "expressao_unaria"):
            return self.expressao_unaria(node.child[0])
        elif (exp == "expressao_numerica"):
            # print (node.child[0].child[0].value)
            return self.expressao_numerica(node.child[0])
        elif (exp == "expressao_identificador"):
            return self.expressao_identificador(node.child[0])
        elif (exp == "expressao_parenteses"):
            return self.expressao_parenteses(node.child[0])

    def expressao_calculo(self, node):
        tipo1 = self.expressao(node.child[0])
        tipo2 = self.expressao(node.child[1])
        if (tipo1 != tipo2):
            print ("Warning Semântico. Comparação entre '"+tipo1+"' e '" + tipo2+"'")
        if (tipo1 == "flutuante" or tipo2 == "flutuante"):
            return "flutuante"
        else:
            return tipo1

    def expressao_binaria(self, node):
        exp = node.child[0].type
        if (exp == "expressao_binaria_com_parenteses"):
            return self.expressao_binaria_com_parenteses(node.child[0])
        elif (exp == "expressao_binaria_sem_parenteses"):
            return self.expressao_binaria_sem_parenteses(node.child[0])
   
    def expressao_binaria_com_parenteses(self, node):
        self.expressao_binaria(node.child[0])

    def expressao_binaria_sem_parenteses(self, node):
        tipo1 = self.expressao(node.child[0])
        tipo2 = self.expressao(node.child[1])
        if (tipo1 != tipo2):
            print ("Warning Semântico. Comparação entre '"+tipo1+"' e '" + tipo2+"'")
        if (tipo1 == "flutuante" or tipo2 == "flutuante"):
            return "flutuante"
        else:
            return tipo1

    def expressao_numerica(self, node):
        if (node.child[0].type == "num_inteiro"):
            return "inteiro"
        elif (node.child[0].type == "num_flutuante"):
            return "flutuante"

    def expressao_unaria(self, node):
        return self.expressao(node.child[0])

    def expressao_identificador(self, node):
        nome = self.scope+"@"+node.value
        if nome not in self.table.keys():
            nome = "global@"+node.value
            if nome not in self.table.keys():
                print ("Erro Semântico. Variavel '" + node.value + "' não declarada")
                exit(1)
        if self.table[nome][3] == False:
            print ("Erro Semântico. Variavel '" + node.value + "' não inicializada")
            exit(1)
        self.table[nome][2] = True
        return self.table[nome][4]


    def expressao_parenteses(self, node):
        self.expressao(node.child[0])

    def chamada(self, node):
        if node.value not in self.table.keys():
            print ("Erro Semântico. Função '" + node.value + "' não declarada")
            exit(1)
        argumentos = self.expressao_args(node.child[0])
        parametros_esperados = self.table[node.value][2]

        if len(argumentos) != len(parametros_esperados):
            print ("Erro Semântico. Numero de parametros passados '" + str(len(argumentos)) +
             "', numero de parametros esperado '" + str(len(parametros_esperados)))
            exit(1)

        for i in range(len(parametros_esperados)):
            if (argumentos[i] != parametros_esperados[i]):
                print ("Erro Semântico, Argumentos esperados pela função '" + node.value+"': '" + str(parametros_esperados)+"' - Recebido: " + str(argumentos))
                exit(1)
        self.table[node.value][3] = True
        return self.table[node.value][4]

    def expressao_args(self, node):
        if node == None:
            return []
        else:
            tipo_args = []
            tipo_arg = self.expressao(node.child[0])
            tipo_args.append(tipo_arg)
            if len(node.child) == 2:
                tipo_args = tipo_args + self.expressao_args(node.child[1])
            return tipo_args

    def variavel_is_declarada(self, variavel):
        if self.scope+"@"+variavel not in self.table.keys():
            if 'global'+"@"+variavel not in self.table.keys():
                return False
        return True

    def set_decl_variavel(self, variavel):
        if self.scope+"@"+variavel in self.table.keys():
            self.table[self.scope+"@"+variavel][2] = True
        if "global"+"@"+variavel in self.table.keys(): 
            self.table["global"+"@"+variavel][2] = True


    def verifica_variaveis_nao_utilizadas(self, table):
        for (k,v) in table.items():
            if (v[0] == "variavel"):
                if (v[2] == False):
                    scope = k.split("@")
                    if (scope[0] != "global"):
                        print("Warning. Variavel '"+v[1] + "' da função '" + scope[0] +"' nunca é utilizada")
                    else:
                        print("Warning. Variavel '"+v[1] + "' nunca é utilizada")

    def verifica_funcoes_nao_utilizadas(self, table):
        for (k,v) in table.items():
            if (v[0] == "funcao" and k != "principal"):
                if (v[3] == False):
                    print("Warning. Função '"+k+ "' nunca é utilizada'")

        

    def verifica_funcao_principal(self, table):
        if ("principal" not in table.keys()):
            print ("Warning. Função \"principal()\" não declarada")

def print_tree(node, level="-"):
    if node != None:
        print("%s %s %s" %(level, node.type, node.value))
        for son in node.child:
            print_tree(son, level+"-")

def print_funcoes(table):
    for (k,v) in table.items():
        if (v[0] == "funcao"):
            print(v)

if __name__ == '__main__':
    import sys
    code = open(sys.argv[1])
    s = Semantica(code.read())

    print_tree(s.tree)
    # print (s.parser.tokens)

    # print("Tabela de Simbolos:", s.table)
    # print_funcoes(s.table)
    pprint.pprint(s.table, depth=3, width=500)
