#Adicionando nota
for i in range(15):
   nota = float(input(f'Insira a nota da pessoa usuária {i}: '))
#verificando se a nota está entre 0 a 5
   while (nota < 0) or (nota > 5):
     nota = float(input(f'Nota inválida, por favor insira a nota correta da pessoa usúaria {i}: '))

print("Verificação feita! Todas as notas são válidas")