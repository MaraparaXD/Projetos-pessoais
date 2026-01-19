#distancia A x B
colonia_A = 3
colonia_B = 10

#% de crescimento
taxa_A = 0.03
taxa_B = 0.015

dias = 0

while colonia_A <= colonia_B:
    colonia_A *= + taxa_A
    colonia_B *= + taxa_B

    dias += 1

#resultado
print(f'Irá levar {dias} dias para ultrapassar a colonia B')