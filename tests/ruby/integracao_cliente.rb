# Usado por tests/python/test_integracao.py com o app rodando: exercita o cliente do plugin de ponta a ponta.
require_relative '../../frontend_ruby/sketchup_ai_assistant/conexao'
require_relative '../../frontend_ruby/sketchup_ai_assistant/contrato'
require_relative '../../frontend_ruby/sketchup_ai_assistant/api_client'

include LeandroBelo::SketchupAIAssistant

def confirmar(condicao, mensagem)
  abort("FALHOU: #{mensagem}") unless condicao
end

cliente = ApiClient.new(**Conexao.ler)
confirmar(cliente.saude['status'] == 'ok', 'saúde')

mesa = cliente.gerar_mock
confirmar(Contrato.pecas(mesa).size == 3, 'mock com 3 peças')

confirmar(cliente.proximo_da_fila.nil?, 'fila começa vazia')
cliente.criar_tarefa(ApiClient.montar_payload('mesa lateral', [], { comprimento_x: 50, largura_y: 50, altura_z: 55 }))
mensagem = nil
20.times do
  mensagem = cliente.proximo_da_fila
  break if mensagem

  sleep 0.1
end
confirmar(mensagem && mensagem['tipo'] == 'objeto', 'tarefa chega pela fila')
confirmar(mensagem['objeto']['dimensoes_totais']['altura_z'] == 55.0, 'tarefa respeita os limites')

begin
  ApiClient.new(porta: Conexao.ler[:porta], token: 'errado').gerar_mock
  abort('FALHOU: token errado deveria ser recusado')
rescue ApiClient::ErroApi => erro
  confirmar(erro.message.include?('401'), 'token errado devolve 401')
end

puts 'OK'
