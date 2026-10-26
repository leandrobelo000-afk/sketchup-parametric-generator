module LeandroBelo
  module SketchupAIAssistant
    # Interpreta o JSON do contrato (ObjetoGeradoSchema) sem depender da API do SketchUp,
    # para poder ser testado fora dele. Todas as medidas ficam em cm.
    module Contrato
      VERSAO_SUPORTADA = '1'.freeze
      EIXOS = %w[comprimento_x largura_y altura_z].freeze

      class ErroContrato < StandardError; end

      Peca = Struct.new(:nome, :dimensoes, :posicao)

      def self.pecas(dados)
        versao = dados.fetch('versao_contrato', '1.0').to_s
        unless versao.split('.').first == VERSAO_SUPORTADA
          raise ErroContrato, "Versão do contrato #{versao} não suportada por esta versão do plugin"
        end

        lista = dados['pecas']
        raise ErroContrato, 'O objeto não tem peças' unless lista.is_a?(Array) && !lista.empty?

        lista.map { |peca| ler_peca(peca) }
      end

      def self.ler_peca(peca)
        dimensoes = EIXOS.map { |eixo| Float(peca.fetch('dimensoes').fetch(eixo)) }
        posicao = %w[x y z].map { |eixo| Float(peca.fetch('posicao_relativa').fetch(eixo)) }
        raise ErroContrato, "Peça #{peca['nome_peca']} com dimensão zero ou negativa" if dimensoes.any? { |d| d <= 0 }

        Peca.new(peca.fetch('nome_peca').to_s, dimensoes, posicao)
      rescue KeyError, TypeError, ArgumentError => erro
        raise ErroContrato, "Peça inválida no JSON: #{erro.message}"
      end
    end
  end
end
