# Coletamos os números a serem operados e solicitamos a operação desejada pela pessoa usuária
num1 = float(input('Informe o primeiro número: '))
num2 = float(input('Informe o segundo número: '))
operacao = input('Informe a operação desejada (+, -, *, /): ')

# Verificamos o operador que foi selecionado e executa a operação matemática conforme a seleção
if operacao == '+':
    resultado = num1 + num2
elif operacao == '-':
    resultado = num1 - num2
elif operacao == '*':
    resultado = num1 * num2
elif operacao == '/':
    resultado = num1 / num2
else: # Especificamos um resultado caso a pessoa usuária não digite alguma das operações corretamente.
    print('Operação inválida, resultado da operação será 0')
    resultado = 0 

#  Fazemos as mesmas verificações das questões anteriores para fazer o relatório do cálculo entre números
if resultado % 1 == 0:
    print('O resultado é inteiro.')
else:
    print('O resultado é decimal.')

if resultado > 0:
    print('O resultado é positivo.')
elif resultado == 0:
    print('O resultado é neutro.')
else:
    print('O resultado é negativo.')

if resultado % 2 == 0:
    print('O resultado é par.')
else:
    print('O resultado é ímpar.')