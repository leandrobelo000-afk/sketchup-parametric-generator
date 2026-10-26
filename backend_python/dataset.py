import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .schemas import InputGeracaoSchema, ObjetoGeradoSchema

EXTENSOES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def registrar_aprovado(pasta: Path, objeto: ObjetoGeradoSchema, entrada: Optional[InputGeracaoSchema]) -> None:
    """
    Guarda no computador do arquiteto cada modelo que ele aprovou e mandou ao SketchUp.
    Estes pares entrada → JSON aprovado são a base para treinar o modelo próprio no futuro.
    As imagens ficam em arquivos à parte, nomeadas pelo hash, para não repetir a mesma imagem.
    """
    pasta_imagens = pasta / "imagens"
    pasta_imagens.mkdir(parents=True, exist_ok=True)

    imagens = []
    for imagem in (entrada.imagens if entrada else []):
        dados = base64.b64decode(imagem.dados_base64)
        nome = hashlib.sha256(dados).hexdigest()[:32] + EXTENSOES[imagem.mime_type]
        arquivo = pasta_imagens / nome
        if not arquivo.exists():
            arquivo.write_bytes(dados)
        imagens.append(nome)

    registro = {
        "data": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prompt_usuario": entrada.prompt_usuario if entrada else None,
        "dimensoes_limite": entrada.dimensoes_limite.model_dump() if entrada and entrada.dimensoes_limite else None,
        "refinamento": bool(entrada and entrada.objeto_base),
        # Num refinamento, o par de treino é (modelo anterior + ajuste pedido) → objeto aprovado
        "objeto_base": entrada.objeto_base.model_dump() if entrada and entrada.objeto_base else None,
        "imagens": imagens,
        "objeto": objeto.model_dump(),
    }
    with open(pasta / "aprovados.jsonl", "a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
