from datetime import datetime

import pandas as pd
from flask_sqlalchemy import BaseQuery
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src import TIMEZONE_SAO_PAULO
from src.extensions import database
from src.soc_web_service.exporta_dados import ExportaDados

from ..empresa.empresa import Empresa
from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..job.infos_carregar import InfosCarregar


class Unidade(database.Model):
    __tablename__ = 'Unidade'

    id_unidade = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'), nullable=False)
    cod_unidade = database.Column(database.String(255), nullable=False)
    nome_unidade = database.Column(database.String(255), nullable=False)
    emails = database.Column(database.String(500))
    ativo = database.Column(database.Boolean, nullable=False)
    cod_rh = database.Column(database.String(255))
    uf = database.Column(database.String(10))

    # relationships
    pedidos = database.relationship('Pedido', backref='unidade', lazy=True) # one to many

    # convocacao de exames
    conv_exames = database.Column(database.Boolean, default=False)
    conv_exames_emails = database.Column(database.String(500))
    conv_exames_corpo_email = database.Column(database.Integer, default=1)

    # exames realizados
    exames_realizados = database.Column(database.Boolean, default=True)
    exames_realizados_emails = database.Column(database.String(500))

    # absenteismo
    absenteismo = database.Column(database.Boolean, default=True)
    absenteismo_emails = database.Column(database.String(500))

    # mandatos cipa
    erros_mandt_cipa = database.Column(database.Boolean, server_default=text('0'), nullable=False)
    mandatos_cipa_emails = database.Column(database.String(500))

    data_inclusao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    data_alteracao = database.Column(database.DateTime)
    alterado_por = database.Column(database.String(50))

    last_server_update = database.Column(database.DateTime)

    def __repr__(self) -> str:
        return f'<{self.id_unidade}> {self.nome_unidade}'

    COLUNAS_PLANILHA = [
        'cod_empresa_principal',
        'id_empresa',
        'cod_empresa',
        'razao_social',
        'id_unidade',
        'cod_unidade',
        'cod_rh',
        'cnpj',
        'uf',
        'nome_unidade',
        'emails',
        'ativo',
        'conv_exames',
        'conv_exames_emails',
        'conv_exames_corpo_email',
        'exames_realizados',
        'exames_realizados_emails',
        'absenteismo',
        'absenteismo_emails',
        'data_inclusao',
        'data_alteracao',
        'incluido_por',
        'alterado_por'
    ]

    @classmethod
    def buscar_unidades(
        self,
        cod_emp_princ: int | None = None,
        id_empresa: int = None,
        id_unidade: int = None,
        cod_unidade: int = None,
        nome_unidade: str = None,
        unidade_ativa: int = None
    ) -> BaseQuery:
        params = []

        if cod_emp_princ:
            params.append(self.cod_empresa_principal == cod_emp_princ)
        if id_empresa:
            params.append(self.id_empresa == id_empresa)
        if id_unidade:
            params.append(self.id_unidade == id_unidade)
        if cod_unidade:
            params.append(self.cod_unidade.like(f'%{cod_unidade}%'))
        if nome_unidade:
            params.append(self.nome_unidade.like(f'%{nome_unidade}%'))
        if unidade_ativa in (0, 1):
            params.append(self.ativo == unidade_ativa)

        query = (
            database.session.query(self)
            .filter(*params)
            .order_by(self.nome_unidade)
        )
        return query

    @classmethod
    def carregar_unidades(
        self,
        cod_emp_princ: int,
        ativo: bool | None = None
    ):
        EMPRESA_PRINCIPAL: EmpresaPrincipal = (EmpresaPrincipal.query.get(cod_emp_princ))
        KEYS = getattr(EMPRESA_PRINCIPAL, 'chaves_exporta_dados', None)

        infos = InfosCarregar(
            tabela=self.__tablename__,
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod
        )

        if not KEYS:
            infos.ok = False
            infos.add_error('Chaves Exporta Dados não encontradas')
            return infos

        ex = ExportaDados(
            wsdl_filename='prod/ExportaDadosWs.xml',
            exporta_dados_keys_filename=KEYS
        )

        PARAMETRO = ex.unidades(
            empresa=EMPRESA_PRINCIPAL.cod,
            codigo=ex.EXPORTA_DADOS_KEYS.get('UNIDADES_COD'),
            chave=ex.EXPORTA_DADOS_KEYS.get('UNIDADES_KEY'),
            ativo=ativo
        )

        body = ex.build_request_body(param=PARAMETRO)

        try:
            resp = ex.call_service(request_body=body)
        except:
            infos.ok = False
            infos.erro = 'Erro no request'
            return infos

        erro = getattr(resp, 'erro', None)
        if erro:
            infos.ok = False
            msg_erro = getattr(resp, 'mensagemErro', None)
            infos.add_error(error=f'Erro SOC: {msg_erro}')
            return infos

        retorno = getattr(resp, 'retorno', None)
        df = ex.dataframe_from_zeep(retorno=retorno)

        if df.empty:
            infos.add_error(error='df vazio')
            return infos

        df = self.__tratar_df_exporta_dados(
            df=df,
            cod_emp_princ=EMPRESA_PRINCIPAL.cod
        )

        # NOTE: remover Unidades sem Empresa na db
        df = df[df['id_empresa'].notna()]

        # NOTE: passar cópia para que o df original não seja modificado
        infos = self.__inserir_unidades(df=df.copy(), infos=infos)
        infos = self.__atualizar_unidades(df=df.copy(), infos=infos)

        return infos

    @classmethod
    def __tratar_df_exporta_dados(
        self,
        df: pd.DataFrame,
        cod_emp_princ: int
    ):
        COLS = {
            'CODIGOEMPRESA': 'cod_empresa',
            'CODIGOUNIDADE': 'cod_unidade',
            'NOMEUNIDADE': 'nome_unidade',
            'UNIDADEATIVA': 'ativo',
            'CODIGORHUNIDADE': 'cod_rh',
            'UF': 'uf'
        }

        df = df.copy()

        df = df[list(COLS.keys())]
        df = df.replace({'': None})
        df.rename(columns=COLS, inplace=True)

        for col in ['cod_empresa', 'ativo']:
            df[col] = df[col].astype(int)

        df = self.__buscar_infos_unidades(df=df, cod_emp_princ=cod_emp_princ)
        df = self.__buscar_infos_empresas(df=df, cod_emp_princ=cod_emp_princ)

        df = df.drop(columns='cod_empresa')

        df['cod_empresa_principal'] = cod_emp_princ

        return df

    @classmethod
    def __buscar_infos_unidades(
        self,
        df: pd.DataFrame,
        cod_emp_princ: int
    ):
        query = (
            database.session.query(
                self.id_unidade,
                self.cod_unidade,
                Empresa.cod_empresa
            )
            .join(Empresa, Empresa.id_empresa == self.id_empresa)
            .filter(self.cod_empresa_principal == cod_emp_princ)
        )

        df_db = pd.read_sql(query.statement, database.session.bind)

        df = df.merge(
            df_db,
            how='left',
            on=['cod_empresa', 'cod_unidade']
        )

        return df

    @classmethod
    def __buscar_infos_empresas(
        self,
        df: pd.DataFrame,
        cod_emp_princ: int
    ):
        query = (
            database.session.query(
                Empresa.id_empresa,
                Empresa.cod_empresa
            )
            .filter(Empresa.cod_empresa_principal == cod_emp_princ)
        )

        df_db = pd.read_sql(query.statement, database.session.bind)

        df = df.merge(
            df_db,
            how='left',
            on='cod_empresa'
        )

        return df

    @classmethod
    def __inserir_unidades(
        self,
        df: pd.DataFrame,
        infos: InfosCarregar
    ) -> InfosCarregar:
        df = df[df['id_unidade'].isna()].copy()

        if df.empty:
            infos.qtd_inseridos = 0
            infos.add_error(error='df vazio ao inserir')
            return infos

        df = df.drop(columns='id_unidade')
        df['data_inclusao'] = datetime.now(tz=TIMEZONE_SAO_PAULO)

        try:
            qtd = df.to_sql(
                name=self.__tablename__,
                con=database.session.bind,
                if_exists='append',
                index=False
            )
            database.session.commit()
            infos.qtd_inseridos = qtd
        except IntegrityError:
            infos.ok = False
            infos.add_error(error='IntegrityError ao inserir')

        return infos

    @classmethod
    def __atualizar_unidades(
        self,
        df: pd.DataFrame,
        infos: InfosCarregar
    ) -> InfosCarregar:
        df = df[df['id_unidade'].notna()].copy()

        if df.empty:
            infos.qtd_atualizados = 0
            infos.add_error(error='df vazio ao atualizar')
            return infos

        df['last_server_update'] = datetime.now(TIMEZONE_SAO_PAULO)

        df_mappings = df.to_dict(orient='records')

        try:
            database.session.bulk_update_mappings(self, df_mappings)
            database.session.commit()
            infos.qtd_atualizados = len(df_mappings)
        except IntegrityError:
            infos.ok = False
            infos.add_error(error='IntegrityError ao atualizar')

        return infos

