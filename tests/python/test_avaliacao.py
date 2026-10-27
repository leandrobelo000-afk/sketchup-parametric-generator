import asyncio
import json
from pathlib import Path

from backend_python.ai_service import ProvedorMock
from backend_python.avaliacao import CasoAvaliacao, avaliar_caso
from backend_python.schemas import InputGeracaoSchema

CASOS = Path(__file__).resolve().parents[2] / "avaliacao" / "casos.json"


def mesa():
    return asyncio.run(ProvedorMock().gerar(InputGeracaoSchema(prompt_usuario="mesa")))


def test_casos_do_repositorio_sao_validos():
    casos = [CasoAvaliacao(**c) for c in json.loads(CASOS.read_text(encoding="utf-8"))]
    assert len(casos) == 20
    assert len({c.id for c in casos}) == 20


def test_nota_maxima_quando_tudo_confere():
    caso = CasoAvaliacao(id="mesa", prompt_usuario="mesa", pecas_min=3, pecas_max=3, pecas_esperadas=[["tampo"], ["pe"]])
    resultado = avaliar_caso(caso, mesa())
    assert resultado["nota"] == 1.0
    assert resultado["pecas_faltando"] == []


def test_nota_parcial_e_acentos_ignorados():
    caso = CasoAvaliacao(
        id="estante", prompt_usuario="estante", pecas_min=7, pecas_max=12,
        pecas_esperadas=[["prateleira"], ["pé"], ["lateral"], ["topo"]],
    )
    resultado = avaliar_caso(caso, mesa())
    assert resultado["geometria_valida"] is True
    assert resultado["quantidade_ok"] is False
    # "pé" casa com "pe_esquerdo"; prateleira, lateral e topo faltam
    assert resultado["pecas_faltando"] == ["prateleira", "lateral", "topo"]
    assert resultado["nota"] == round((1 + 0 + 0.25) / 3, 3)


def test_script_de_avaliacao_roda_com_o_mock(monkeypatch, tmp_path):
    import scripts.avaliar as avaliar

    monkeypatch.setenv("SKETCHUP_AI_PROVEDOR", "mock")
    monkeypatch.setattr(avaliar, "RAIZ", tmp_path)
    media = avaliar.main(["--arquivo", str(CASOS), "--casos", "mesa_centro_dois_pes"])
    assert media == 1.0
    assert len(list((tmp_path / "avaliacao" / "resultados").iterdir())) == 1


def test_gemini_espera_e_tenta_de_novo_no_limite_de_uso(monkeypatch):
    from google.genai import errors

    import backend_python.ai_service as ai

    esperas = []

    async def dormir(segundos):
        esperas.append(segundos)

    monkeypatch.setattr(ai.asyncio, "sleep", dormir)
    resposta_ok = mesa().model_dump_json()
    chamadas = []

    class Resposta:
        text = resposta_ok

    async def gerar_conteudo(**_):
        chamadas.append(1)
        if len(chamadas) <= 2:
            raise errors.ClientError(429, {"error": {"message": "limite"}})
        return Resposta()

    provedor = ai.ProvedorGemini("chave-falsa", "modelo")
    monkeypatch.setattr(provedor._cliente.aio.models, "generate_content", gerar_conteudo)
    objeto = asyncio.run(provedor.gerar(InputGeracaoSchema(prompt_usuario="mesa")))

    assert objeto.nome_objeto == "mesa_de_centro"
    assert esperas == [15, 30]


def test_gemini_nao_insiste_em_erro_que_nao_e_de_limite(monkeypatch):
    import pytest
    from google.genai import errors

    import backend_python.ai_service as ai

    async def gerar_conteudo(**_):
        raise errors.ClientError(400, {"error": {"message": "chave inválida"}})

    provedor = ai.ProvedorGemini("chave-falsa", "modelo")
    monkeypatch.setattr(provedor._cliente.aio.models, "generate_content", gerar_conteudo)
    with pytest.raises(errors.ClientError):
        asyncio.run(provedor.gerar(InputGeracaoSchema(prompt_usuario="mesa")))
