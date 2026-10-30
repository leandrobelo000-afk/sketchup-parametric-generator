"""
Roda os casos de avaliacao/casos.json no provedor de IA configurado e dá uma nota de 0 a 100%.
Serve para comparar versões do prompt, modelos e provedores com os mesmos pedidos.

Uso, na raiz do repositório:
  python scripts/avaliar.py                       # usa SKETCHUP_AI_PROVEDOR do .env (mock por padrão)
  python scripts/avaliar.py --casos mesa_lateral  # só os casos indicados
Com o Gemini, os casos são espaçados em 6 s para caber no nível gratuito (--intervalo muda isso).
O relatório completo vai para avaliacao/resultados/.
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from dotenv import load_dotenv

from backend_python.ai_service import criar_provedor
from backend_python.avaliacao import CasoAvaliacao, avaliar_caso
from backend_python.schemas import InputGeracaoSchema


async def avaliar(casos, provedor, intervalo=0.0):
    resultados = []
    for indice, caso in enumerate(casos):
        if indice and intervalo:
            # Espaça as chamadas para caber no limite por minuto do nível gratuito
            await asyncio.sleep(intervalo)
        entrada = InputGeracaoSchema(prompt_usuario=caso.prompt_usuario, dimensoes_limite=caso.dimensoes_limite)
        try:
            resultado = avaliar_caso(caso, await provedor.gerar(entrada))
        except Exception as erro:  # uma falha da IA conta como nota zero, não interrompe a avaliação
            resultado = {"id": caso.id, "nota": 0.0, "falha": str(erro)}
        resultados.append(resultado)
        print(f"{resultado['nota'] * 100:5.0f}%  {caso.id}" + (f"  ({resultado['falha']})" if "falha" in resultado else ""))
    return resultados


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--casos", nargs="*", help="ids dos casos a rodar (padrão: todos)")
    parser.add_argument("--arquivo", type=Path, default=RAIZ / "avaliacao" / "casos.json")
    parser.add_argument("--intervalo", type=float, default=None,
                        help="segundos entre casos (padrão: 6 com o Gemini, 0 com o mock)")
    args = parser.parse_args(argv)

    load_dotenv(RAIZ / ".env")
    casos = [CasoAvaliacao(**c) for c in json.loads(args.arquivo.read_text(encoding="utf-8"))]
    if args.casos:
        casos = [c for c in casos if c.id in args.casos]

    provedor = criar_provedor()
    intervalo = args.intervalo if args.intervalo is not None else (6.0 if provedor.nome == "gemini" else 0.0)
    resultados = asyncio.run(avaliar(casos, provedor, intervalo))
    media = sum(r["nota"] for r in resultados) / len(resultados) if resultados else 0.0
    print(f"\nNota média ({provedor.nome}, {len(resultados)} casos): {media * 100:.0f}%")

    pasta = RAIZ / "avaliacao" / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    relatorio = pasta / f"{datetime.now():%Y%m%d-%H%M%S}_{provedor.nome}.json"
    relatorio.write_text(json.dumps({"provedor": provedor.nome, "media": media, "resultados": resultados}, ensure_ascii=False, indent=2))
    print(f"Relatório: {relatorio}")
    return media


if __name__ == "__main__":
    main()
