# Coletamos o turno de estudo
turno = input('Digite em qual turno você estuda (manhã, tarde ou noite): ')

# Comparamos a entrada com todas as opções e imprimimos o resultado.
if turno == 'manhã':
  print('Bom Dia!')
elif turno == 'tarde':
  print('Boa Tarde!')
elif turno == 'noite':
  print('Boa Noite!')
else:
  print('Valor Inválido!')