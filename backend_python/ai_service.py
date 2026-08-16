import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Importamos o nosso contrato para forçar a IA a segui-lo
from schemas import ObjetoGeradoSchema, InputGeracaoSchema

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Erro Crítico: GEMINI_API_KEY não encontrada no arquivo .env!")
        
        genai.configure(api_key=self.api_key)
        

        self.modelo = genai.GenerativeModel('gemini-1.5-flash')


    async def analisar_imagem_e_gerar_pecas(self, dados_entrada: InputGeracaoSchema) -> ObjetoGeradoSchema:
        """
        Envia a imagem e o prompt para o Gemini e exige o retorno estruturado.
        """

        prompt_sistema = f"""
        Você é um assistente de modelagem 3D. O usuário quer criar: {dados_entrada.prompt_usuario}.
        As dimensões limite são X:{dados_entrada.dimensoes_limite.comprimento_x}, Y:{dados_entrada.dimensoes_limite.largura_y}, Z:{dados_entrada.dimensoes_limite.altura_z}.
        Analise a imagem de referência e divida o objeto em formas geométricas simples (caixas/prismas).
        Calcule as dimensões e a posição espacial (X, Y, Z) de cada peça de forma que elas se encaixem perfeitamente.
        """


        imagem_formatada = {
            "mime_type": "image/jpeg", 
            "data": dados_entrada.imagem_base64
        }


        resposta = await self.modelo.generate_content_async(
            contents=[prompt_sistema, imagem_formatada],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ObjetoGeradoSchema,
                temperature=0.1 # Temperatura baixa para evitar alucinações matemáticas
            )
        )


        dados_json = json.loads(resposta.text)
        return ObjetoGeradoSchema(**dados_json)


ai_service = GeminiService()