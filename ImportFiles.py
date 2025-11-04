import os
import base64
import shutil
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === CONFIGURAÇÕES ===
PASTA_BASE = r"" #Diretorio da sua pasta principal.
MAP_FILE = Path(PASTA_BASE) / "pasta_map.json"
EXTENSOES_VALIDAS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".zip")

# === ENDPOINTS ===
#Adicione a URL respectiva de sua MID.
URL_API = "https://seudominio.rest.marketingcloudapis.com/asset/v1/content/assets"
URL_AUTH = "https://seudominio.auth.marketingcloudapis.com/v2/token"

# === CREDENCIAIS TOKEN ===
CLIENT_ID = ""
CLIENT_SECRET = ""
ACCOUNT_ID = ""
GRANT_TYPE = ""


# === MAPEAMENTO DE ASSET TYPES ===
# Fonte: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/base-asset-types.html
ASSET_TYPE_MAP = {
    ".pdf": {"name": "document", "id": 127},
    ".zip": {"name": "archive", "id": 13},
    ".jpg": {"name": "jpg", "id": 23},
    ".jpeg": {"name": "jpeg", "id": 22},
    ".png": {"name": "png", "id": 28},
    ".gif": {"name": "gif", "id": 20},
    ".bmp": {"name": "bmp", "id": 25},
    ".tif": {"name": "tiff", "id": 26},
    ".tiff": {"name": "tiff", "id": 26},
}


# === FUNÇÃO PARA OBTER TOKEN ===
def get_token():
    try:
        response = requests.post(
            URL_AUTH,
            json={
                "grant_type": GRANT_TYPE,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "account_id": ACCOUNT_ID
            },
            timeout=15
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                print("🔐 Token obtido com sucesso.")
                return token
        print(f"❌ Erro ao obter token ({response.status_code}): {response.text}")
        return None
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return None


# === TOKEN GLOBAL ===
API_TOKEN = get_token()


# === FUNÇÃO PARA LER MAPA DE PASTAS ===
def carregar_mapa():
    if not MAP_FILE.exists():
        print("⚠️ Criando arquivo de mapeamento vazio...")
        MAP_FILE.write_text("{}", encoding="utf-8")

    with open(MAP_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("❌ Erro ao ler o arquivo de mapeamento JSON.")
            return {}


# === FUNÇÕES DE UTILIDADE ===
def converter_para_base64(caminho_arquivo: Path) -> str:
    with open(caminho_arquivo, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def gerar_nome_com_data(nome_arquivo: str) -> str:
    nome_sem_ext = Path(nome_arquivo).stem
    data_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{nome_sem_ext}_{data_str}"


def get_asset_type(caminho_arquivo: Path) -> dict:
    """Define o tipo correto de asset conforme a extensão."""
    ext = caminho_arquivo.suffix.lower()
    return ASSET_TYPE_MAP.get(ext, {"name": "archive", "id": 13})


def enviar_asset(nome_arquivo: str, base64_str: str, categoria_id: str, asset_type: dict) -> bool:
    """Envia um asset (imagem/pdf) para o Marketing Cloud."""
    global API_TOKEN

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    nome_com_data = gerar_nome_com_data(nome_arquivo)

    payload = {
        "name": nome_com_data,
        "assetType": asset_type,
        "category": {"id": int(categoria_id)},
        "fileName": nome_arquivo,
        "file": base64_str,
        "isProtected": False
    }

    try:
        resp = requests.post(URL_API, headers=headers, json=payload, timeout=60)

        # Se o token expirou, tenta renovar automaticamente
        if resp.status_code == 401:
            print("⚠️ Token expirado. Renovando...")
            API_TOKEN = get_token()
            headers["Authorization"] = f"Bearer {API_TOKEN}"
            resp = requests.post(URL_API, headers=headers, json=payload, timeout=60)

        if resp.status_code in (200, 201):
            data = resp.json()
            asset_id = data.get("id")
            print(f"✅ Asset enviado: {nome_com_data} (categoria {categoria_id}, tipo {asset_type['name']}, id={asset_id})")
            return True
        else:
            print(f"⚠️ Falha ao enviar {nome_arquivo}: {resp.status_code} - {resp.text}")
            return False

    except Exception as e:
        print(f"❌ Erro ao enviar {nome_arquivo}: {e}")
        return False


def processar_arquivo(caminho_arquivo: Path, mapa_pastas: dict):
    """Processa um novo arquivo e faz o upload."""
    if not caminho_arquivo.suffix.lower() in EXTENSOES_VALIDAS:
        return

    pasta_nome = caminho_arquivo.parent.name
    categoria_id = mapa_pastas.get(pasta_nome)

    if not categoria_id:
        print(f"⚠️ Pasta '{pasta_nome}' não está mapeada no JSON.")
        return

    pasta_lidos = caminho_arquivo.parent / "lidos"
    pasta_lidos.mkdir(exist_ok=True)

    try:
        base64_str = converter_para_base64(caminho_arquivo)
        asset_type = get_asset_type(caminho_arquivo)
        if enviar_asset(caminho_arquivo.name, base64_str, categoria_id, asset_type):
            destino = pasta_lidos / caminho_arquivo.name
            shutil.move(str(caminho_arquivo), str(destino))
            print(f"📦 Movido para {destino}")
    except Exception as e:
        print(f"❌ Erro ao processar {caminho_arquivo.name}: {e}")


# === WATCHDOG HANDLER ===
class MonitorPastasHandler(FileSystemEventHandler):
    def __init__(self, mapa_pastas):
        super().__init__()
        self.mapa_pastas = mapa_pastas

    def on_created(self, event):
        if not event.is_directory:
            caminho = Path(event.src_path)
            time.sleep(2)
            print(f"📂 Novo arquivo detectado: {caminho}")
            processar_arquivo(caminho, self.mapa_pastas)


# === MONITORAMENTO ===
def iniciar_monitoramento():
    mapa_pastas = carregar_mapa()
    observer = Observer()
    handler = MonitorPastasHandler(mapa_pastas)

    for pasta in Path(PASTA_BASE).iterdir():
        if pasta.is_dir():
            print(f"👀 Monitorando pasta: {pasta}")
            observer.schedule(handler, str(pasta), recursive=False)

    observer.start()
    print("🚀 Monitoramento iniciado. Aguardando novos arquivos...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("🛑 Monitoramento encerrado.")
    observer.join()


# === EXECUÇÃO PRINCIPAL ===
if __name__ == "__main__":
    iniciar_monitoramento()
