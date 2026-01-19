# Coletamos os preços dos 3 anos
preco_ano1 = float(input('Informe o preço médio do carro no primeiro ano: '))
preco_ano2 = float(input('Informe o preço médio do carro no segundo ano: '))
preco_ano3 = float(input('Informe o preço médio do carro no terceiro ano: '))

# Determinamos o maior valor através de comparações
maior = preco_ano1
if preco_ano2 > maior:
  maior = preco_ano2
if preco_ano3 > maior:
  maior = preco_ano3

# Determinamos o menor valor através de comparações
menor = preco_ano1
if preco_ano2 < menor:
  menor = preco_ano2
if preco_ano3 < menor:
  menor = preco_ano3

# Mostramos o resultado
print(f'O preço mais alto foi de R$ {maior}.')
print(f'O preço mais baixo foi de R$ {menor}.')