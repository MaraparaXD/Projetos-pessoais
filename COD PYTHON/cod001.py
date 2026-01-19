# Coletar os números
num1 = float(input('Digite o 1° número: '))
num2 = float(input('Digite o 2° número: '))

# Comparamos ambos os números e descobrimos qual é o maior
if num1 > num2:
    print(f'O primeiro número é maior: {num1}')
elif num2 > num1:
    print(f'O segundo número é maior: {num2}')
else: # Caso os números sejam iguais
    print('Os dois números são iguais.')