require 'json'

module LeandroBelo
  module SketchupAIAssistant
    # Lê a porta e o token que o app desktop grava ao iniciar.
    module Conexao
      class ErroConexao < StandardError; end

      def self.caminho_padrao
        File.join(Dir.home, '.sketchup_ai_assistant', 'conexao.json')
      end

      def self.ler(caminho = caminho_padrao)
        unless File.exist?(caminho)
          raise ErroConexao, 'O app SketchUp AI Assistant não está aberto. Abra o app e tente de novo.'
        end

        dados = JSON.parse(File.read(caminho))
        porta = dados['porta']
        token = dados['token']
        unless porta.is_a?(Integer) && token.is_a?(String) && !token.empty?
          raise ErroConexao, "Arquivo de conexão inválido: #{caminho}"
        end

        { porta: porta, token: token }
      rescue JSON::ParserError
        raise ErroConexao, "Arquivo de conexão inválido: #{caminho}"
      end
    end
  end
end
