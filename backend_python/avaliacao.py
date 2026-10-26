import unicodedata
from typing import List, Optional

from pydantic import BaseModel, Field

from .schemas import Dimensoes3D, ObjetoGeradoSchema
from .validacao import validar_geometria


class CasoAvaliacao(BaseModel):
    """Um pedido de teste e o que se espera do modelo gerado para ele."""
    id: str
    prompt_usuario: str
    dimensoes_limite: Optional[Dimensoes3D] = None
    pecas_min: int = Field(1, ge=1)
    pecas_max: int = Field(50, ge=1)
    # Cada item é uma lista de alternativas: basta uma aparecer em algum nome de peça
    pecas_esperadas: List[List[str]] = Field(default_factory=list)


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def avaliar_caso(caso: CasoAvaliacao, objeto: ObjetoGeradoSchema) -> dict:
    """
    Pontua um objeto gerado de 0 a 1 em três critérios de peso igual:
    geometria válida, quantidade de peças plausível e presença das peças esperadas.
    """
    erros = validar_geometria(objeto, caso.dimensoes_limite)
    quantidade_ok = caso.pecas_min <= len(objeto.pecas) <= caso.pecas_max

    nomes = [_normalizar(p.nome_peca) for p in objeto.pecas]
    faltando = [
        "/".join(alternativas) for alternativas in caso.pecas_esperadas
        if not any(_normalizar(alt) in nome for alt in alternativas for nome in nomes)
    ]
    cobertura = 1.0 if not caso.pecas_esperadas else 1 - len(faltando) / len(caso.pecas_esperadas)

    nota = (float(not erros) + float(quantidade_ok) + cobertura) / 3
    return {
        "id": caso.id,
        "nota": round(nota, 3),
        "geometria_valida": not erros,
        "erros_geometria": erros,
        "quantidade_pecas": len(objeto.pecas),
        "quantidade_ok": quantidade_ok,
        "pecas_faltando": faltando,
    }
