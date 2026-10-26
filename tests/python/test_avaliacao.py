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
