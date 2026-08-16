require 'net/http'
require 'uri'
require 'json'
require 'base64'

resposta = ApiClient.enviar_para_ia(
  "Mesa de centro moderna de madeira", 
  "C:/caminho/para/sua/imagem_de_teste.jpg",
  { comprimento_x: 100, largura_y: 50, altura_z: 40 }
)
if resposta.is_a?(Net::HTTPSuccess)
  dados_json = JSON.parse(resposta.body)
  lista_pecas = dados_json["pecas"]
  
  puts "Desenhando objeto: #{dados_json['nome_objeto']}"
  modelo_su = Sketchup.active_model
  modelo_su.start_operation('Gerar Objeto IA', true)

  entidades_raiz = modelo_su.active_entities
  grupo_pai = entidades_raiz.add_group
  grupo_pai.name = dados_json['nome_objeto']
  dados_json["pecas"].each do |peca|
    dim_x = peca["dimensoes"]["comprimento_x"].to_f.cm
    dim_y = peca["dimensoes"]["largura_y"].to_f.cm
    dim_z = peca["dimensoes"]["altura_z"].to_f.cm
    pos_x = peca["posicao_relativa"]["x"].to_f.cm
    pos_y = peca["posicao_relativa"]["y"].to_f.cm
    pos_z = peca["posicao_relativa"]["z"].to_f.cm
    grupo_peca = grupo_pai.entities.add_group
    grupo_peca.name = peca["nome_peca"]
    pt1 = [0, 0, 0]
    pt2 = [dim_x, 0, 0]
    pt3 = [dim_x, dim_y, 0]
    pt4 = [0, dim_y, 0]
  
    face_base = grupo_peca.entities.add_face(pt1, pt2, pt3, pt4)
    face_base.pushpull(-dim_z)
    vetor_movimento = [pos_x, pos_y, pos_z]
    transformacao = Geom::Transformation.translation(vetor_movimento)
    grupo_peca.transform!(transformacao)
  end

modelo_su.commit_operation
puts "Modelo gerado com sucesso e encapsulado corretamente!"

else
  puts "Erro ao gerar modelo: #{resposta.code} - #{resposta.message}"
  puts "Detalhes do erro: #{resposta.body}"
end