import sys
def main():
    if len(sys.argv) >= 2:
        # lexer = Lexer() 
        f = open(sys.argv[1])
        # lexer.test(f.read())  
        code = f.read() 
        print (code)

if __name__ == '__main__':
    main()            