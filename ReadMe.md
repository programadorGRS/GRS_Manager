## Diretorios ambiente de producao

| Descricao | Comando |
| ------ | ------ |
| Configuracao das credenciais do email | cat /GRS_Manager/configs/email.json |
| Configuracao das credenciais do Banco de Dados | cat /GRS_Manager/configs/prod.json |


## Criar ambiente de Homologacao

- Instalar o Python 3.10.12
- Abrir a pasta Script onde o python foi instalado(Padrao: AppData\Local\Programs\Python\Python310\Scripts)
- Abrir um CMD nessa pasta
- Executar o comando 
```sh
pip install -r "DIRETORIO ONDE ESTA CLONADO O ARQUIVO REQUIREMENTS DO GIT\requirements.txt"
EXEMPLO: pip install -r "C:\GitHub\GRS_Manager\requirements.txt"
```
- Executar o comando para iniciar o flask
```sh
py -m flask run
```