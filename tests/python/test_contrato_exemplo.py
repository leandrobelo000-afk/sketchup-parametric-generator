import json
from pathlib import Path

from backend_python.schemas import ObjetoGeradoSchema

EXEMPLO = Path(__file__).resolve().parents[1] / "exemplos" / "mesa_de_centro.json"


def test_exemplo_compartilhado_segue_o_contrato():
    # O mesmo arquivo é lido pelos testes Ruby: se o contrato mudar, os dois lados quebram juntos
    ObjetoGeradoSchema.model_validate(json.loads(EXEMPLO.read_text()))
