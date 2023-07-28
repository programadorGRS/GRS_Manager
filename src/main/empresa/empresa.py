from datetime import datetime

import jwt
import pandas as pd
from flask import current_app
from flask_sqlalchemy import BaseQuery
from sqlalchemy import text

from src import TIMEZONE_SAO_PAULO, database
from src.exporta_dados import ExportaDadosWS
from src.utils import get_json_configs

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..grupo.grupo import grupo_empresa
from ..job.infos_carregar import InfosCarregar


class Empresa(database.Model):
    __tablename__ = 'Empresa'
    id_empresa = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod_empresa = database.Column(database.Integer, nullable=False)
    nome_abrev = database.Column(database.String(255))
    razao_social_inicial = database.Column(database.String(255))
    razao_social = database.Column(database.String(255), nullable=False)
    ativo = database.Column(database.Boolean, nullable=False, default=True)
    emails = database.Column(database.String(500))
    cnpj = database.Column(database.String(100))
    uf = database.Column(database.String(5))
    subgrupo = database.Column(database.String(50))
    logo = database.Column(database.String(100), server_default='grs.png')  # filename only (with extension)

    # RTC
    modelo_rtc = database.Column(database.String(100), server_default="rtc_default.html")  # filename only (with extension)

    pedidos = database.relationship('Pedido', backref='empresa', lazy=True) # one to many
    pedidos_proc = database.relationship('PedidoProcessamento', backref='empresa', lazy=True) # one to many
    grupo = database.relationship('Grupo', secondary=grupo_empresa, backref='empresas', lazy=True) # many to many
    unidades = database.relationship('Unidade', backref='empresa', lazy=True) # one to many
    jobs = database.relationship('Job', backref='empresa', lazy=True) # one to many

    # convocacao de exames
    conv_exames = database.Column(database.Boolean, default=True, server_default=text('1'))
    conv_exames_emails = database.Column(database.String(500))
    conv_exames_corpo_email = database.Column(database.Integer, default=1, server_default=text('1'))

    conv_exames_convocar_clinico = database.Column(database.Boolean, default=False, server_default=text('0'))
    conv_exames_nunca_realizados = database.Column(database.Boolean, default=False, server_default=text('0'))
    conv_exames_per_nunca_realizados = database.Column(database.Boolean, default=False, server_default=text('0'))
    conv_exames_pendentes = database.Column(database.Boolean, default=False, server_default=text('0'))
    conv_exames_pendentes_pcmso = database.Column(database.Boolean, default=False, server_default=text('0'))
    conv_exames_selecao = database.Column(database.Integer, default=1, server_default=text('1'))

    # exames realizados
    exames_realizados = database.Column(database.Boolean, default=True, server_default=text('1'))
    exames_realizados_emails = database.Column(database.String(500))

    # absenteismo
    absenteismo = database.Column(database.Boolean, default=True, server_default=text('1'))
    absenteismo_emails = database.Column(database.String(500))

    # mandatos cipa
    hist_mandt_cipa = database.Column(database.Boolean, server_default=text('0'), nullable=False)
    erros_mandt_cipa = database.Column(database.Boolean, server_default=text('0'), nullable=False)
    mandatos_cipa_emails = database.Column(database.String(500))

    # central de avisos
    dominios_email = database.Column(database.String(100))
    central_avisos_token = database.Column(database.String(255))

    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    last_server_update = database.Column(database.DateTime)

    def __repr__(self) -> str:
        return f'<{self.id_empresa}> {self.razao_social}'

    @classmethod
    def buscar_empresas(
        self,
        cod_empresa_principal: int | None = None,
        id_empresa: int = None,
        cod_empresa: int = None,
        nome_empresa: str = None,
        empresa_ativa: int = None,
    ) -> BaseQuery:
        params = []

        if cod_empresa_principal:
            params.append((self.cod_empresa_principal == cod_empresa_principal))
        if id_empresa:
            params.append(self.id_empresa == id_empresa)
        if cod_empresa:
            params.append(self.cod_empresa == cod_empresa)
        if nome_empresa:
            params.append(self.razao_social.like(f'%{nome_empresa}%'))
        if empresa_ativa in (0, 1):
            params.append(self.ativo == empresa_ativa)

        query = (
            database.session.query(self)
            .filter(*params)
            .order_by(self.razao_social)
        )
        return query

    @classmethod
    def carregar_empresas(self, cod_empresa_principal: int) -> InfosCarregar:
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(cod_empresa_principal)
        CREDENCIAIS = get_json_configs(EMPRESA_PRINCIPAL.configs_exporta_dados)

        PARAMETRO = ExportaDadosWS.empresas(
            empresa_principal=EMPRESA_PRINCIPAL.cod,
            cod_exporta_dados=CREDENCIAIS.get('EMPRESAS_COD'),
            chave=CREDENCIAIS.get('EMPRESAS_KEY')
        )

        resp = ExportaDadosWS.request_exporta_dados_ws(parametro=PARAMETRO)

        infos = InfosCarregar(
            tabela=self.__tablename__,
            cod_empresa_principal=cod_empresa_principal
        )

        if resp.get('response').status_code != 200:
            infos.ok = False
            infos.erro = 'Erro no request'
            return infos

        if resp.get('erro_soc'):
            infos.ok = False
            infos.erro = f'Erro SOC {resp.get("msg_erro")}'
            return infos
        
        df = ExportaDadosWS.xml_to_dataframe(xml_string=resp.get('response').text)

        if df.empty:
            infos.ok = False
            infos.erro = 'df vazio'
            return infos
        
        df = self.__tratar_df_exporta_dados(
            df=df,
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod
        )
        

        # NOTE: passar cópia para que o df original não seja modificado
        infos.qtd_inseridos = self.__inserir_empresas(df=df.copy())

        infos.qtd_atualizados = self.__atualizar_empresas(df=df.copy())

        return infos

    @classmethod
    def __tratar_df_exporta_dados(
        self,
        df: pd.DataFrame,
        cod_empresa_principal: int
    ):
        COLS = {
            'CODIGO': 'cod_empresa',
            'RAZAOSOCIAL': 'razao_social',
            'ATIVO': 'ativo',
            'CNPJ': 'cnpj',
            'UF': 'uf'
        }

        df = df[list(COLS.keys())]
        df = df.replace({'': None})
        df.rename(columns=COLS, inplace=True)

        for col in ['cod_empresa', 'ativo']:
            df[col] = df[col].astype(int)
        
        df['cod_empresa_principal'] = cod_empresa_principal

        df = self.__buscar_id_empresas(df=df, cod_empresa_principal=cod_empresa_principal)

        return df
    
    @classmethod
    def __buscar_id_empresas(self, df: pd.DataFrame, cod_empresa_principal: int):
        query = (
            database.session.query(
                self.id_empresa,
                self.cod_empresa
            )
            .filter(self.cod_empresa_principal == cod_empresa_principal)
        )
        df_db = pd.read_sql(query.statement, database.session.bind)

        df = df.merge(
            right=df_db,
            how='left',
            on='cod_empresa'
        )
        return df
    
    @classmethod
    def __inserir_empresas(self, df: pd.DataFrame):
        df = df[df['id_empresa'].isna()].copy()

        if df.empty:
            return 0
        
        df.drop(columns='id_empresa', inplace=True)
        df['data_inclusao'] = datetime.now(tz=TIMEZONE_SAO_PAULO)
        df['incluido_por'] = 'Servidor'

        qtd = df.to_sql(
            name=self.__tablename__,
            con=database.session.bind,
            index=False,
            if_exists='append'
        )
        database.session.commit()

        return qtd
    
    @classmethod
    def __atualizar_empresas(self, df: pd.DataFrame):
        df = df[df['id_empresa'].notna()].copy()

        if df.empty:
            return 0
        
        df['last_server_update'] = datetime.now(TIMEZONE_SAO_PAULO)

        df = df[[
            'id_empresa',
            'razao_social',
            'ativo',
            'cnpj',
            'uf',
            'last_server_update'
        ]]

        df_mappings = df.to_dict(orient='records')

        database.session.bulk_update_mappings(self, df_mappings)
        database.session.commit()

        return len(df_mappings)

    @staticmethod
    def generate_token_central_avisos(id_empresas: list[int]):
        token = jwt.encode(
            payload={"empresas": id_empresas},
            key=current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        return token
