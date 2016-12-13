#-------------------------------------------------------------------------
# gen.py
# Analisador léxico para a linguagem t++
# Autor: Leonardo Pontes Baiser
#-------------------------------------------------------------------------
import pprint

from llvmlite import ir, binding
from semantica import Semantica
from ctypes import CFUNCTYPE, c_int32
import os

class Gen:
    
    #def __init__(self, code, module, symbols, ee, passes, optz, debug):
    def __init__(self, code, module, optz=False, debug=True):
        semantica = Semantica(code)
        self.module = module
        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()
        self.ee = self.execution_engine()

        # self.passes = passes
        self.optimization = optz
        self.builder = None
        self.funcao = None
        self.leia = None
        self.escreva = None
        self.debug = debug
        self.scope = "global"
        self.table = semantica.table
        self.tree = semantica.tree
        self.gen_top(self.tree)

    def gen_top(self, node):
        if node == None:
            return 
        elif len(node.child) == 1:
            self.gen_procedimento(node.child[0])
        else:
            self.gen_top(node.child[0])
            self.gen_procedimento(node.child[1])

    def gen_procedimento(self, node):
        if (node.child[0].type == "declaracao"):
            self.gen_declaracao(node.child[0])
        if (node.child[0].type == "funcao"):
            self.scope = node.child[0].child[0].value 
            self.gen_funcao(node.child[0])
            self.scope = "global"

    def gen_declaracao(self, node):
        nome = self.scope+"@"+node.value
        tipo = self.gen_tipo(node.child[0].type)
        if self.scope == "global":
            ref_var = ir.GlobalVariable(self.module, tipo, name = node.value)
        else:
            ref_var = self.builder.alloca(tipo, name=node.value)
        self.table[nome][5] = ref_var

    def gen_funcao(self, node):
        self.gen_prototipo(node.child[0])
        self.gen_corpo(node.child[1])

    def gen_prototipo(self, node):
        tipo_retorno = self.gen_tipo(node.child[0].type)
        argumentos = self.table[node.value][2]
        self.scope = node.value

        tipo_argumentos = ()
        for arg in argumentos:
            tipo_argumentos = tipo_argumentos + (self.gen_tipo(arg),)

        tipo_funcao = ir.FunctionType(tipo_retorno,tipo_argumentos)
        self.funcao = ir.Function(self.module,tipo_funcao,node.value)
        self.table[node.value][4] = self.funcao
        bloco = self.funcao.append_basic_block('BLOCO')
        self.builder = ir.IRBuilder(bloco)


    def gen_corpo(self, node):
        if node == None:
            return
        elif len(node.child) == 1:
            self.gen_composicao(node.child[0])
        elif len(node.child) == 2:
            self.gen_composicao(node.child[0])
            self.gen_corpo(node.child[1])

    def gen_composicao(self, node):
        comp = node.child[0].type
        if (comp == "atribuicao"): #ok
            self.gen_atribuicao(node.child[0])
        elif (comp == "declaracao"): #ok
            self.gen_declaracao(node.child[0])
        elif (comp == "chamada"): #ok
            self.gen_chamada(node.child[0])
        elif (comp == "condicional"): #ok
            self.gen_condicional(node.child[0])
        elif (comp == "repeticao"): #ok
            self.gen_repeticao(node.child[0])
        elif (comp == "retorna"): #ok
            self.gen_retorna(node.child[0])
        elif (comp == "leia"):
            self.gen_leia(node.child[0])
        elif (comp == "escreva"):
            self.gen_escreva(node.child[0])

    def gen_atribuicao(self, node):
        nome = self.scope+"@"+node.value
        if nome not in self.table.keys() or self.table[self.scope+"@"+node.value][5] == 0:
            nome = "global@"+node.value
        ref_var = self.table[nome][5]
        tipo = self.gen_tipo(self.table[nome][4])
        tipo_exp = self.gen_expressao(node.child[0], tipo)
        self.builder.store(tipo_exp, ref_var)

        

    def gen_chamada(self, node):
        funcao = self.builder.load(self.table[node.value][4])
        nome= node.value
        argumentos = self.gen_expressao_args(node.child[0], nome)
        return self.builder.call(funcao,argumentos,name="CHAMADA")

    def gen_expressao_args(self, node, nome):
        if node == None:
            return []
        else:
            argumentos = []
            #arrumar tipo
            arg = self.table[nome][2].pop(0)
            tipo = self.gen_tipo(arg)
            
            argumento = self.gen_expressao(node.child[0], tipo)
            argumentos.append(argumento)
            if len(node.child) == 2:
                argumentos = argumentos + self.gen_expressao_args(node.child[1], nome)
            return argumentos

    def gen_condicional(self, node):
        tipo = self.gen_tipo("flutuante")
        cond = self.gen_expressao_binaria(node.child[0], tipo)
        entao_se = self.funcao.append_basic_block('ENTAO_SE')
        if (len(node.child)== 3): 
            else_se = self.funcao.append_basic_block('ELSE_SE')
        fim_se = self.funcao.append_basic_block('FIM_SE')
        if (len(node.child)==3):
            self.builder.cbranch(cond, entao_se, else_se)
        else:
            self.builder.cbranch(cond, entao_se, fim_se)
        self.builder.position_at_start(entao_se)
        self.gen_corpo(node.child[1])
        self.builder.branch(fim_se)
        if (len(node.child)==3):
            self.builder.position_at_start(else_se)
            self.gen_corpo(node.child[2])
            self.builder.branch(fim_se)
        self.builder.position_at_start(fim_se)

    def gen_repeticao(self, node):
        repeticao_start = self.funcao.append_basic_block('LOOP')
        repeticao_fim = self.funcao.append_basic_block('FIM_LOOP')
        self.builder.branch(repeticao_start)
        self.builder.position_at_start(repeticao_start)
        self.gen_corpo(node.child[0])
        tipo = self.gen_tipo("flutuante")
        condicao_stop = self.gen_expressao_binaria(node.child[1], tipo)
        print(condicao_stop)
        self.builder.cbranch(condicao_stop, repeticao_fim, repeticao_start)
        self.builder.position_at_start(repeticao_fim)

    def gen_retorna(self, node):
        tipo = self.gen_tipo("flutuante")
        ref_funcao = self.gen_expressao(node.child[0], tipo)
        self.builder.ret(ref_funcao)

    def gen_escreva(self, node):
        escreve = ir.FunctionType(ir.VoidType(), [ir.FloatType])
        self.escreva = ir.Function(self.module, escreve, 'ESCREVE')
        tipo = self.gen_tipo("flutuante")
        exp = self.gen_expressao(node.child[0], tipo)
        self.builder.call(self.escreva, [exp])
        self.mod = self.compile_ir()
        funcao_escreva = self.ee.get_function_address("ESCREVE")
        funcao_c = CFUNCTYPE(c_int32)(funcao_escreva)
        valor_retorno = funcao_c()

    def gen_leia(self, node):
        leitura = ir.FunctionType(ir.IntType(32), [])
        self.leia = ir.Function(self.module, leitura, 'LEIA')
        l = self.builder.call(self.leia, [])
        resultado = ir.Constant(ir.DoubleType(), l)
        self.builder.ret(resultado)
        self.mod = self.compile_ir()
        funcao_leia = self.ee.get_function_address("LEIA")
        cfunc = CFUNCTYPE(c_int32)(funcao_leia)
        valor_retorno = cfunc()

    def gen_expressao(self, node, tipo):

        exp = node.child[0].type
        if (exp == "expressao_calculo"):
           return self.gen_expressao_calculo(node.child[0],tipo)
        elif (exp == "expressao_numerica"):
            return self.gen_expressao_numerica(node.child[0], tipo)
        elif (exp == "expressao_parenteses"):
            return self.gen_expressao_parenteses(node.child[0], tipo)
        elif (exp == "expressao_unaria"):
            return self.gen_expressao_unaria(node.child[0], tipo)
        elif (exp == "expressao_identificador"):
            return self.gen_expressao_identificador(node.child[0], tipo)
        elif (exp == "chamada"):
            return self.gen_chamada(node.child[0])

    def gen_expressao_calculo(self, node, tipo):
        tipo1 = self.gen_expressao(node.child[0], tipo)
        tipo2 = self.gen_expressao(node.child[1], tipo)

        if node.value == "+":
            ref = self.builder.fadd(tipo1, tipo2, name='ADD')
        elif node.value == "-":
            ref = self.builder.fsub(tipo1, tipo2, name='SUB')
        elif node.value == "*":
            ref = self.builder.fmul(tipo1, tipo2, name='MUL')
        elif node.value == "/":
            ref = self.builder.fdiv(tipo1, tipo2, name='DIV')
        return ref

    def gen_expressao_numerica(self, node, tipo):
        return ir.Constant(tipo, node.child[0].value)

    def gen_expressao_parenteses(self, node, tipo):
        return self.gen_expressao(node.child[0], tipo)

    def gen_expressao_unaria(self, node, tipo):
        ref_unaria = self.gen_expressao(node.child[0], tipo)
        if node.value == "+":
            return ref_unaria
        elif node.value == "-":
            return self.builder.fmul(ref_unaria, ir.Constant(tipo, -1), name='MUL')

    def gen_expressao_identificador(self, node, tipo):
        nome = self.scope+"@"+node.value
        if nome not in self.table.keys() or self.table[self.scope+"@"+node.value][5] == 0:
            nome = "global@"+node.value
        ref_var = self.table[nome][5]
        
        return self.builder.addrspacecast(ref_var,tipo)

    def gen_expressao_binaria(self, node, tipo):
        exp = node.child[0].type
        if (exp == "expressao_binaria_com_parenteses"):
            return self.gen_expressao_binaria_com_parenteses(node.child[0], tipo)
        elif (exp == "expressao_binaria_sem_parenteses"):
            return self.gen_expressao_binaria_sem_parenteses(node.child[0], tipo)

    def gen_expressao_binaria_sem_parenteses(self, node, tipo):
        tipo1 = self.gen_expressao(node.child[0], tipo)
        tipo2 = self.gen_expressao(node.child[1], tipo)
        simbolo = node.value
        if simbolo == "=":
            exp = self.builder.icmp_signed("==", tipo1, tipo2, 'cmptmp')
        else:
            exp = self.builder.icmp_signed(node.value, tipo1, tipo2, 'cmptmp')
        return exp


    def gen_expressao_binaria_com_parenteses(self, node, tipo):
        print (node.child[0].child[0])
        self.gen_expressao_binaria(node.child[0], tipo)

    def gen_tipo(self, node):
        if (node == "inteiro" or node == "num_inteiro"):
            return ir.IntType(32)
        elif (node == "flutuante" or node == "num_flutuante"):
            return ir.DoubleType()

    def execution_engine(self):
        target = binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        backing_mod = binding.parse_assembly("")
        engine = binding.create_mcjit_compiler(backing_mod, target_machine)
        return engine

        binding.load_library_permanently("//funcoes.so")        


    def compile_ir(self):
        self.mod = binding.parse_assembly(str(self.module))
        self.mod.verify()
        self.ee.add_module(self.mod)
        self.ee.finalize_object()
        return self.mod

if __name__ == '__main__':
    import sys
    code = open(sys.argv[1])
    module = ir.Module('module_tpp')
    gen = Gen(code.read(), module)

    # print(gen.table)
    print(gen.module)
    pprint.pprint(gen.table, depth=3, width="300")

