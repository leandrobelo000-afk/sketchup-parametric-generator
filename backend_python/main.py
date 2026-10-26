import asyncio
import secrets
import time
from collections import deque
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .ai_service import ErroGeracao, ProvedorIA, ProvedorMock, criar_provedor
from .dataset import registrar_aprovado
from .schemas import VERSAO_CONTRATO, EnvioSketchupSchema, InputGeracaoSchema, ObjetoGeradoSchema

# Tempo sem consultas à fila após o qual consideramos o SketchUp desconectado, em segundos
SKETCHUP_TIMEOUT = 5.0


def create_app(
    token: Optional[str] = None,
    provedor: Optional[ProvedorIA] = None,
    ui_dir: Optional[Path] = None,
    dataset_dir: Optional[Path] = None,
) -> FastAPI:
    """
    Monta a API. O app desktop chama esta função com um token aleatório;
    só quem conhece o token (a janela do app e o plugin) acessa as rotas /v1.
    Com dataset_dir, cada modelo aprovado na janela do app é guardado nessa pasta.
    """
    app = FastAPI(title="SketchUp AI Assistant API", version=VERSAO_CONTRATO)
    app.state.provedor = provedor or criar_provedor()
    app.state.mock = ProvedorMock()
    # Mensagens à espera de serem desenhadas pelo plugin, na ordem de chegada
    app.state.fila = deque()
    app.state.ultima_consulta_sketchup = 0.0
    app.state.tarefas = set()

    @app.middleware("http")
    async def exigir_token(request: Request, call_next):
        if token and request.url.path.startswith("/v1/"):
            if not secrets.compare_digest(request.headers.get("X-Token", ""), token):
                return JSONResponse(status_code=401, content={"detail": "Token inválido"})
        return await call_next(request)

    @app.get("/saude")
    def saude():
        return {
            "status": "ok",
            "versao_contrato": VERSAO_CONTRATO,
            "provedor": app.state.provedor.nome,
            "sketchup_conectado": time.monotonic() - app.state.ultima_consulta_sketchup < SKETCHUP_TIMEOUT,
        }

    @app.post("/v1/gerar-mock", response_model=ObjetoGeradoSchema)
    async def gerar_modelo_mock(entrada: Optional[InputGeracaoSchema] = None):
        """
        Endpoint de Mocking para validar a comunicação com o SketchUp (Ruby).
        Retorna uma mesa de centro sem chamar a IA.
        """
        return await app.state.mock.gerar(entrada or InputGeracaoSchema(prompt_usuario="mesa de centro"))

    async def gerar(entrada: InputGeracaoSchema) -> ObjetoGeradoSchema:
        try:
            return await app.state.provedor.gerar(entrada)
        except ErroGeracao as erro:
            raise HTTPException(status_code=422, detail=f"A IA devolveu uma geometria inválida: {erro}")

    @app.post("/v1/gerar", response_model=ObjetoGeradoSchema)
    async def gerar_modelo(entrada: InputGeracaoSchema):
        """Gera o modelo e devolve na hora. Usado pela janela do app para mostrar a prévia."""
        return await gerar(entrada)

    @app.post("/v1/tarefas", status_code=202)
    async def criar_tarefa(entrada: InputGeracaoSchema):
        """
        Gera o modelo em segundo plano e coloca o resultado na fila do SketchUp.
        Usado pelo plugin, para que o SketchUp não fique travado esperando a IA.
        """
        async def executar():
            try:
                objeto = await gerar(entrada)
                app.state.fila.append({"tipo": "objeto", "objeto": objeto.model_dump()})
            except HTTPException as erro:
                app.state.fila.append({"tipo": "erro", "mensagem": erro.detail})
            except Exception as erro:  # a falha precisa chegar ao arquiteto, não sumir no log
                app.state.fila.append({"tipo": "erro", "mensagem": f"Falha na geração: {erro}"})

        tarefa = asyncio.create_task(executar())
        app.state.tarefas.add(tarefa)
        tarefa.add_done_callback(app.state.tarefas.discard)
        return {"status": "em_andamento"}

    @app.post("/v1/fila", status_code=202)
    def enviar_ao_sketchup(envio: EnvioSketchupSchema):
        """A janela do app aprovou a prévia: o plugin vai desenhá-la na próxima consulta."""
        app.state.fila.append({"tipo": "objeto", "objeto": envio.objeto.model_dump()})
        if dataset_dir:
            registrar_aprovado(dataset_dir, envio.objeto, envio.entrada)
        return {"status": "na_fila", "posicao": len(app.state.fila)}

    @app.get("/v1/fila/proximo")
    def proximo_da_fila():
        """Consultado pelo plugin a cada poucos segundos; 204 quando não há nada para desenhar."""
        app.state.ultima_consulta_sketchup = time.monotonic()
        if not app.state.fila:
            return Response(status_code=204)
        return app.state.fila.popleft()

    if ui_dir:
        app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")

    return app

