inteiro: k
inteiro: j
{inteiro: n}
flutuante: leo

flutuante teste(inteiro: t, flutuante: a)
fim

flutuante fatorial(inteiro: n)
	inteiro: fat
	flutuante: leo
	fat := leo
	se n > 0 então {não calcula se n > 0}
		fat := -1+2
		k := 2
		repita
			fat := fat * n
			n := n - 1
		até n = 0
		retorna(fat) {retorna o valor do fatorial de n}
	senão
		retorna(0)
	fim
fim

flutuante principal()
	inteiro: n
	inteiro: t
	inteiro: a
	leia(n)
	fatorial(n)
	escreva(fatorial(n))
fim