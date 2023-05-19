import json
from datetime import datetime, timedelta
from typing import Literal

from zeep.client import Client, Factory
from zeep.plugins import Plugin
from zeep.settings import Settings
from zeep.wsse.username import UsernameToken
from zeep.wsse.utils import WSU


class SOCWebService():
    CONFIGS: dict[str, any]
    WS_KEYS: dict[str, any]
    EXPORTA_DADOS_KEYS: dict[str, any]
    HOMOLOGACAO: Literal[0, 1]
    ENCODING: str

    def __init__(
            self,
            ws_keys_file: str = 'grs.json',
            exporta_dados_keys_file: str = 'grs.json',
            homologacao: Literal[0, 1] = 0,
            encoding: str = 'UTF-8'
        ):
        """
            Classe para integração com os Web Services do SOC

            As configurações são definidas na tela 337 - Empresa/Cliente do SOC no link Configuração de Integração.

            Args:
                ws_keys_file (str, optional): nome do arquivo com credenciais para o Web Service. Defaults to 'grs.json'.

                exporta_dados_keys_file (str, optional): nome do arquivo com as credenciais dos Exporta Dados. Defaults to 'grs.json'.

                homologacao (Literal[0, 1], optional): Indica a Empresa usada no Webservice é de homologação. \
                É usado na tag identificacaoUsuarioWsVo. Defaults to 0.
        """
        self.ENCODING = encoding
        self.HOMOLOGACAO = homologacao
        
        self.CONFIGS: dict = self.read_json(path='configs/soc/web_service.json')
        self.WS_KEYS: dict = self.read_json(path=f'keys/soc/web_service/{ws_keys_file}')
        self.EXPORTA_DADOS_KEYS: dict = self.read_json(path=f'keys/soc/exporta_dados/{exporta_dados_keys_file}')

    def get_client(
            self,
            wsdl_url: str,
            create_username_token: bool = True,
            raw_response: bool = False,
            plugins: list[Plugin] | None = None
        ) -> Client:
        """Cria client para o WSDL especificado

        Args:
            raw_response (bool, optional): Tipo de retorno ao chamar o servico. Defaults to False.
            - True: resquests.Response
            - False: zeep.object (dict)

            plugins (list[Plugin] | None, optional): Lista de instancias de zeep plugins. Defaults to None.
        """
        conf = Settings(raw_response=raw_response)

        client = Client(wsdl=wsdl_url, settings=conf)

        if create_username_token:
            client.wsse = self.__generate_username_token()

        if plugins:
            client.plugins = plugins

        return client

    def generate_identificacaoUsuarioWsVo(self, factory: Factory):
        '''
            Cria a tag padrão do SOC de identificação do Usuário do WebService

            Nome da tag no XML deve ser: identificacaoWsVo
            Tipo da tag: identificacaoUsuarioWsVo (é uma extensão da tag original identificacaoWsVo)

            Vide Manual/WSDL para encontrar local correto da tag em cada API

            Propriedades:
            - chaveAcesso: chave de acesso da Empresa para o webservice
            - codigoEmpresaPrincipal: cod da Empresa Principal da base no SOC
            - codigoResponsavel: responsável pela empresa no SOC
            - codigoUsuario: usuário que está usando o Web Service (encontrado em Usuários Web Service na tela 337,\
                o primeiro caractere "U" deve ser desconsiderado)
            - homologacao: indica se a empresa acessada no momento é de homologação.

            Essas propriedades são definidas na tela 337 - Empresa/Cliente do SOC no link Configuração de Integração.
        '''
        identificacao = factory.identificacaoUsuarioWsVo(
            chaveAcesso=self.WS_KEYS.get('PASSWORD'),
            codigoEmpresaPrincipal=self.WS_KEYS.get('COD_EMP_PRINCIPAL'),
            codigoResponsavel=self.WS_KEYS.get('COD_RESP'),
            codigoUsuario=self.WS_KEYS.get('USER'),
            homologacao=str(self.HOMOLOGACAO)
        )
        return identificacao

    def __generate_username_token(self, add_timestamp_token: bool = True) -> UsernameToken:
        '''
            Gera Header UsernameToken de acordo com WSSE.

            Cria Nonce e PasswordDigest automaticamente por padrão.
        '''
        # NOTE: use_digest=True, cria nonce e digest sozinho, \
        # vide metodos da classe UsernameToken
        username_token = UsernameToken(
            username=self.WS_KEYS.get('USERNAME'),
            password=self.WS_KEYS.get('PASSWORD'),
            use_digest=True
        )

        if add_timestamp_token:
            username_token.timestamp_token = self.__generate_timestamp_token()

        return username_token

    def __generate_timestamp_token(self):
        '''
            Gera Timestamp Token em UTC-0 de acordo com WSSE.
        '''
        timestamp_token = WSU.Timestamp()
        today_datetime = datetime.utcnow()
        expires_datetime = today_datetime + timedelta(minutes=10)
        timestamp_elements = [
            WSU.Created(today_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")),
            WSU.Expires(expires_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"))
        ]
        timestamp_token.extend(timestamp_elements)
        return timestamp_token

    def read_json(self, path: str) -> dict:
        with open(path, mode='r', encoding=self.ENCODING) as f:
            return dict(json.loads(f.read()))

