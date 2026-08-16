from fastapi import FastAPI
from schemas import ObjetoGeradoSchema, Dimensoes3D, PecaGenerica, Ponto3D

app = FastAPI(title="SketchUp AI Assistant API")

@app.post("/gerar-mock", response_model=ObjetoGeradoSchema)
def gerar_modelo_mock():
    """
    Endpoint de Mocking para validar a comunicação com o SketchUp (Ruby).
    Retorna uma mesa de centro estática sem chamar a IA.
    """
    mock_resposta = ObjetoGeradoSchema(
        nome_objeto="mesa_de_centro",cd 
        dimensoes_totais=Dimensoes3D(comprimento_x=100.0, largura_y=50.0, altura_z=45.0),
        pecas=[
            PecaGenerica(
                nome_peca="tampo_superior",
                dimensoes=Dimensoes3D(comprimento_x=100.0, largura_y=50.0, altura_z=5.0),
                posicao_relativa=Ponto3D(x=0.0, y=0.0, z=40.0)
            ),
            PecaGenerica(
                nome_peca="pe_esquerdo",
                dimensoes=Dimensoes3D(comprimento_x=5.0, largura_y=50.0, altura_z=40.0),
                posicao_relativa=Ponto3D(x=5.0, y=0.0, z=0.0)
            ),
            PecaGenerica(
                nome_peca="pe_direito",
                dimensoes=Dimensoes3D(comprimento_x=5.0, largura_y=50.0, altura_z=40.0),
                posicao_relativa=Ponto3D(x=90.0, y=0.0, z=0.0)
            )
        ]
    )
    
    return mock_resposta