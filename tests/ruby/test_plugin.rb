require 'minitest/autorun'
require 'tmpdir'
require 'json'
require_relative '../../frontend_ruby/sketchup_ai_assistant/conexao'
require_relative '../../frontend_ruby/sketchup_ai_assistant/contrato'
require_relative '../../frontend_ruby/sketchup_ai_assistant/api_client'

module LeandroBelo
  module SketchupAIAssistant
    class TestContrato < Minitest::Test
      def objeto
        JSON.parse(File.read(File.join(__dir__, '..', 'exemplos', 'mesa_de_centro.json')))
      end

      def test_le_as_pecas_em_cm
        pecas = Contrato.pecas(objeto)
        assert_equal 3, pecas.size
        assert_equal 'tampo_superior', pecas.first.nome
        assert_equal [100.0, 50.0, 5.0], pecas.first.dimensoes
        assert_equal [0.0, 0.0, 40.0], pecas.first.posicao
      end

      def test_recusa_versao_maior_do_contrato
        assert_raises(Contrato::ErroContrato) { Contrato.pecas(objeto.merge('versao_contrato' => '2.0')) }
      end

      def test_recusa_objeto_sem_pecas
        assert_raises(Contrato::ErroContrato) { Contrato.pecas(objeto.merge('pecas' => [])) }
      end

      def test_recusa_peca_incompleta_ou_sem_volume
        dados = objeto
        dados['pecas'][0]['dimensoes'].delete('altura_z')
        assert_raises(Contrato::ErroContrato) { Contrato.pecas(dados) }

        dados = objeto
        dados['pecas'][0]['dimensoes']['altura_z'] = 0
        assert_raises(Contrato::ErroContrato) { Contrato.pecas(dados) }
      end
    end

    class TestConexao < Minitest::Test
      def test_le_porta_e_token
        Dir.mktmpdir do |pasta|
          caminho = File.join(pasta, 'conexao.json')
          File.write(caminho, { porta: 51234, token: 'abc', pid: 1 }.to_json)
          assert_equal({ porta: 51234, token: 'abc' }, Conexao.ler(caminho))
        end
      end

      def test_app_fechado
        erro = assert_raises(Conexao::ErroConexao) { Conexao.ler('/nao/existe/conexao.json') }
        assert_match(/não está aberto/, erro.message)
      end

      def test_arquivo_corrompido
        Dir.mktmpdir do |pasta|
          caminho = File.join(pasta, 'conexao.json')
          File.write(caminho, '{porta')
          assert_raises(Conexao::ErroConexao) { Conexao.ler(caminho) }
        end
      end
    end

    class TestApiClient < Minitest::Test
      def test_payload_com_imagem
        Dir.mktmpdir do |pasta|
          imagem = File.join(pasta, 'ref.PNG')
          File.binwrite(imagem, "\x89PNG")
          payload = ApiClient.montar_payload('mesa', [imagem], { comprimento_x: 1, largura_y: 2, altura_z: 3 })
          assert_equal 'image/png', payload[:imagens].first[:mime_type]
          assert_equal "\x89PNG".b, payload[:imagens].first[:dados_base64].unpack1('m0')
        end
      end

      def test_payload_recusa_formato_desconhecido
        assert_raises(ApiClient::ErroApi) { ApiClient.montar_payload('mesa', ['planta.dwg'], {}) }
      end
    end
  end
end
