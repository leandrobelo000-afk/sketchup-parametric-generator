import time

import pytest
from fastapi.testclient import TestClient

from backend_python.ai_service import ErroGeracao, ProvedorMock
from backend_python.main import create_app

TOKEN = "segredo"
CABECALHO = {"X-Token": TOKEN}
ENTRADA = {"prompt_usuario": "mesa de centro", "dimensoes_limite": {"comprimento_x": 120, "largura_y": 60, "altura_z": 40}}


def esperar_fila(cliente):
    # A tarefa roda em segundo plano: consulta a fila algumas vezes até o resultado chegar
    for _ in range(50):
        resposta = cliente.get("/v1/fila/proximo", headers=CABECALHO)
        if resposta.status_code == 200:
            return resposta.json()
        time.sleep(0.02)
    raise AssertionError("a tarefa não chegou à fila")


@pytest.fixture
def cliente(tmp_path):
    (tmp_path / "index.html").write_text("<h1>ui</h1>")
    return TestClient(create_app(token=TOKEN, provedor=ProvedorMock(), ui_dir=tmp_path))


def test_saude_nao_exige_token(cliente):
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    assert resposta.json()["provedor"] == "mock"
    assert resposta.json()["sketchup_conectado"] is False


def test_rotas_v1_exigem_token(cliente):
    assert cliente.post("/v1/gerar", json=ENTRADA).status_code == 401
    assert cliente.post("/v1/gerar", json=ENTRADA, headers={"X-Token": "errado"}).status_code == 401


def test_ui_servida_sem_token(cliente):
    assert cliente.get("/ui/").text == "<h1>ui</h1>"


def test_mock_sem_corpo_devolve_mesa_padrao(cliente):
    objeto = cliente.post("/v1/gerar-mock", headers=CABECALHO).json()
    assert objeto["versao_contrato"] == "1.0"
    assert objeto["unidade"] == "cm"
    assert objeto["dimensoes_totais"] == {"comprimento_x": 100.0, "largura_y": 50.0, "altura_z": 45.0}
    assert len(objeto["pecas"]) == 3


def test_gerar_respeita_dimensoes_limite(cliente):
    objeto = cliente.post("/v1/gerar", json=ENTRADA, headers=CABECALHO).json()
    assert objeto["dimensoes_totais"] == ENTRADA["dimensoes_limite"]
    tampo = objeto["pecas"][0]
    assert tampo["posicao_relativa"]["z"] + tampo["dimensoes"]["altura_z"] == 40


def test_entrada_invalida_devolve_422(cliente):
    resposta = cliente.post("/v1/gerar", json={"prompt_usuario": "x"}, headers=CABECALHO)
    assert resposta.status_code == 422


def test_fila_entrega_na_ordem_e_marca_sketchup_conectado(cliente):
    assert cliente.get("/v1/fila/proximo", headers=CABECALHO).status_code == 204
    assert cliente.get("/saude").json()["sketchup_conectado"] is True

    objeto = cliente.post("/v1/gerar", json=ENTRADA, headers=CABECALHO).json()
    objeto["nome_objeto"] = "primeiro"
    cliente.post("/v1/fila", json=objeto, headers=CABECALHO)
    objeto["nome_objeto"] = "segundo"
    cliente.post("/v1/fila", json=objeto, headers=CABECALHO)

    assert cliente.get("/v1/fila/proximo", headers=CABECALHO).json()["objeto"]["nome_objeto"] == "primeiro"
    assert cliente.get("/v1/fila/proximo", headers=CABECALHO).json()["objeto"]["nome_objeto"] == "segundo"


def test_tarefa_coloca_resultado_na_fila(cliente):
    with cliente:  # mantém o loop de eventos vivo para a tarefa em segundo plano
        assert cliente.post("/v1/tarefas", json=ENTRADA, headers=CABECALHO).status_code == 202
        mensagem = esperar_fila(cliente)
    assert mensagem["tipo"] == "objeto"
    assert mensagem["objeto"]["nome_objeto"] == "mesa_de_centro"


class ProvedorQueFalha:
    nome = "falha"

    async def gerar(self, entrada):
        raise ErroGeracao("peça fora dos limites")


def test_falha_da_ia_vira_422_e_mensagem_de_erro_na_fila():
    cliente = TestClient(create_app(token=TOKEN, provedor=ProvedorQueFalha()))
    with cliente:
        resposta = cliente.post("/v1/gerar", json=ENTRADA, headers=CABECALHO)
        assert resposta.status_code == 422
        assert "peça fora dos limites" in resposta.json()["detail"]

        cliente.post("/v1/tarefas", json=ENTRADA, headers=CABECALHO)
        mensagem = esperar_fila(cliente)
    assert mensagem["tipo"] == "erro"
    assert "peça fora dos limites" in mensagem["mensagem"]
