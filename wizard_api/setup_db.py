import pandas as pd
import random

def gerar_massa_v4_correta():
    dados = []
    # Testando o Mapper com variações de nomes
    for i in range(1, 151):
        # 15% de chance de pedir mais que o estoque de 50
        qtd = random.randint(1, 40) if i % 8 != 0 else random.randint(55, 90)
        
        dados.append({
            "id": None, # A API vai preencher com o ID oficial do banco
            "Item": f"Componente Tech Wizard V{i}",
            "Preco": None,
            "Qtd": qtd,
            "Vendedor": random.choice(["Tiago", "Ludmila", "Zendar", "Duraes_Staff"])
        })

    df = pd.DataFrame(dados)
    df.to_csv("carga_v4_150_itens.csv", index=False)
    print("✨ Arquivo 'carga_v4_150_itens.csv' gerado com ID incluso!")

if __name__ == "__main__":
    gerar_massa_v4_correta()