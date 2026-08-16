# SketchUp AI Assistant 🚀

Um plugin inovador que integra a modelagem 3D do SketchUp com Inteligência Artificial Generativa. Este projeto estabelece uma ponte de comunicação entre o ecossistema Ruby do SketchUp e um servidor backend moderno em Python.

## 🏗️ Arquitetura do Projeto

O projeto adota o princípio de **Separação de Responsabilidades (SRP)**, dividindo o sistema em duas camadas principais:

*   **Backend (Python/FastAPI):** Responsável por processar prompts, interagir com modelos de LLM (ex: Gemini) e devolver uma matriz de dados geométricos estruturados em JSON via uma arquitetura API-First.
*   **Frontend (Ruby/SketchUp):** Um cliente HTTP nativo que captura as intenções do usuário, comunica-se com a API e renderiza as coordenadas espaciais transformando-as em faces, grupos e componentes 3D no SketchUp.

## 🛤️ Roadmap e Status do Projeto

O desenvolvimento está dividido em fases lógicas para garantir a estabilidade do contrato de dados.

### ✅ Fase 1: Fundação e Mocking (Concluído)
- [x] Configuração do ambiente virtual Python e instalação de dependências (FastAPI, Uvicorn, Pydantic).
- [x] Criação do contrato de dados (`ObjetoGeradoSchema`) definindo dimensões totais e peças relativas (x, y, z).
- [x] Implementação do endpoint de Mocking (`/gerar-mock`) para isolar o front-end da latência da IA.
- [x] Desenvolvimento do Cliente HTTP em Ruby (`api_client.rb`) com requisições POST seguras.
- [x] Refatoração do módulo Ruby garantindo o tratamento de respostas e o *Parse* correto de String para Hash JSON.

### ⏳ Fase 2: Motor Geométrico (Em Andamento)
- [ ] Implementação da lógica de desenho iterativo no `sketchup_draw.rb`.
- [ ] Tradução das coordenadas (x, y, z) do Hash Ruby para a classe `Geom::Transformation` do SketchUp.
- [ ] Encapsulamento automático das peças geradas em Componentes/Grupos isolados.

### 🚀 Fase 3: IA e Materiais (Futuro)
- [ ] Substituição do endpoint de Mock pela integração real com a API do Google Gemini.
- [ ] Envio e decodificação de imagens de referência (Base64).
- [ ] Especificação avançada e mapeamento de materiais (ex: aplicação automatizada de texturas de madeira, mármore ou quartzito com base no prompt).
- [ ] Criação da Interface Gráfica (UI) utilizando as janelas de diálogo HTML/JS nativas do SketchUp.

## 🛠️ Como Executar Localmente

### Subindo o Servidor Python
1. Navegue até a pasta `backend_python`.
2. Ative o ambiente virtual (`venv\Scripts\activate` ou `source venv/bin/activate`).
3. Execute o comando: `uvicorn main:app --reload`
4. A documentação da API estará disponível em `http://127.0.0.1:8000/docs`.