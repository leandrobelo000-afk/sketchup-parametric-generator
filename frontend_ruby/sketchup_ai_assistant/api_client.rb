require 'net/http'
require 'uri'
require 'json'
require 'base64'

module LeandroBelo
  module SketchupAIAssistant
    # Cliente HTTP do servidor local que o app desktop sobe em 127.0.0.1.
    class ApiClient
      class ErroApi < StandardError; end

      ERROS_DE_REDE = [
        Errno::ECONNREFUSED, Errno::ECONNRESET, Errno::EHOSTUNREACH,
        Net::OpenTimeout, Net::ReadTimeout, SocketError, EOFError
      ].freeze

      TIPOS_IMAGEM = { '.jpg' => 'image/jpeg', '.jpeg' => 'image/jpeg', '.png' => 'image/png', '.webp' => 'image/webp' }.freeze

      def initialize(porta:, token:, host: '127.0.0.1')
        @host = host
        @porta = porta
        @token = token
      end

      # Monta o corpo do InputGeracaoSchema a partir do que o arquiteto digitou
      def self.montar_payload(prompt, caminhos_imagens, dimensoes)
        imagens = caminhos_imagens.map do |caminho|
          tipo = TIPOS_IMAGEM[File.extname(caminho).downcase]
          raise ErroApi, "Formato de imagem não suportado: #{File.basename(caminho)}" unless tipo

          { mime_type: tipo, dados_base64: Base64.strict_encode64(File.binread(caminho)) }
        end

        { prompt_usuario: prompt, imagens: imagens, dimensoes_limite: dimensoes }
      end

      def saude
        get('/saude')
      end

      def gerar_mock(payload = nil)
        post('/v1/gerar-mock', payload, read_timeout: 10)
      end

      # A geração roda em segundo plano no app; o resultado chega por proximo_da_fila
      def criar_tarefa(payload)
        post('/v1/tarefas', payload)
      end

      # nil quando não há nada para desenhar
      def proximo_da_fila
        get('/v1/fila/proximo', read_timeout: 2)
      end

      private

      def get(caminho, read_timeout: 5)
        requisitar(Net::HTTP::Get.new(caminho), read_timeout)
      end

      def post(caminho, payload, read_timeout: 5)
        requisicao = Net::HTTP::Post.new(caminho, 'Content-Type' => 'application/json')
        requisicao.body = payload.nil? ? '' : payload.to_json
        requisitar(requisicao, read_timeout)
      end

      def requisitar(requisicao, read_timeout)
        http = Net::HTTP.new(@host, @porta)
        http.open_timeout = 1
        http.read_timeout = read_timeout
        requisicao['X-Token'] = @token

        resposta = http.request(requisicao)
        return nil if resposta.is_a?(Net::HTTPNoContent)
        return JSON.parse(resposta.body) if resposta.is_a?(Net::HTTPSuccess)

        raise ErroApi, mensagem_de_erro(resposta)
      end

      def mensagem_de_erro(resposta)
        detalhe = JSON.parse(resposta.body)['detail']
        detalhe = detalhe.map { |d| d['msg'] }.join('; ') if detalhe.is_a?(Array)
        "Erro #{resposta.code}: #{detalhe}"
      rescue JSON::ParserError
        "Erro #{resposta.code} na comunicação com o app"
      end
    end
  end
end
