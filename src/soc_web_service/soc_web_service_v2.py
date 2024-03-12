from datetime import datetime, timedelta
from io import BytesIO
from typing import Any

from zeep.client import Client, Factory
from zeep.plugins import Plugin
from zeep.settings import Settings
from zeep.wsse.username import UsernameToken
from zeep.wsse.utils import WSU


class SOCWebServiceV2:
    WS_KEYS: dict[str, Any]

    client: Client | None
    factory: Factory | None

    def __init__(self):
        pass

    def set_ws_keys(self, keys: dict[str, Any]):
        self.WS_KEYS = keys
        return None

    def set_client(
        self,
        wsdl: str | BytesIO,
        raw_response: bool = False,
        xml_huge_tree: bool = True,
        plugins: list[Plugin] | None = None,
    ):
        conf = Settings(raw_response=raw_response, xml_huge_tree=xml_huge_tree)  # type: ignore

        client = Client(wsdl=wsdl, settings=conf)

        if plugins:
            client.plugins = plugins

        self.client = client

        return None

    def set_factory(self, namespace: str = "ns0"):
        self.attribute_required("client")
        self.factory = self.client.type_factory(namespace=namespace)  # type: ignore
        return None

    def set_client_username_token(
        self, add_timestamp_token: bool = True, use_digest: bool = True
    ):
        """
        Gera Header UsernameToken para o client atual de acordo com WSSE.

        Cria Nonce e PasswordDigest automaticamente por padrão.
        """
        self.attribute_required("WS_KEYS")
        self.attribute_required("client")

        # NOTE: use_digest=True, cria nonce e digest sozinho, \
        # vide metodos da classe UsernameToken
        username_token = UsernameToken(
            username=self.WS_KEYS.get("USERNAME"),
            password=self.WS_KEYS.get("PASSWORD"),
            use_digest=use_digest,
        )

        if add_timestamp_token:
            username_token.timestamp_token = self.__generate_timestamp_token()

        self.client.wsse = username_token  # type: ignore        
        return None

    def __generate_timestamp_token(self):
        """Gera Timestamp Token em UTC-0 de acordo com WSSE."""
        timestamp_token = WSU.Timestamp()
        today_datetime = datetime.utcnow()
        expires_datetime = today_datetime + timedelta(minutes=60)
        timestamp_elements = [
            WSU.Created(today_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")),
            WSU.Expires(expires_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")),
        ]
        timestamp_token.extend(timestamp_elements)
        
        return timestamp_token

    def generate_identificacaoUsuarioWsVo(self, homologacao: bool = False):
        """
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
        """
        self.attribute_required("WS_KEYS")
        self.attribute_required("factory")

        identificacao = self.factory.identificacaoUsuarioWsVo(  # type: ignore
            chaveAcesso=self.WS_KEYS.get("PASSWORD"),
            codigoEmpresaPrincipal=self.WS_KEYS.get("COD_EMP_PRINCIPAL"),
            codigoResponsavel=self.WS_KEYS.get("COD_RESP"),
            codigoUsuario=self.WS_KEYS.get("USER"),
            homologacao=str(int(homologacao)),
        )
        return identificacao

    def attribute_required(self, attr_name: str):
        if not getattr(self, attr_name, None):
            raise AttributeError(
                f"The attribute {attr_name} is required for this method"
            )
        return None
