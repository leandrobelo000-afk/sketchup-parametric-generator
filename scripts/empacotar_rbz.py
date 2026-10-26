"""
Empacota a extensão do SketchUp em dist/sketchup_ai_assistant.rbz (um zip com o loader e a pasta).
Uso, na raiz do repositório: python scripts/empacotar_rbz.py
"""
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "frontend_ruby"
DESTINO = RAIZ / "dist" / "sketchup_ai_assistant.rbz"

DESTINO.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as rbz:
    rbz.write(ORIGEM / "sketchup_ai_assistant.rb", "sketchup_ai_assistant.rb")
    for arquivo in sorted((ORIGEM / "sketchup_ai_assistant").rglob("*.rb")):
        rbz.write(arquivo, arquivo.relative_to(ORIGEM).as_posix())

print(f"Extensão gerada em {DESTINO}")
