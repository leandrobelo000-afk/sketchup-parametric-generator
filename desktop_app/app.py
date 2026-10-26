"""
App desktop do SketchUp AI Assistant.

Sobe o backend FastAPI numa thread, em 127.0.0.1 e numa porta livre, e abre a janela
pywebview com a interface. A porta e o token são gravados em ~/.sketchup_ai_assistant/conexao.json,
que é onde o plugin do SketchUp os encontra.
"""
import argparse
import json
import os
import secrets
import signal
import socket
import sys
import threading
import time
from pathlib import Path

# Permite rodar `python desktop_app/app.py` a partir da raiz do repositório
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn
from dotenv import load_dotenv

from backend_python.main import create_app

PASTA_CONEXAO = Path.home() / ".sketchup_ai_assistant"
ARQUIVO_CONEXAO = PASTA_CONEXAO / "conexao.json"


def pasta_ui() -> Path:
    # No executável do PyInstaller os arquivos extras ficam em sys._MEIPASS
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "ui"


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def escrever_conexao(porta: int, token: str) -> None:
    PASTA_CONEXAO.mkdir(exist_ok=True)
    ARQUIVO_CONEXAO.write_text(json.dumps({"porta": porta, "token": token, "pid": os.getpid()}))


def remover_conexao() -> None:
    try:
        dados = json.loads(ARQUIVO_CONEXAO.read_text())
        # Só apaga se o arquivo for desta instância do app
        if dados.get("pid") == os.getpid():
            ARQUIVO_CONEXAO.unlink()
    except (OSError, ValueError):
        pass


def iniciar_servidor(porta: int, token: str) -> uvicorn.Server:
    app = create_app(token=token, ui_dir=pasta_ui())
    # log_config=None: no executável sem console não existe stdout para o log padrão do uvicorn
    servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=porta, log_config=None))
    threading.Thread(target=servidor.run, daemon=True).start()

    limite = time.monotonic() + 10
    while not servidor.started:
        if time.monotonic() > limite:
            raise RuntimeError("O servidor local não iniciou em 10 segundos")
        time.sleep(0.05)
    return servidor


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="SketchUp AI Assistant")
    parser.add_argument("--sem-janela", action="store_true", help="Só o servidor, sem abrir a janela (testes)")
    parser.add_argument("--porta", type=int, default=0, help="Porta fixa (padrão: uma porta livre)")
    args = parser.parse_args(argv)

    load_dotenv()
    porta = args.porta or porta_livre()
    token = secrets.token_urlsafe(24)
    servidor = iniciar_servidor(porta, token)
    escrever_conexao(porta, token)
    # Encerramento pelo sistema também apaga o arquivo de conexão (via finally)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    try:
        if args.sem_janela:
            print(f"Servidor em http://127.0.0.1:{porta} (Ctrl+C para sair)")
            while True:
                time.sleep(1)
        else:
            import webview
            # O token vai no fragmento da URL: a janela o lê sem que ele trafegue em requisições
            webview.create_window(
                "SketchUp AI Assistant",
                f"http://127.0.0.1:{porta}/ui/#token={token}",
                width=1100,
                height=760,
                min_size=(800, 600),
            )
            webview.start()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.should_exit = True
        remover_conexao()


if __name__ == "__main__":
    main()
