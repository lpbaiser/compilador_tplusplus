
inteiro teste(inteiro: x)
	inteiro: s
	inteiro: f
	f := 0
	s:= 2
	se s < 3 então
		repita
			f := f * 3
			s := s + 1
		até s = 5
	fim
		
fim

inteiro principal()
	inteiro: x
	inteiro: j
	x:= + 2
	j:= x
	teste(x)
	escreva(j)

fim