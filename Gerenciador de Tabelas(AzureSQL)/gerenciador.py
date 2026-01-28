import pyodbc
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# --- CONFIGURAÇÃO ---
SERVER = '' # <--- ⚠️ URL DO SERVIDOR
DATABASE = '' # <--- ⚠️ NOME DO BANCO DE DADOS
USERNAME = '' # <--- ⚠️ SEU USUÁRIO
SENHA    = '' # <--- ⚠️ SUA SENHA
DRIVER   = '{ODBC Driver 18 for SQL Server}'

console = Console()

def get_connection():
    conn_str = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={SENHA};Encrypt=yes;TrustServerCertificate=yes;'
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        console.print(f"[bold red]❌ Erro de Conexão:[/bold red] {e}")
        return None

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def listar_tabelas(cursor):
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    return [row[0] for row in cursor.fetchall()]

# ==============================================================================
# 1. CRIAR TABELA
# ==============================================================================
def menu_criar_tabela(cursor):
    console.rule("[bold green]CRIAR NOVA TABELA[/bold green]")
    nome_tabela = Prompt.ask("Nome da nova Tabela (ou 'SAIR' para cancelar)")
    if nome_tabela.upper() == 'SAIR': return

    colunas_definidas = []
    while True:
        limpar_tela()
        console.rule(f"[bold green]CRIANDO TABELA: {nome_tabela}[/bold green]")
        
        # Preview
        if colunas_definidas:
            tb = Table()
            tb.add_column("Coluna e Tipo", style="cyan")
            for col in colunas_definidas: tb.add_row(col)
            console.print(tb)
        
        console.print("\n[bold yellow]Como adicionar:[/bold yellow] Digite [Nome] [Tipo].")
        console.print("Ex: [green]id INT PRIMARY KEY IDENTITY[/green]")
        console.print("Comandos: [bold blue]SALVAR[/bold blue] = Terminar e Criar | [bold red]SAIR[/bold red] = Cancelar tudo")
        
        entrada = Prompt.ask("\nNova Coluna")
        
        # Verifica comandos exatos
        if entrada.upper() == 'SAIR': return
        elif entrada.upper() == 'SALVAR': 
            if not colunas_definidas:
                console.print("[red]Adicione pelo menos uma coluna![/red]")
                Prompt.ask("Enter...")
                continue
            break
            
        if len(entrada.strip()) > 0: colunas_definidas.append(entrada)

    sql = f"CREATE TABLE {nome_tabela} ({', '.join(colunas_definidas)})"
    
    if Confirm.ask("Executar?"):
        try:
            cursor.execute(sql)
            cursor.commit()
            console.print(f"\n[bold green]✅ Tabela '{nome_tabela}' criada![/bold green]")
        except Exception as e: console.print(f"\n[bold red]Erro SQL:[/bold red] {e}")
    Prompt.ask("\nEnter para voltar...")

# ==============================================================================
# 2. SELECT
# ==============================================================================
def menu_select(cursor):
    tabelas = listar_tabelas(cursor)
    if not tabelas: return

    while True:
        limpar_tela()
        console.rule("[bold blue]VISUALIZAR DADOS[/bold blue]")
        for idx, t in enumerate(tabelas): console.print(f"[{idx}] {t}")

        escolha = Prompt.ask("\nID da tabela (ou 'SAIR' voltar)")
        if escolha.upper() == 'SAIR': break

        try:
            tabela = tabelas[int(escolha)]
            cursor.execute(f"SELECT * FROM {tabela}")
            cols = [c[0] for c in cursor.description]
            rows = cursor.fetchall()

            t_dados = Table(title=f"Dados: {tabela}")
            for c in cols: t_dados.add_column(c)
            for r in rows: t_dados.add_row(*[str(x) for x in r])
            console.print(t_dados)
            Prompt.ask("\nEnter para nova consulta...")
        except: pass

