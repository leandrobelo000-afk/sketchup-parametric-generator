require 'net/http'
require 'uri'
require 'json'
require 'base64'

module ApiClient
  def self.enviar_para_ia(prompt, caminho_imagem, dimensoes)   
    
    # 1. Preparação Dinâmica dos Dados
    imagem_dados = File.binread(caminho_imagem)
    imagem_base64 = Base64.strict_encode64(imagem_dados)
    
    payload = {
      prompt_usuario: prompt,
      imagem_base64: imagem_base64,
      dimensoes_limite: dimensoes
    }
    
    # 2. Configuração de Rede
    url = URI("http://localhost:8000/gerar-mock") # Usando o mock para testes estruturais
    http = Net::HTTP.new(url.host, url.port)
    http.read_timeout = 60 

    requisicao = Net::HTTP::Post.new(url.path, { 'Content-Type' => 'application/json' })
    requisicao.body = payload.to_json

    # 3. Execução da Chamada
    puts "Enviando dados para o servidor Python... Aguarde."
    resposta = http.request(requisicao)

    # 4. Avaliação e Retorno
    if resposta.is_a?(Net::HTTPSuccess)
      return JSON.parse(resposta.body)
    else
      puts "Erro na comunicação com a API: Código #{resposta.code}"
      return nil
    end
    
  end
end