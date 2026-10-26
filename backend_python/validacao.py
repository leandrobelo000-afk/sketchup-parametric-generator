from typing import List, Optional

from .schemas import Dimensoes3D, ObjetoGeradoSchema

# Folga para erros de arredondamento da IA, em cm
TOLERANCIA = 0.5


def validar_geometria(objeto: ObjetoGeradoSchema, limites: Optional[Dimensoes3D] = None) -> List[str]:
    """
    Confere se as peças cabem no objeto (e nos limites pedidos) e estão apoiadas no chão.
    Devolve a lista de problemas encontrados; lista vazia significa geometria válida.
    """
    erros = []
    caixa = objeto.dimensoes_totais

    if limites:
        for eixo in ("comprimento_x", "largura_y", "altura_z"):
            if getattr(caixa, eixo) > getattr(limites, eixo) + TOLERANCIA:
                erros.append(f"dimensoes_totais.{eixo} ({getattr(caixa, eixo)}) excede o limite ({getattr(limites, eixo)})")

    for peca in objeto.pecas:
        pos, dim = peca.posicao_relativa, peca.dimensoes
        if pos.x < -TOLERANCIA or pos.y < -TOLERANCIA or pos.z < -TOLERANCIA:
            erros.append(f"{peca.nome_peca}: posição negativa ({pos.x}, {pos.y}, {pos.z})")
        if pos.x + dim.comprimento_x > caixa.comprimento_x + TOLERANCIA:
            erros.append(f"{peca.nome_peca}: ultrapassa o comprimento total no eixo X")
        if pos.y + dim.largura_y > caixa.largura_y + TOLERANCIA:
            erros.append(f"{peca.nome_peca}: ultrapassa a largura total no eixo Y")
        if pos.z + dim.altura_z > caixa.altura_z + TOLERANCIA:
            erros.append(f"{peca.nome_peca}: ultrapassa a altura total no eixo Z")

    if objeto.pecas and min(p.posicao_relativa.z for p in objeto.pecas) > TOLERANCIA:
        erros.append("nenhuma peça está apoiada no chão (z = 0)")

    return erros
