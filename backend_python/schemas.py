from typing import List
from pydantic import BaseModel, Field

class InputGeracaoSchema(BaseModel):
    prompt_usuario: str = Field(..., description="O texto descrevendo o que deve ser gerado. Ex: 'Mesa rústica de madeira'")
    imagem_base64: str = Field(..., description="A imagem de referência codificada em string Base64")
    
    
# 1. Define os blocos construtivos universais
class Ponto3D(BaseModel):
    x: float = Field(..., description="Coordenada X no espaço")
    y: float = Field(..., description="Coordenada Y no espaço")
    z: float = Field(..., description="Coordenada Z no espaço (altura)")

class Dimensoes3D(BaseModel):
    comprimento_x: float = Field(..., description="Dimensão no eixo X")
    largura_y: float = Field(..., description="Dimensão no eixo Y")
    altura_z: float = Field(..., description="Dimensão no eixo Z")

# 2. O Componente Genérico (Pode ser o encosto de uma cadeira ou a prateleira de um armário)
class PecaGenerica(BaseModel):
    nome_peca: str = Field(..., description="Nome descritivo da peça. Ex: 'assento', 'prateleira_01', 'pe_direito'")
    dimensoes: Dimensoes3D
    posicao_relativa: Ponto3D = Field(..., description="Ponto de origem (0,0,0) desta peça em relação ao objeto principal")

# 3. O Contrato Principal (A Raiz)
class ObjetoGeradoSchema(BaseModel):
    nome_objeto: str = Field(..., description="Nome geral do objeto. Ex: 'cadeira_gamer', 'estante_livros'")
    dimensoes_totais: Dimensoes3D
    # lista dinâmica
    pecas: List[PecaGenerica] = Field(..., description="Lista de todas as peças volumétricas que formam o objeto")