import json
from json2table import convert
import pandas as pd

class Usuario():    
    def __init__(self):
        self.companyKey = ""
        self.code = ""
        self.fullName = ""
        self.departamentCode = ""
        self.hiringDate = ""
        self.demissionDate = ""
        self.birthDate = ""
        self.gender = ""
        self.street = ""
        self.streetNumber = ""
        self.complement = ""
        self.homeState = ""
        self.city = ""
        self.zipCode = ""
        self.areaCode = ""
        self.telephone = ""
        self.areaCodeMobile = ""
        self.mobileNumber = ""
        self.email = ""
        #self. = ""
        
def readJsonUsuariosAtivos(diretorioArquivoJson):
    with open(diretorioArquivoJson, "r", encoding="utf8") as arquivo:
        dados = json.load(arquivo)
        for dadosUsuario in dados['items']:
            novoUsuario = Usuario()
            novoUsuario.companyKey = dadosUsuario['companyKey']
            novoUsuario.code = dadosUsuario['code']
            novoUsuario.fullName = dadosUsuario['fullName']
            novoUsuario.departamentCode = dadosUsuario['departamentCode']
            novoUsuario.hiringDate = dadosUsuario['hiringDate']
            novoUsuario.demissionDate = dadosUsuario['demissionDate']
            novoUsuario.birthDate = dadosUsuario['birthDate']
            novoUsuario.gender = dadosUsuario['gender']
            novoUsuario.street = dadosUsuario['street']
            novoUsuario.streetNumber = dadosUsuario['streetNumber']
            novoUsuario.complement = dadosUsuario['complement']
            novoUsuario.homeState = dadosUsuario['homeState']
            novoUsuario.city = dadosUsuario['city']
            novoUsuario.zipCode = dadosUsuario['zipCode']
            novoUsuario.areaCode = dadosUsuario['areaCode']
            novoUsuario.telephone = dadosUsuario['telephone']
            novoUsuario.areaCodeMobile = dadosUsuario['areaCodeMobile']
            novoUsuario.mobileNumber = dadosUsuario['mobileNumber']
            novoUsuario.email = dadosUsuario['email']
def convertJson2DataTable(diretorioArquivoJson):
    with open(diretorioArquivoJson, "r", encoding="utf8") as arquivo:
        data = json.loads(arquivo.read())
        df = pd.json_normalize(data['items'])
        print(df)
        