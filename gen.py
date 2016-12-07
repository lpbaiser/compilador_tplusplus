#-------------------------------------------------------------------------
# gen.py
# Analisador léxico para a linguagem t++
# Autor: Leonardo Pontes Baiser
#-------------------------------------------------------------------------

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
        binding.load_library_permanently(os.getcwd() + '//funcoesC.so')
        self.ee = self.create_execution_engine()

        # self.passes = passes
        self.optimization = optz
        self.builder = None
        self.funcao = None
        # self.symbols = symbols
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
        elif (comp == "condicional"):
            self.gen_condicional(node.child[0])
        elif (comp == "repeticao"):
            self.gen_repeticao(node.child[0])
        elif (comp == "retorna"): #ok
            self.gen_retorna(node.child[0])
        elif (comp == "leia"):
            self.gen_leia(node.child[0])
        elif (comp == "escreva"):
            self.gen_escreva(node.child[0])

    def gen_atribuicao(self, node):
        nome = self.scope+"@"+node.value
        if nome not in self.table.keys():
            nome = "global@"+node.value
        ref_var = self.table[nome][5]
        tipo_exp = self.gen_expressao(node.child[0])
        self.builder.store(tipo_exp, ref_var)

    def gen_chamada(self, node):
        funcao = self.builder.load(self.table[node.value][4])
        argumentos = self.gen_expressao_args(node.child[0])
        return self.builder.call(funcao,argumentos,name="CHAMADA")

    def gen_expressao_args(self, node):
        if node == None:
            return []
        else:
            argumentos = []
            argumento = self.gen_expressao(node.child[0])
            argumentos.append(argumento)
            if len(node.child) == 2:
                argumentos = argumentos + self.gen_expressao_args(node.child[1])
            return argumentos

    def gen_condicional(self, node):
        self.gen_expressao_binaria(node.child[0])
        self.gen_corpo(node.child[1])
        if len(node.child) == 3:
            self.gen_corpo(node.child[2])

    def gen_repeticao(self, node):
        repeticao_start = self.funcao.append_basic_block('LOOP')
        repeticao_fim = self.funcao.append_basic_block('FIM_LOOP')
        self.builder.branch(repeticao_start)
        self.builder.position_at_start(repeticao_start)
        self.gen_corpo(node.child[0])
        condicao_stop = self.gen_expressao_binaria(node.child[1])
        print(condicao_stop)
        self.builder.cbranch(condicao_stop, repeticao_fim, repeticao_start)
        self.builder.position_at_start(repeticao_fim)

    def gen_retorna(self, node):
        ref_funcao = self.gen_expressao(node.child[0])
        self.builder.ret(ref_funcao)

    def gen_escreva(self, node):
        escreve = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
        self.escreva = ir.Function(self.module, escreve, 'ESCREVE')
        exp = self.gen_expressao(node.child[0])
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

    def gen_expressao(self, node):

        exp = node.child[0].type
        if (exp == "expressao_calculo"):
           return self.gen_expressao_calculo(node.child[0])
        elif (exp == "expressao_numerica"):
            return self.gen_expressao_numerica(node.child[0])
        elif (exp == "expressao_parenteses"):
            return self.gen_expressao_parenteses(node.child[0])
        elif (exp == "expressao_unaria"):
            return self.gen_expressao_unaria(node.child[0])
        elif (exp == "expressao_identificador"):
            return self.gen_expressao_identificador(node.child[0])
        elif (exp == "chamada"):
            return self.gen_chamada(node.child[0])

    def gen_expressao_calculo(self, node):
        tipo1 = self.gen_expressao(node.child[0])
        tipo2 = self.gen_expressao(node.child[1])

        if node.value == "+":
            ref = self.builder.fadd(tipo1, tipo2, name='ADD')
        elif node.value == "-":
            ref = self.builder.fsub(tipo1, tipo2, name='SUB')
        elif node.value == "*":
            ref = self.builder.fmul(tipo1, tipo2, name='MUL')
        elif node.value == "/":
            ref = self.builder.fdiv(tipo1, tipo2, name='DIV')
        return ref

    def gen_expressao_numerica(self, node):
        return ir.Constant(self.gen_tipo(node.child[0].type), node.child[0].value)

    def gen_expressao_parenteses(self, node):
        return self.gen_expressao(node.child[0])

    def gen_expressao_unaria(self, node):
        ref_unaria = self.gen_expressao(node.child[0])
        if node.value == "+":
            return ref_unaria
        elif node.value == "-":
            return self.builder.fmul(ref_unaria, ir.Constant(ref_unaria.type, -1), name='MUL')

    def gen_expressao_identificador(self, node):
        nome = self.scope+"@"+node.value
        if nome not in self.table.keys():
            nome = "global@"+node.value
        ref_var = self.table[nome][5]
        return self.builder.load(ref_var)

    def gen_expressao_binaria(self, node):
        exp = node.child[0].type
        if (exp == "expressao_binaria_com_parenteses"):
            return self.gen_expressao_binaria_com_parenteses(node.child[0])
        elif (exp == "expressao_binaria_sem_parenteses"):
            return self.gen_expressao_binaria_sem_parenteses(node.child[0])

    def gen_expressao_binaria_sem_parenteses(self, node):
        tipo1 = self.gen_expressao(node.child[0])
        tipo2 = self.gen_expressao(node.child[1])
        simbolo = node.value
        if simbolo == "=":
            exp = self.builder.icmp_signed("==", tipo1, tipo2, 'cmptmp')
        else:
            exp = self.builder.icmp_signed(node.value, tipo1, tipo2, 'cmptmp')
        return exp


    def gen_expressao_binaria_com_parenteses(self, node):
        print (node.child[0].child[0])
        self.gen_expressao_binaria(node.child[0])

    def gen_tipo(self, node):
        if (node == "inteiro" or node == "num_inteiro"):
            return ir.IntType(32)
        elif (node == "flutuante" or node == "num_flutuante"):
            return ir.DoubleType()

    def compile_ir(self):
        self.mod = binding.parse_assembly(str(self.module))
        self.mod.verify()
        self.ee.add_module(self.mod)
        self.ee.finalize_object()
        return self.mod

    # def compile_ir(self):
    #     mod = binding.parse_assembly(str(self.module))
    #     mod.verify()
    #     self.ee.add_module(mod)
    #     self.ee.finalize_object()
    #     return mod

    # def gen_top(self, node):
    #     print ('gen_top')
    #     # print (node)
    #     node = node.child[0]
    #     print ('node type: ' + node.type)
    #     if node.type == 'decl':
    #         self.gen_definition(node)	
    #         if self.optimization:
    #             self.passes.run(self.func)
    #         if self.debug:
    #             print(self.func)

    # def gen_definition(self, node):
    #     print('ptype ', node.value)
    #     self.gen_prototype(node.child[0], node.child[0].value)
    #     self.gen_block()
    #     result = self.gen_expr(node.child[1])
    #     self.builder.ret(result)

    # def gen_prototype(self, node, name=''):
    #     # tratamento de funções redefinidas
    #     print("Função:", name)
    #     if name and name in self.symbols.keys():
    #         self.symbols.pop(name)
    #         self.module.globals.pop(name)
    #         self.module._sequence.remove(name)
    #     node = node.child[0]
    #     args = self.gen_arg_names(node)
    #     num_args = len(args)
    #     ty_func = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()] * num_args)
    #     self.func = ir.Function(self.module, ty_func, name=name)
    #     self.symbols[self.func.name] = {}
    #     for i, arg in enumerate(args):
    #         self.func.args[i].name = arg
    #         self.symbols[self.func.name][arg] = self.func.args[i]
    #     for i in self.module.functions:
    #         print(i)

    # def gen_block(self):
    #     block = self.func.append_basic_block('entry')
    #     self.builder = ir.IRBuilder(block)

    # def gen_arg_names(self, node):
    #     args = []
    #     while node and node.type == 'declaracao_args':
    #         args.append(node.value)
    #         if node.child:
    #             node = node.child[0]
    #         else:
    #             break
    #     return args

    # def gen_expr(self, node):
    #     node = node.child[0]
    #     if node.type == 'expressao_binaria':
    #         return self.gen_binary_expr(node)
    #     elif node.type == 'expressao_args':
    #         return self.gen_call_expr(node)
    #     elif node.type == 'condicional':
    #         return self.gen_if_expr(node)
    #     elif node.type == 'id_expr':
    #         return self.symbols[self.func.name][node.value]
    #     elif node.type == 'num_expr':
    #         return ir.Constant(ir.DoubleType(), node.value)

    # def gen_binary_expr(self, node):
    #     left = self.gen_expr(node.child[0])
    #     right = self.gen_expr(node.child[1])
    #     op = node.value
    #     # operações aritméticas
    #     if op == '+':
    #         return self.builder.fadd(left, right, 'addtmp')
    #     elif op == '-':
    #         return self.builder.fsub(left, right, 'subtmp')
    #     elif op == '*':
    #         return self.builder.fmul(left, right, 'multmp')
    #     elif op == '/':
    #         return self.builder.fdiv(left, right, 'divtmp')
    #     # operações lógicas
    #     if op == '=':
    #         return self.builder.fcmp_unordered('==', left, right, 'cmptmp')
    #     elif op == '>':
    #         return self.builder.fcmp_unordered('>', left, right, 'cmptmp')
    #     elif op == '>=':
    #         return self.builder.fcmp_unordered('>=', left, right, 'cmptmp')
    #     elif op == '<':
    #         return self.builder.fcmp_unordered('<', left, right, 'cmptmp')
    #     elif op == '<=':
    #         return self.builder.fcmp_unordered('<=', left, right, 'cmptmp')

    # def gen_call_args(self, node):
    #     args = []
    #     while node:
    #         args.append(self.gen_expr(node.child[0]))
    #         if len(node.child) > 1:
    #             node = node.child[1]
    #         else:
    #             break
    #     return args

    # def gen_call_expr(self, node):
    #     args = self.gen_call_args(node.child[0])
    #     if node.value not in self.symbols.keys():
    #         err = "'%s' não está definida" % (node.value)
    #         self.func = None
    #         return err
    #     num_func_call = len(self.symbols[node.value])
    #     num_func = len(args)
    #     if num_func == num_func_call:
    #         func = self.module.get_global(node.value)
    #         return self.builder.call(func, args, 'calltmp')
    #     else:
    #         err = "'%s' espera %d argumento(s), %d passado(s)" % (node.value, num_func_call, num_func)
    #         self.func = None
    #         return err

    # def gen_if_expr(self, node):
    #     # formula a condição
    #     cond = self.gen_expr(node.child[0])
    #     # Estava dando erro
    #     #bool_cond = self.builder.fcmp_unordered('==', cond,
    #     #                              ir.Constant(ir.DoubleType(), 0), 'ifcond')
    #     # adiciona os blocos básicos
    #     then_block = self.func.append_basic_block('entao')
    #     else_block = self.func.append_basic_block('senao')
    #     merge_block = self.func.append_basic_block('ifcont')
    #     #self.builder.cbranch(bool_cond, then_block, else_block)
    #     self.builder.cbranch(cond, then_block, else_block)
    #     # emite o valor 'entao'
    #     self.builder.position_at_end(then_block)
    #     then_value = self.gen_expr(node.child[1])
    #     self.builder.branch(merge_block)
    #     then_block = self.builder.basic_block
    #     # emite o valor 'senao'
    #     self.builder.position_at_end(else_block)
    #     else_value = self.gen_expr(node.child[2])
    #     self.builder.branch(merge_block)
    #     else_block = self.builder.basic_block
    #     # finalizando o código e acionando os nós PHI
    #     self.builder.position_at_end(merge_block)
    #     phi = self.builder.phi(ir.DoubleType(), 'iftmp')
    #     phi.add_incoming(then_value, then_block)
    #     phi.add_incoming(else_value, else_block)
    #     return phi

if __name__ == '__main__':
    import sys
    code = open(sys.argv[1])
    module = ir.Module('module_tpp')
    gen = Gen(code.read(), module)

    print(gen.table)
    print(gen.module)


    # print_tree(s.tree)
    # print (s.parser.tokens)

    # print("Tabela de Simbolos:", s.table)
    # print_funcoes(s.table)
    # pprint.pprint(s.table, depth=3, width=500)
