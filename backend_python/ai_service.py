import asyncio
import base64
import os
from typing import Optional, Protocol

from .schemas import Dimensoes3D, InputGeracaoSchema, ObjetoGeradoSchema, PecaGenerica, Ponto3D
from .validacao import validar_geometria


class ErroGeracao(Exception):
    """A IA não conseguiu devolver uma geometria válida."""


class ProvedorIA(Protocol):
    nome: str

    async def gerar(self, entrada: InputGeracaoSchema) -> ObjetoGeradoSchema: ...


class ProvedorMock:
    """
    Devolve uma mesa de centro sem chamar a IA, ajustada às dimensões limite quando informadas.
    Serve para testar o app e o plugin sem custo nem latência.
    """
    nome = "mock"

    async def gerar(self, entrada: InputGeracaoSchema) -> ObjetoGeradoSchema:
        # O mock não entende o pedido de ajuste: devolve o modelo anterior como veio
        if entrada.objeto_base:
            return entrada.objeto_base.model_copy(deep=True)

        limite = entrada.dimensoes_limite or Dimensoes3D(comprimento_x=100.0, largura_y=50.0, altura_z=45.0)
        x, y, z = limite.comprimento_x, limite.largura_y, limite.altura_z
        tampo, pe = 5.0, 5.0

        return ObjetoGeradoSchema(
            nome_objeto="mesa_de_centro",
            dimensoes_totais=Dimensoes3D(comprimento_x=x, largura_y=y, altura_z=z),
            pecas=[
                PecaGenerica(
                    nome_peca="tampo_superior",
                    dimensoes=Dimensoes3D(comprimento_x=x, largura_y=y, altura_z=tampo),
                    posicao_relativa=Ponto3D(x=0.0, y=0.0, z=z - tampo)
                ),
                PecaGenerica(
                    nome_peca="pe_esquerdo",
                    dimensoes=Dimensoes3D(comprimento_x=pe, largura_y=y, altura_z=z - tampo),
                    posicao_relativa=Ponto3D(x=pe, y=0.0, z=0.0)
                ),
                PecaGenerica(
                    nome_peca="pe_direito",
                    dimensoes=Dimensoes3D(comprimento_x=pe, largura_y=y, altura_z=z - tampo),
                    posicao_relativa=Ponto3D(x=x - 2 * pe, y=0.0, z=0.0)
                ),
            ]
        )


# Esperas, em segundos, antes de cada nova tentativa quando o Gemini recusa por limite de uso (429)
# ou por sobrecarga (503). O nível gratuito tem poucas chamadas por minuto.
ESPERAS_LIMITE = (15, 30, 60)


class ProvedorGemini:
    """
    Envia o prompt e as imagens ao Gemini e exige o retorno no formato do contrato.
    No modelo de assinatura, esta chamada passará a ser feita pelo servidor na nuvem;
    por enquanto a chave vem do ambiente do desenvolvedor (arquivo .env).
    """
    nome = "gemini"

    def __init__(self, api_key: str, modelo: str):
        # Importado aqui para o app funcionar em modo mock sem o SDK instalado
        from google import genai
        from google.genai import errors
        self._tipos = genai.types
        self._erro_api = errors.APIError
        self._cliente = genai.Client(api_key=api_key)
        self.modelo = modelo

    def _prompt(self, entrada: InputGeracaoSchema, erros_anteriores: Optional[list] = None) -> str:
        limites = ""
        if entrada.dimensoes_limite:
            d = entrada.dimensoes_limite
            limites = f"As dimensões limite são X:{d.comprimento_x}, Y:{d.largura_y}, Z:{d.altura_z} (cm)."
        texto = f"""
        Você é um assistente de modelagem 3D de mobiliário. O arquiteto quer criar: {entrada.prompt_usuario}.
        {limites}
        Analise as imagens de referência (se houver) e divida o objeto em formas geométricas simples (caixas/prismas).
        Calcule as dimensões e a posição espacial (X, Y, Z), em cm, de cada peça de forma que elas se encaixem perfeitamente.
        A origem (0,0,0) é o canto inferior do objeto; nenhuma peça pode ter coordenada negativa nem sair de dimensoes_totais.
        """
        if entrada.objeto_base:
            texto += (
                "\nEste é o modelo atual, em JSON. Aplique somente o ajuste pedido acima e mantenha o restante igual:\n"
                + entrada.objeto_base.model_dump_json()
            )
        if erros_anteriores:
            texto += "\nSua resposta anterior tinha estes problemas, corrija-os:\n- " + "\n- ".join(erros_anteriores)
        return texto

    async def _chamar(self, conteudo, configuracao):
        for espera in (*ESPERAS_LIMITE, None):
            try:
                return await self._cliente.aio.models.generate_content(
                    model=self.modelo, contents=conteudo, config=configuracao
                )
            except self._erro_api as erro:
                if erro.code not in (429, 503) or espera is None:
                    raise
                await asyncio.sleep(espera)

    async def gerar(self, entrada: InputGeracaoSchema) -> ObjetoGeradoSchema:
        imagens = [
            self._tipos.Part.from_bytes(data=base64.b64decode(img.dados_base64), mime_type=img.mime_type)
            for img in entrada.imagens
        ]
        configuracao = self._tipos.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=ObjetoGeradoSchema.model_json_schema(),
            temperature=0.1  # Temperatura baixa para evitar alucinações matemáticas
        )

        erros = None
        # Uma tentativa extra: se a geometria vier inválida, devolvemos os erros para a IA corrigir
        for _ in range(2):
            resposta = await self._chamar([*imagens, self._prompt(entrada, erros)], configuracao)
            objeto = ObjetoGeradoSchema.model_validate_json(resposta.text)
            erros = validar_geometria(objeto, entrada.dimensoes_limite)
            if not erros:
                return objeto

        raise ErroGeracao("; ".join(erros))


def criar_provedor() -> ProvedorIA:
    """Escolhe o provedor pela variável SKETCHUP_AI_PROVEDOR (mock por padrão)."""
    escolha = os.getenv("SKETCHUP_AI_PROVEDOR", "mock").lower()
    if escolha == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("SKETCHUP_AI_PROVEDOR=gemini exige GEMINI_API_KEY no arquivo .env")
        return ProvedorGemini(api_key, os.getenv("GEMINI_MODELO", "gemini-flash-latest"))
    return ProvedorMock()
