import json
from datetime import datetime, timedelta
from typing import Literal

from zeep.client import Client, Factory
from zeep.plugins import Plugin
from zeep.settings import Settings
from zeep.wsse.username import UsernameToken
from zeep.wsse.utils import WSU


class SOCWebService:
    WSDL: dict[str, any]
    WS_KEYS: dict[str, any] | None
    HOMOLOGACAO: Literal[0, 1]
    ENCODING: str

    client: Client | None
    factory: Factory | None

    def __init__(
            self,
            wsdl_filename: str,
            client_raw_response: bool = False,
            xml_huge_tree: bool = True,
            client_plugins: list[Plugin] | None = None,
            homologacao: Literal[0, 1] = 0,
            encoding: str = 'UTF-8',
            **kwargs
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

        self.WSDL = f'configs/soc/wsdl/{wsdl_filename}'

        self.client_raw_response = client_raw_response
        self.xml_huge_tree = xml_huge_tree
        self.client_plugins = client_plugins

        self.__init_client()
        self.__init_factory()

    def set_webservice_keys(self, filename: str):
        '''
        Seta WS_KEYS

        Args:
            filename (str): nome do arquivo. O arquivo deve estar na pasta keys/soc/web_service/
        '''
        self.WS_KEYS = self.read_json(path=f'keys/soc/web_service/{filename}')
        return None

    def __init_client(self):
        conf = Settings(
            raw_response=self.client_raw_response,
            xml_huge_tree=self.xml_huge_tree
        )

        self.client = Client(wsdl=self.WSDL, settings=conf)

        if self.client_plugins:
            self.client.plugins = self.client_plugins

        return None

    def __init_factory(self):
        self.factory = self.client.type_factory("ns0")
        return None

    def generate_username_token(self, add_timestamp_token: bool = True) -> UsernameToken:
        '''
            Gera Header UsernameToken para o client atual de acordo com WSSE.

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

        self.client.wsse = username_token

        return None

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

    def generate_identificacaoUsuarioWsVo(self):
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

        if not hasattr(self, "factory"):
            raise AttributeError("Inicialize factory neste objeto antes usar os metodos")

        identificacao = self.factory.identificacaoUsuarioWsVo(
            chaveAcesso=self.WS_KEYS.get('PASSWORD'),
            codigoEmpresaPrincipal=self.WS_KEYS.get('COD_EMP_PRINCIPAL'),
            codigoResponsavel=self.WS_KEYS.get('COD_RESP'),
            codigoUsuario=self.WS_KEYS.get('USER'),
            homologacao=str(self.HOMOLOGACAO)
        )
        return identificacao

