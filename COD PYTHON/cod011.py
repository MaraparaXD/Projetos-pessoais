#Coletando números 
inicio = int(input("Digite o primeiro número inteiro: "))
fim = int(input("Digite o segundo número inteiro: "))

#Estrutura do contador
if inicio < fim:

    for i in range(inicio+1, fim):
        print(i)
elif fim > inicio:

    for i in range(fim+1,inicio):
        print(i)
else:
    print("Os dois números são igaus.") 