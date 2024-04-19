import json

def environment():
    with open('scripts\jobs\integracao_funcional\src\config\config.json', "r", encoding="utf8") as arquivo:
        return json.loads(arquivo.read())        