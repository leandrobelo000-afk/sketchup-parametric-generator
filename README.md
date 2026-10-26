# SketchUp AI Assistant 🚀

Um plugin inovador que integra a modelagem 3D do SketchUp com Inteligência Artificial Generativa. O arquiteto descreve o móvel, anexa imagens de referência e o modelo aparece no SketchUp, organizado em grupos e componentes editáveis.

## 🏗️ Arquitetura do Projeto

O sistema tem três partes, e a IA nunca gera código Ruby: ela devolve um JSON validado (o contrato), que o plugin transforma em geometria.

*   **App desktop (`desktop_app/`):** janela própria feita com pywebview, onde o arquiteto escreve o prompt, envia imagens e vê a prévia. Roda o backend no mesmo processo.
*   **Backend (`backend_python/`, Python/FastAPI):** processa os pedidos, chama o modelo de IA e valida a geometria. Escuta só em `127.0.0.1`, protegido por um token gerado a cada execução.
*   **Extensão SketchUp (`frontend_ruby/`, Ruby):** conecta ao app, recebe os modelos e os desenha. Segue as regras da Extension Warehouse: só Ruby legível, sem binários.

O app grava a porta e o token em `~/.sketchup_ai_assistant/conexao.json`; é ali que a extensão os encontra. A extensão consulta a fila do app a cada 2 segundos, então o SketchUp nunca fica travado esperando a IA.

### Contrato de dados (v1.0)

`ObjetoGeradoSchema` em `backend_python/schemas.py`: `versao_contrato`, `unidade` (sempre cm), `nome_objeto`, `dimensoes_totais` e a lista de `pecas`, cada uma com `dimensoes` e `posicao_relativa`. O exemplo em `tests/exemplos/mesa_de_centro.json` é validado pelos testes Python e Ruby.

### Rotas do backend

| Rota | Uso |
| --- | --- |
| `GET /saude` | Status, provedor de IA e se o SketchUp está conectado (sem token) |
| `POST /v1/gerar` | Gera e devolve o modelo (prévia na janela do app) |
| `POST /v1/gerar-mock` | Mesa de centro de teste, sem IA |
| `POST /v1/tarefas` | Gera em segundo plano e põe o resultado na fila (usado pela extensão) |
| `POST /v1/fila` | Envia um modelo aprovado ao SketchUp |
| `GET /v1/fila/proximo` | Próximo modelo a desenhar (204 quando vazio) |

As rotas `/v1` exigem o cabeçalho `X-Token`.

## 🛤️ Roadmap e Status do Projeto

Decisões: foco em **mobiliário**, v1 com um **modelo de IA de mercado** (Gemini) e, na versão comercial, **assinatura paga**, com a chave da IA guardada num servidor nosso.

### ✅ Fase 1: Fundação e Mocking
- [x] Contrato de dados versionado (`ObjetoGeradoSchema` v1.0) com unidade explícita
- [x] Endpoint de mock e cliente HTTP em Ruby

### ✅ Fase 2: Protótipo do app e do motor geométrico
- [x] App desktop pywebview + FastAPI, com prévia em vista frontal e superior
- [x] Extensão SketchUp instalável (`.rbz`), com menu e conexão ao app
- [x] Desenho com `Geom::Transformation`, uma operação desfazível por modelo e componentes compartilhados para peças iguais
- [x] Validação geométrica (peças dentro da caixa, apoiadas no chão) com nova tentativa da IA
- [x] Testes Python e Ruby, incluindo um teste de ponta a ponta app ↔ cliente Ruby

### ⏳ Fase 3: IA real e assinatura
- [x] Conjunto de avaliação com 20 móveis e script de pontuação (`scripts/avaliar.py`)
- [x] Dataset local dos modelos aprovados, base para o modelo próprio no futuro
- [x] Refinar a prévia com um pedido de ajuste ("deixe o tampo mais fino")
- [ ] Rodar a avaliação com o Gemini e ajustar o prompt até uma nota mínima
- [ ] Servidor na nuvem com login e assinatura, que guarda a chave da IA
- [ ] Materiais (madeira, mármore, quartzito) a partir do prompt
- [ ] Assinatura de código do executável

## 🛠️ Como Executar Localmente

### App desktop
1. Na raiz do repositório, crie e ative um ambiente virtual (`python -m venv .venv` e `.venv\Scripts\activate` ou `source .venv/bin/activate`).
2. Instale as dependências: `pip install -r backend_python/requirements-dev.txt`
3. Opcional: copie `.env.example` para `.env` e preencha `GEMINI_API_KEY` com `SKETCHUP_AI_PROVEDOR=gemini`. Sem isso, o app usa o mock.
4. Rode `python desktop_app/app.py`. A janela abre e o servidor sobe numa porta livre.

Só o backend, sem janela: `uvicorn backend_python.servidor_dev:app --reload` (documentação em `http://127.0.0.1:8000/docs`).

### Extensão no SketchUp
1. Gere o pacote: `python scripts/empacotar_rbz.py`
2. No SketchUp: Extensões › Extension Manager › Install Extension, e escolha `dist/sketchup_ai_assistant.rbz`.
3. Com o app aberto, use Extensões › SketchUp AI Assistant › Conectar ao app. Depois, "Enviar ao SketchUp" na janela do app desenha o modelo.

### Executável para distribuir
`python scripts/build_app.py` gera `dist/SketchUpAIAssistant/`. O build é feito com `--onedir` e sem UPX para reduzir falsos positivos de antivírus. Enquanto o executável não for assinado, o Windows mostra o aviso do SmartScreen na primeira execução, e cada versão pode ser enviada para análise em https://www.microsoft.com/en-us/wdsi/filesubmission.

### Avaliação da IA
`python scripts/avaliar.py` roda os 20 pedidos de `avaliacao/casos.json` no provedor configurado e dá uma nota de 0 a 100% por caso: geometria válida, quantidade de peças plausível e presença das peças esperadas (tampo, pés, gavetas…). O mock tira cerca de 48%, porque sempre devolve a mesma mesa; é a linha de base que o Gemini precisa superar. Cada execução grava um relatório em `avaliacao/resultados/`.

### Dataset de modelos aprovados
Cada "Enviar ao SketchUp" na janela do app grava o pedido e o modelo aprovado em `~/.sketchup_ai_assistant/dataset/aprovados.jsonl`, e as imagens de referência em `dataset/imagens/`. Os dados ficam só no computador do arquiteto. Para desligar, use `SKETCHUP_AI_SALVAR_DATASET=0` no `.env`.

### Testes
`pytest` e `ruby tests/ruby/test_plugin.rb`, na raiz do repositório.
