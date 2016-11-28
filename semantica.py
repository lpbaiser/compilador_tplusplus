#-------------------------------------------------------------------------
# semantica.py
# Analisador léxico para a linguagem t++
# Autor: Leonardo Pontes Baiser
#-------------------------------------------------------------------------

from parser import Parser


class Semantica():

    def __init__(self, code):
        self.table = {}
        self.scope = "global"
        self.tree = Parser(code).ast  
        self.top(self.tree)

    def top(self, node):
        if len(node.child) == 1:
            self.procedimento(node.child[0])
        else:
            self.top(node.child[0])
            self.procedimento(node.child[1])

    def procedimento(self, node):
        # print (node.child[0].type)
        if (node.child[0].type == "declaracao"):
            self.declaracao(node.child[0])
        if (node.child[0].type == "funcao"):
            self.scope = node.child[0].child[0].value 
            self.funcao(node.child[0])
            self.scope = "global"

    def declaracao(self, node):
        # print (node.value)
        tipo = str(node.child[0])
        # print (self.scope)
        if self.scope+"@"+node.value in self.table.keys():
            print("Warning. Variavel '"+node.value + "' já declarada")
            

        if node.value in self.table.keys():
            print("Erro Semantico. '"+node.value + "' é um procedimento," +
                  " não pode criar variaveis com o mesmo nodeme do procedimento")
            exit(1)
        # print (node.type)
        # self.scope = node.value
        self.table[self.scope+"@"+node.value] = [str(node.value), "variavel", 0, 0, tipo]#nome variavel, classe, delc(T/F), 0, tipo
        # self.scope = "global"
        
        # print (self.table[self.scope+"@"+node.value][2])

    def funcao(self, node):
        self.prototipo(node.child[0])
        self.corpo(node.child[1])

    def prototipo(self, node):

        tipo = node.child[0]
        nome_func = node.value
        # self.scope = nome_func
        if nome_func in self.table.keys():
            print("Erro Semantico. Procedimento '"+nome_func + "' já declarado")
            exit(1)
        argumentos = self.get_tipos_argumentos(node.child[1])
        self.table[nome_func] = ['funcao', argumentos]
        self.declaracao_args(node.child[1])
        # self.scope = "global"

    def declaracao_args(self, node):
        if node == None:
            return
        self.declaracao(node.child[0])
        if len(node.child) > 1:
            self.declaracao_args(node.child[1])

    def get_tipos_argumentos(self, node):
        if node == None:
            return []
        tipos = []
        qtde_paramentros = len(node.child)
        if (len(node.child) > 0):
            tipo = str(node.child[0].child[0])
            tipos.append(tipo)
            nome_variavel = str(node.child[0].value)
            if (len(node.child) > 1):
                tipos = tipos+self.get_tipos_argumentos(node.child[1])
        return tipos

    def corpo(self, node):
        if node == None:
            return
        self.composicao(node.child[0])
        if len(node.child) > 1:
            self.corpo(node.child[1])

    def composicao(self, node):
        comp = node.child[0].type
        # print (comp)
        if (comp == "atribuicao"):
            self.atribuicao(node.child[0])
        if (comp == "declaracao"):
            self.declaracao(node.child[0])
        if (comp == "chamada"):
            self.chamada(node.child[0])
        if (comp == "condicional"):
            self.condicional(node.child[0])
        if (comp == "repeticao"):
            self.repeticao(node.child[0])
        if (comp == "retorna"):
            self.retorna(node.child[0])
        if (comp == "leia"):
            self.leia(node.child[0])
        if (comp == "escreva"):
            self.escreva(node.child[0])
       
    def atribuicao(self, node):
        self.expressao(node.child[0])
        self.set_decl_variavel(node.value)
        if self.variavel_is_declarada(node.child[0].child[0].value):
            self.set_decl_variavel(node.child[0].child[0].value)
            tipo_var1 = self.table[self.scope+"@"+node.value][4]
            if (self.scope+"@"+node.child[0].child[0].value in self.table.keys()):
                tipo_var2 = self.table[self.scope+"@"+node.child[0].child[0].value][4]
            elif ("global"+"@"+node.child[0].child[0].value in self.table.keys()):
                tipo_var2 = self.table["global"+"@"+node.child[0].child[0].value][4]
            if (tipo_var1 == "inteiro" and tipo_var2 == "flutuante"):
                print ("Warning Semantico. Coerção implícita de tipos (inteiro<->flutuante)")

    def condicional(self, node):
        # print(node.child[1])
        self.expressao(node.child[0])
        self.corpo(node.child[1])
        if len(node.child) == 3:
            # print(node.child[2])
            self.corpo(node.child[2])

    def repeticao(self, node):
        self.corpo(node.child[0])
        self.expressao(node.child[1])

    def retorna(self, node):
        self.expressao(node.child[0])

    def leia(self, node):
        self.expressao(node.child[0])

    def escreva(self, node):
        self.expressao(node.child[0])

    def expressao(self, node):
        # print(node.child[0].type)
        exp = node.child[0].type  
        if (exp == "expressao"):
            self.expressao(node.child[1])
        if (exp == "expressao_binaria"):
            self.expressao_binaria(node.child[0])
        if (exp == "chamada"):
            self.chamada(node.child[0])
        if (exp == "expressao_unaria"):
            self.expressao_unaria(node.child[0])
        if (node.child[0] == "expressao_numerica"):
            pass
        if (exp == "expressao_identificador"):
            self.expressao_identificador(node.child[0])
        if (exp == "expressao_parenteses"):
            self.expressao_parenteses(node.child[0])

    def expressao_binaria(self, node):
        self.expressao(node.child[0])
        self.expressao(node.child[1])

    def expressao_unaria(self, node):
        self.expressao(node.child[0])

    def expressao_identificador(self, node):
        if self.variavel_is_declarada(node.value) == False:
            print ("Erro Semantico. Variavel '" + node.value + "' não declarada ")
            # exit(1)

    def expressao_parenteses(self, node):
        self.expressao(node.child[0])

    def chamada(self, node):
        if node.value not in self.table.keys():
            print ("Erro Semantico. Função '" + node.value + "' não declarada")
            exit(1)
        self.expressao_args(node.child[0])
        qtde_parametros = self.lista_qtde_parametros(node.child[0])
        if len(self.table[node.value][1]) != qtde_parametros:
            print ("Erro Semantico. Numero de parametros passados '" + str(qtde_parametros) +
             "', numero de parametros esperado '" + str(len(self.table[node.value][1])))
            exit(1)

        self.set_uso_variavel_chamada(node.child[0])

    def set_uso_variavel_chamada(self, node):
        if len(node.child) > 1:
            self.set_decl_variavel(node.child[0].child[0].value)
            self.set_uso_variavel_chamada(node.child[1])
        elif len(node.child) == 1:
            self.set_decl_variavel(node.child[0].child[0].value)


    def expressao_args(self, node):
        if node == None:
            return []
        self.expressao(node.child[0])
        if len(node.child) > 1:
            self.expressao_args(node.child[1])

    def lista_qtde_parametros(self, node):
        if len(node.child) > 1:
            return self.lista_qtde_parametros(node.child[1])+1
        elif len(node.child) == 1:
            return 1
        else:
            return 0

    def variavel_is_declarada(self, variavel):
        if self.scope+"@"+variavel in self.table.keys():
            return True
        elif 'global'+"@"+variavel in self.table.keys():
            return True
        return False

    def set_decl_variavel(self, variavel):
        if self.scope+"@"+variavel in self.table.keys():
            self.table[self.scope+"@"+variavel][2] = 1
        if "global"+"@"+variavel in self.table.keys(): 
            self.table["global"+"@"+variavel][2] = 1


def verifica_variaveis_nao_utilizadas(table):
    for (k,v) in table.items():
        if (v[1] == "variavel"):
            if (v[2] == 0):
                scope = k.split("@")
                if (scope[0] != "global"):
                    print("Warning. Variavel '"+v[0] + "' da função '" + scope[0] +"' nunca é utilizada")
                else:
                    print("Warning. Variavel '"+v[0] + "' nunca é utilizada")

def verifica_funcao_principal(table):
    if ("principal" not in table.keys()):
        print ("Warning. Função \"principal()\" não declarada")

def print_tree(node, level="-"):
    if node != None:
        print("%s %s %s" %(level, node.type, node.value))
        for son in node.child:
            print_tree(son, level+"-")

if __name__ == '__main__':
    import sys
    code = open(sys.argv[1])
    s = Semantica(code.read())

    # print_tree(s.tree)
    verifica_variaveis_nao_utilizadas(s.table)
    verifica_funcao_principal(s.table)
    print("Tabela de Simbolos:", s.table)
