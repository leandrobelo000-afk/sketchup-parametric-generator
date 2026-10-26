"""Sobe o app desktop de verdade (sem janela) e conversa com ele pelo cliente Ruby do plugin."""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(shutil.which("ruby") is None, reason="Ruby não instalado")
def test_plugin_ruby_conversa_com_o_app(tmp_path):
    ambiente = {**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path), "SKETCHUP_AI_PROVEDOR": "mock"}
    app = subprocess.Popen([sys.executable, str(RAIZ / "desktop_app" / "app.py"), "--sem-janela"], env=ambiente)
    conexao = tmp_path / ".sketchup_ai_assistant" / "conexao.json"
    try:
        limite = time.monotonic() + 20
        while not conexao.exists():
            assert app.poll() is None, "o app encerrou antes de gravar o arquivo de conexão"
            assert time.monotonic() < limite, "o app não gravou o arquivo de conexão"
            time.sleep(0.1)
        assert set(json.loads(conexao.read_text())) == {"porta", "token", "pid"}

        resultado = subprocess.run(
            ["ruby", str(RAIZ / "tests" / "ruby" / "integracao_cliente.rb")],
            env=ambiente, capture_output=True, text=True, timeout=30,
        )
        assert resultado.returncode == 0, resultado.stdout + resultado.stderr
        assert "OK" in resultado.stdout
    finally:
        app.terminate()
        app.wait(timeout=10)