# ==============================================================================
# 3. INSERT
# ==============================================================================
def menu_insert(cursor):
    console.rule("[bold green]INSERIR DADOS[/bold green]")
    tabelas = listar_tabelas(cursor)
    if not tabelas: return

    for idx, t in enumerate(tabelas): console.print(f"[{idx}] {t}")
    escolha = Prompt.ask("\nEscolha a tabela (ou 'SAIR')")
    if escolha.upper() == 'SAIR': return

    try:
        tabela = tabelas[int(escolha)]
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabela}'")
        colunas_db = [row[0] for row in cursor.fetchall()]
        
        console.print(f"\n[bold cyan]Preenchendo '{tabela}'[/bold cyan]")
        console.print("[dim](Deixe vazio para NULL/Identity. Digite 'SAIR' no valor para cancelar)[/dim]")
        
        campos, valores = [], []

        for col in colunas_db:
            valor = Prompt.ask(f"Valor para [magenta]{col}[/magenta]")
            
            # Segurança extra: se digitar SAIR no meio do insert, cancela
            if valor.upper() == 'SAIR':
                console.print("[red]Inserção cancelada.[/red]")
                return

            if valor.strip() != "":
                campos.append(col)
                valores.append(valor)
        
        if not campos: return

        placeholders = ", ".join(["?"] * len(campos))
        sql = f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({placeholders})"

        cursor.execute(sql, valores)
        cursor.commit()
        console.print(f"\n[bold green]✅ Inserido![/bold green]")
        
    except Exception as e: console.print(f"\n[bold red]Erro:[/bold red] {e}")
    Prompt.ask("Enter para voltar...")

# ==============================================================================
# 4. UPDATE
# ==============================================================================
def menu_update(cursor):
    console.rule("[bold orange1]ATUALIZAR DADOS (UPDATE)[/bold orange1]")
    tabelas = listar_tabelas(cursor)
    if not tabelas: return

    for idx, t in enumerate(tabelas): console.print(f"[{idx}] {t}")
    escolha = Prompt.ask("\nID da tabela para alterar (ou 'SAIR')")
    if escolha.upper() == 'SAIR': return

    try:
        tabela = tabelas[int(escolha)]
        
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabela}'")
        colunas = [row[0] for row in cursor.fetchall()]
        console.print(f"\nColunas: [cyan]{', '.join(colunas)}[/cyan]")
        
        col_alvo = Prompt.ask("Qual coluna mudar?")
        if col_alvo not in colunas: return

        novo_valor = Prompt.ask(f"Novo valor para '{col_alvo}'")

        col_filtro = Prompt.ask(f"Coluna do WHERE (ex: id)", default=colunas[0])
        val_filtro = Prompt.ask(f"Valor do '{col_filtro}'")

        sql = f"UPDATE {tabela} SET {col_alvo} = ? WHERE {col_filtro} = ?"
        
        console.print(Panel(f"[dim]SQL:[/dim] UPDATE {tabela} SET {col_alvo}='{novo_valor}' WHERE {col_filtro}='{val_filtro}'"))
        
        if Confirm.ask("Confirmar?"):
            cursor.execute(sql, (novo_valor, val_filtro))
            cursor.commit()
            console.print(f"[bold green]✅ Linhas afetadas: {cursor.rowcount}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Erro:[/bold red] {e}")
    Prompt.ask("Enter para voltar...")

# ==============================================================================
# 5. DROP
# ==============================================================================
def menu_drop(cursor):
    tabelas = listar_tabelas(cursor)
    if not tabelas: return
    
    for idx, t in enumerate(tabelas): console.print(f"[{idx}] {t}")
    escolha = Prompt.ask("\nID da tabela para EXCLUIR (ou 'SAIR')")
    if escolha.upper() == 'SAIR': return

    try:
        tabela = tabelas[int(escolha)]
        if Confirm.ask(f"[bold red]Apagar '{tabela}' PERMANENTEMENTE?[/bold red]"):
            cursor.execute(f"DROP TABLE {tabela}")
            cursor.commit()
            console.print("[green]Tabela Deletada.[/green]")
    except: pass
    Prompt.ask("Enter...")

# ==============================================================================
# MENU
# ==============================================================================
def main():
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()

    while True:
        limpar_tela()
        console.print(Panel("[bold white]🛠️  DBA MASTER 6.0 (Blindado)[/bold white]", style="purple"))
        console.print("[1] Criar Tabela")
        console.print("[2] Ler Dados (Select)")
        console.print("[3] Inserir Dados (Insert)")
        console.print("[4] Atualizar (Update)")
        console.print("[5] Excluir (Drop)")
        console.print("[0] SAIR")
        
        op = Prompt.ask("Opção", choices=["0","1","2","3","4","5"])

        if op == '0': break
        elif op == '1': menu_criar_tabela(cursor)
        elif op == '2': menu_select(cursor)
        elif op == '3': menu_insert(cursor)
        elif op == '4': menu_update(cursor)
        elif op == '5': menu_drop(cursor)
        
    conn.close()

if __name__ == "__main__":
    main()
