from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# Versão do contrato compartilhado entre o backend Python e o plugin Ruby.
# Qualquer mudança incompatível no formato exige uma nova versão.
VERSAO_CONTRATO = "1.0"


# 1. Define os blocos construtivos universais
class Ponto3D(BaseModel):
    x: float = Field(..., description="Coordenada X no espaço")
    y: float = Field(..., description="Coordenada Y no espaço")
    z: float = Field(..., description="Coordenada Z no espaço (altura)")

class Dimensoes3D(BaseModel):
    comprimento_x: float = Field(..., gt=0, description="Dimensão no eixo X")
    largura_y: float = Field(..., gt=0, description="Dimensão no eixo Y")
    altura_z: float = Field(..., gt=0, description="Dimensão no eixo Z")


# 2. O Componente Genérico (Pode ser o encosto de uma cadeira ou a prateleira de um armário)
class PecaGenerica(BaseModel):
    nome_peca: str = Field(..., description="Nome descritivo da peça. Ex: 'assento', 'prateleira_01', 'pe_direito'")
    dimensoes: Dimensoes3D
    posicao_relativa: Ponto3D = Field(..., description="Ponto de origem (0,0,0) desta peça em relação ao objeto principal")

# 3. O Contrato Principal (A Raiz)
class ObjetoGeradoSchema(BaseModel):
    versao_contrato: str = Field(VERSAO_CONTRATO, description="Versão do contrato JSON")
    unidade: Literal["cm"] = Field("cm", description="Unidade de todas as medidas")
    nome_objeto: str = Field(..., description="Nome geral do objeto. Ex: 'cadeira_gamer', 'estante_livros'")
    dimensoes_totais: Dimensoes3D
    # lista dinâmica
    pecas: List[PecaGenerica] = Field(..., min_length=1, description="Lista de todas as peças volumétricas que formam o objeto")


# 4. A entrada enviada pelo arquiteto (pelo app ou pelo plugin)
class ImagemReferencia(BaseModel):
    mime_type: str = Field("image/jpeg", pattern=r"^image/(jpeg|png|webp)$")
    dados_base64: str = Field(..., min_length=1, description="A imagem codificada em Base64")

class InputGeracaoSchema(BaseModel):
    prompt_usuario: str = Field(..., min_length=3, description="O texto descrevendo o que deve ser gerado. Ex: 'Mesa rústica de madeira'")
    imagens: List[ImagemReferencia] = Field(default_factory=list, max_length=4, description="Imagens de referência enviadas pelo arquiteto")
    dimensoes_limite: Optional[Dimensoes3D] = Field(None, description="Caixa máxima, em cm, que o objeto pode ocupar")
    objeto_base: Optional[ObjetoGeradoSchema] = Field(None, description="Modelo anterior a ser refinado; o prompt descreve o ajuste")


# 5. O que a janela do app envia ao SketchUp depois que o arquiteto aprova a prévia
class EnvioSketchupSchema(BaseModel):
    objeto: ObjetoGeradoSchema
    entrada: Optional[InputGeracaoSchema] = Field(None, description="O pedido que gerou o objeto, guardado no dataset de modelos aprovados")
