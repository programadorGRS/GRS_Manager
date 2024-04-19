from src.usuario.usuario import Usuario, readJsonUsuariosAtivos, convertJson2DataTable
from src.requests.requests import getUsuarioAtivo
from src.config.config import environment
import json, os
'''''
O objetivo deste programa e capturar os dados dos usuarios que estao no sistema do protheus e atulizar 
a base de dados do SOC
'''''

if __name__ == '__main__':  
  config = environment()
  readJsonUsuariosAtivos(config['diretorioArquivoUsuarioAtivoJson'])
  convertJson2DataTable(config['diretorioArquivoUsuarioAtivoJson'])