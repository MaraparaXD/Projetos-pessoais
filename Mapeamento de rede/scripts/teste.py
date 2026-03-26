import requests
import hashlib

IP = "192.168.1.244:8080"
SENHA = "260832leo"

print("-" * 50)
print("🕵️‍♂️ INICIANDO RAIO-X DO ROTEADOR INTELBRAS")
print("-" * 50)

# 1. Preparando a chave
hash_md5 = hashlib.md5(SENHA.encode('utf-8')).hexdigest()
senha_cripto = f"{hash_md5}zendar"
print(f"🔑 Chave forjada: {senha_cripto}")

sessao = requests.Session()
cabecalho_base = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
sessao.headers.update(cabecalho_base)

# 2. O Teste da Portaria (POST)
url_post = f"http://{IP}/login/Auth"
print(f"\n🚪 1. Batendo na porta: {url_post}")
try:
    res_post = sessao.post(
        url_post, 
        data={"password": senha_cripto}, 
        headers={"Cookie": f"password={senha_cripto}", "X-Requested-With": "XMLHttpRequest", "Referer": f"http://{IP}/login.html"},
        timeout=5
    )
    print(f"   ↳ Status HTTP: {res_post.status_code}")
    print(f"   ↳ Resposta Interna: {res_post.text.strip()[:150]}")
except Exception as e:
    print(f"   ↳ ❌ Erro: {e}")

# 3. O Teste do Cofre (GET)
url_get = f"http://{IP}/goform/getOnlineList?0.135792468"
print(f"\n📦 2. Tentando abrir o cofre: {url_get}")
try:
    res_get = sessao.get(
        url_get,
        headers={"Cookie": f"password={senha_cripto}", "X-Requested-With": "XMLHttpRequest", "Referer": f"http://{IP}/online_list.html"},
        timeout=5
    )
    print(f"   ↳ Status HTTP: {res_get.status_code}")
    print(f"   ↳ Resposta Interna: {res_get.text.strip()[:150]}")
except Exception as e:
    print(f"   ↳ ❌ Erro: {e}")

print("-" * 50)