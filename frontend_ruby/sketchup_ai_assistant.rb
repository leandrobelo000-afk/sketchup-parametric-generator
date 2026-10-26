# Arquivo raiz da extensão: só registra a extensão no SketchUp, como exige a Extension Warehouse.
require 'sketchup.rb'
require 'extensions.rb'

module LeandroBelo
  module SketchupAIAssistant
    VERSAO = '0.1.0'.freeze

    unless file_loaded?(__FILE__)
      extensao = SketchupExtension.new('SketchUp AI Assistant', 'sketchup_ai_assistant/main')
      extensao.description = 'Gera mobiliário 3D a partir de prompt e imagens de referência, com IA.'
      extensao.version = VERSAO
      extensao.creator = 'Leandro Belo'
      Sketchup.register_extension(extensao, true)
      file_loaded(__FILE__)
    end
  end
end
