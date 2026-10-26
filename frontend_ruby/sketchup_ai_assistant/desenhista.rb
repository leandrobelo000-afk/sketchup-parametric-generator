module LeandroBelo
  module SketchupAIAssistant
    # Converte o objeto do contrato em geometria do SketchUp.
    module Desenhista
      # Cria um grupo com o nome do objeto e uma instância de componente por peça.
      # Peças com as mesmas dimensões compartilham o componente (ex.: os pés de uma mesa).
      def self.desenhar(dados, modelo = Sketchup.active_model)
        pecas = Contrato.pecas(dados)

        modelo.start_operation('Gerar objeto IA', true)
        begin
          grupo_pai = modelo.active_entities.add_group
          grupo_pai.name = dados['nome_objeto'].to_s
          definicoes = {}

          pecas.each do |peca|
            definicao = (definicoes[peca.dimensoes] ||= criar_definicao(modelo, peca))
            posicao = Geom::Transformation.translation(peca.posicao.map(&:cm))
            instancia = grupo_pai.entities.add_instance(definicao, posicao)
            instancia.name = peca.nome
          end

          modelo.commit_operation
        rescue StandardError
          modelo.abort_operation
          raise
        end

        modelo.selection.clear
        modelo.selection.add(grupo_pai)
        grupo_pai
      end

      def self.criar_definicao(modelo, peca)
        x, y, z = peca.dimensoes.map(&:cm)
        definicao = modelo.definitions.add(peca.nome)
        face = definicao.entities.add_face([0, 0, 0], [x, 0, 0], [x, y, 0], [0, y, 0])
        # Uma face desenhada no chão costuma nascer virada para baixo; sem isto a peça extrudaria para baixo
        face.reverse! if face.normal.z < 0
        face.pushpull(z)
        definicao
      end
    end
  end
end
