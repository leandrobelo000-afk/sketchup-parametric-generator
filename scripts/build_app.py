"""
Gera o app desktop com o PyInstaller em dist/SketchUpAIAssistant/.

`--onedir` e `--noupx` reduzem os falsos positivos de antivírus em executáveis sem assinatura.
Uso, na raiz do repositório: python scripts/build_app.py
"""
import os
import sys
from pathlib import Path

import PyInstaller.__main__

RAIZ = Path(__file__).resolve().parent.parent

PyInstaller.__main__.run([
    str(RAIZ / "desktop_app" / "app.py"),
    "--name", "SketchUpAIAssistant",
    "--onedir",
    "--noupx",
    "--windowed",
    "--noconfirm",
    "--paths", str(RAIZ),
    "--add-data", f"{RAIZ / 'desktop_app' / 'ui'}{os.pathsep}ui",
    "--collect-submodules", "backend_python",
    "--distpath", str(RAIZ / "dist"),
    "--workpath", str(RAIZ / "build"),
    "--specpath", str(RAIZ / "build"),
    *sys.argv[1:],
])
