# Coletamos a data
dia = int(input('Digite o dia: '))
mes = int(input('Digite o mês: '))
ano = int(input('Digite o ano: '))

# Análise de fevereiro
if mes == 2:
  # Verificamos se é ou não um ano bissexto
  if ano % 4 == 0 and (ano % 400 == 0 or ano % 100 != 0):
    dias_fevereiro = 29
  else:
    dias_fevereiro = 28
  # Verificamos se o dia colocado corresponde ao máximo de dias de fevereiro
  if dia >= 1 and dia <= dias_fevereiro:
    print('Data válida')
  else:
    print('Data inválida')
# Verificamos meses terminados em 31 dias
elif mes in [1, 3, 5, 7, 8, 10, 12]:
  if dia >= 1 and dia <= 31:
    print('Data válida')
  else:
    print('Data inválida')
# Verificamos meses terminados em 30 dias
elif mes in [4, 6, 9, 11]:
  if dia >= 1 and dia <= 30:
    print('Data válida')
  else:
    print('Data inválida')
# Caso o mês não esteja entre 1 e 12
else:
  print('Data inválida')