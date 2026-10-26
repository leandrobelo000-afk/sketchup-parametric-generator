import asyncio

from backend_python.ai_service import ProvedorMock
from backend_python.schemas import Dimensoes3D, InputGeracaoSchema
from backend_python.validacao import validar_geometria


def mesa(**limites):
    entrada = InputGeracaoSchema(prompt_usuario="mesa", dimensoes_limite=Dimensoes3D(**limites) if limites else None)
    return asyncio.run(ProvedorMock().gerar(entrada))


def test_mock_e_geometria_valida():
    assert validar_geometria(mesa()) == []
    assert validar_geometria(mesa(comprimento_x=80, largura_y=40, altura_z=30)) == []


def test_objeto_maior_que_o_limite():
    erros = validar_geometria(mesa(), Dimensoes3D(comprimento_x=90, largura_y=50, altura_z=45))
    assert any("comprimento_x" in e for e in erros)


def test_peca_fora_da_caixa_e_flutuando():
    objeto = mesa()
    for peca in objeto.pecas:
        peca.posicao_relativa.z += 10
    erros = validar_geometria(objeto)
    assert any("ultrapassa a altura" in e for e in erros)
    assert any("apoiada no chão" in e for e in erros)


def test_posicao_negativa():
    objeto = mesa()
    objeto.pecas[1].posicao_relativa.x = -3
    assert any("posição negativa" in e for e in validar_geometria(objeto))
