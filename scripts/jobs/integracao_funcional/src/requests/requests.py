import requests
from requests.auth import HTTPBasicAuth
from src.config.config import environment

config = environment()

def getUsuarioAtivo(diretorioArquivoJson):  
  basic = HTTPBasicAuth(config['loginUsuarioAtivo'], config['senhaUsuarioAtivo'])
  try:    
    response = requests.request("GET", config['urlUsuarioAtivo'], headers=config['headersUsuarioAtivo'], auth=basic)  
    createJsonUsuarios(diretorioArquivoJson, response)
    print('Arquivo atualizado com sucesso')
  except Exception as error: print("ERRO: ", error)

def getUsuarios(diretorioArquivoJson):    
    url = "https://protheus.funcionalmais.com:9134/rest/rh/v1/employeedatacontent"    
    headers = {
      'product': 'gpea010',
      'companyid': '01',
      'branchid': '00101001'  
    }
    basic = HTTPBasicAuth('integracao.grs', 'integracao@grs123')
    try:    
        response = requests.request("GET", url, headers=headers, auth=basic)  
        createJsonUsuarios(diretorioArquivoJson, response)
        print('Arquivo atualizado com sucesso')
    except Exception as error: print("ERRO: ", error)

def createJsonUsuarios(diretorioArquivoJson, text):
    with open(diretorioArquivoJson, "w") as arquivo:
        arquivo.write(text)