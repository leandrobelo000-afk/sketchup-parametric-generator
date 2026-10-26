require 'sketchup.rb'

module LeandroBelo
  module SketchupAIAssistant
    PASTA = File.dirname(__FILE__)

    Sketchup.require(File.join(PASTA, 'conexao'))
    Sketchup.require(File.join(PASTA, 'contrato'))
    Sketchup.require(File.join(PASTA, 'api_client'))
    Sketchup.require(File.join(PASTA, 'desenhista'))

    INTERVALO_FILA = 2 # segundos entre consultas ao app

    def self.conectar
      @cliente = ApiClient.new(**Conexao.ler)
      @cliente.saude
      UI.stop_timer(@timer) if @timer
      @timer = UI.start_timer(INTERVALO_FILA, true) { consultar_fila }
      Sketchup.status_text = 'SketchUp AI Assistant: conectado ao app'
      true
    rescue Conexao::ErroConexao, ApiClient::ErroApi => erro
      @cliente = nil
      UI.messagebox("Não foi possível conectar ao app.\n\n#{erro.message}")
      false
    rescue *ApiClient::ERROS_DE_REDE
      # O arquivo de conexão pode ter sobrado de um app que foi encerrado à força
      @cliente = nil
      UI.messagebox('O app SketchUp AI Assistant não respondeu. Abra o app e tente de novo.')
      false
    end

    def self.desconectar
      UI.stop_timer(@timer) if @timer
      @timer = nil
      @cliente = nil
      Sketchup.status_text = 'SketchUp AI Assistant: desconectado'
    end

    def self.conectado?
      !@cliente.nil? || conectar
    end

    # Chamado pelo timer: desenha o que o app mandou (pela janela dele ou por uma tarefa do plugin)
    def self.consultar_fila
      return if @ocupado || @cliente.nil?

      @ocupado = true
      mensagem = @cliente.proximo_da_fila
      tratar_mensagem(mensagem) if mensagem
    rescue *ApiClient::ERROS_DE_REDE
      desconectar
      UI.messagebox('A conexão com o app SketchUp AI Assistant foi perdida. Abra o app e conecte de novo.')
    rescue Contrato::ErroContrato, ApiClient::ErroApi => erro
      UI.messagebox("Não foi possível desenhar o modelo.\n\n#{erro.message}")
    ensure
      @ocupado = false
    end

    def self.tratar_mensagem(mensagem)
      case mensagem['tipo']
      when 'objeto'
        grupo = Desenhista.desenhar(mensagem['objeto'])
        Sketchup.status_text = "SketchUp AI Assistant: #{grupo.name} desenhado"
      when 'erro'
        UI.messagebox("A geração falhou.\n\n#{mensagem['mensagem']}")
      end
    end

    def self.gerar_pelo_prompt
      return unless conectado?

      rotulos = ['Descrição', 'Comprimento X (cm)', 'Largura Y (cm)', 'Altura Z (cm)']
      respostas = UI.inputbox(rotulos, ['', 100.0, 50.0, 45.0], 'SketchUp AI Assistant')
      return unless respostas

      prompt, x, y, z = respostas
      imagens = []
      if UI.messagebox('Adicionar uma imagem de referência?', MB_YESNO) == IDYES
        caminho = UI.openpanel('Imagem de referência', '', 'Imagens|*.jpg;*.jpeg;*.png;*.webp||')
        imagens << caminho if caminho
      end

      dimensoes = { comprimento_x: x.to_f, largura_y: y.to_f, altura_z: z.to_f }
      @cliente.criar_tarefa(ApiClient.montar_payload(prompt, imagens, dimensoes))
      Sketchup.status_text = 'SketchUp AI Assistant: gerando… o modelo aparece quando a IA terminar'
    rescue ApiClient::ErroApi, *ApiClient::ERROS_DE_REDE => erro
      UI.messagebox("Não foi possível enviar o pedido.\n\n#{erro.message}")
    end

    def self.desenhar_mock
      return unless conectado?

      Desenhista.desenhar(@cliente.gerar_mock)
    rescue Contrato::ErroContrato, ApiClient::ErroApi, *ApiClient::ERROS_DE_REDE => erro
      UI.messagebox("Não foi possível desenhar a mesa de teste.\n\n#{erro.message}")
    end

    unless file_loaded?(__FILE__)
      menu = UI.menu('Extensions').add_submenu('SketchUp AI Assistant')
      menu.add_item('Conectar ao app') { conectar }
      menu.add_item('Gerar pelo prompt…') { gerar_pelo_prompt }
      menu.add_item('Desenhar mesa de teste (mock)') { desenhar_mock }
      menu.add_separator
      menu.add_item('Desconectar') { desconectar }
      file_loaded(__FILE__)
    end
  end
end
