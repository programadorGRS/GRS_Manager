from datetime import date, datetime

import numpy as np
import pandas as pd
from sqlalchemy.exc import IntegrityError

from src import TIMEZONE_SAO_PAULO
from src.extensions import database
from src.soc_web_service.exporta_dados import ExportaDados

from ..empresa.empresa import Empresa
from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..job.job_infos import JobInfos
from ..unidade.unidade import Unidade


class Funcionario(database.Model):
    __tablename__ = 'Funcionario'
    id_funcionario = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod_funcionario = database.Column(database.Integer, nullable=False)
    nome_funcionario = database.Column(database.String(100))
    cpf_funcionario = database.Column(database.String(20))
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'), nullable=False)
    id_unidade = database.Column(database.Integer, database.ForeignKey('Unidade.id_unidade'))
    cod_setor = database.Column(database.String(100))
    nome_setor = database.Column(database.String(100))
    cod_cargo = database.Column(database.String(100))
    nome_cargo = database.Column(database.String(100))
    situacao = database.Column(database.String(50))
    data_adm = database.Column(database.Date)
    data_dem = database.Column(database.Date)
    data_inclusao = database.Column(database.DateTime)

    @classmethod
    def carregar_funcionarios(
        self,
        id_empresa: int,
        data_inicio: date | None = None,
        data_fim: date | None = None
    ):
        '''
            Insere e Atualiza os Funcionários da Empresa passada.

            Args:
                data_inicio/fim (datetime.date, optional): não tem limite de 
                dias. \
                Se os dois forem passados, a pesquisa será filtrada por data. \
                Caso contrário, o parametro parametroData será marcado como \
                False
        '''
        EMPRESA: Empresa = Empresa.query.get(id_empresa)
        EMPRESA_PRINCIPAL: EmpresaPrincipal = (
            EmpresaPrincipal.query.get(EMPRESA.cod_empresa_principal)
        )
        KEYS = getattr(EMPRESA_PRINCIPAL, 'chaves_exporta_dados', None)

        infos = JobInfos(
            tabela=self.__tablename__,
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            id_empresa=EMPRESA.id_empresa
        )

        if not KEYS:
            infos.ok = False
            infos.add_error('Chaves Exporta Dados não encontradas')
            return infos

        ex = ExportaDados(
            wsdl_filename='prod/ExportaDadosWs.xml',
            exporta_dados_keys_filename=KEYS
        )

        PARAMETRO = ex.cadastro_funcionarios(
            empresa=EMPRESA_PRINCIPAL.cod,
            codigo=ex.EXPORTA_DADOS_KEYS.get('CAD_FUNCIONARIOS_EMPRESA_COD'),
            chave=ex.EXPORTA_DADOS_KEYS.get('CAD_FUNCIONARIOS_EMPRESA_KEY'),
            empresaTrabalho=EMPRESA.cod_empresa,
            dataInicio=data_inicio if data_inicio else None,
            dataFim=data_fim if data_fim else None,
            parametroData=True if data_inicio and data_fim else None
        )

        infos = JobInfos(
            tabela=self.__tablename__,
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            id_empresa=EMPRESA.id_empresa
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
            id_empresa=EMPRESA.id_empresa,
            cod_emp_princ=EMPRESA_PRINCIPAL.cod
        )

        # NOTE: prevenir que não hajam funcionarios sem Unidade
        df = df[df['id_unidade'].notna()]
        df = df.drop(columns='cod_unidade') # col desnecessaria no df final
        if df.empty:
            infos.add_error(error='df vazio ao validar id_unidade')
            return infos

        # NOTE: passar cópia para que o df original não seja modificado
        infos = self.__inserir_funcionarios(df=df.copy(), infos=infos)
        infos = self.__atualizar_funcionarios(df=df.copy(), infos=infos)

        return infos

    @classmethod
    def __tratar_df_exporta_dados(
            self,
            df: pd.DataFrame,
            id_empresa: int,
            cod_emp_princ: int
        ) -> pd.DataFrame:
        COLS = {
            'CODIGO': 'cod_funcionario',
            'NOME': 'nome_funcionario',
            'CPFFUNCIONARIO': 'cpf_funcionario',
            'CODIGOUNIDADE': 'cod_unidade',
            'CODIGOSETOR': 'cod_setor',
            'NOMESETOR': 'nome_setor',
            'CODIGOCARGO': 'cod_cargo',
            'NOMECARGO': 'nome_cargo',
            'SITUACAO': 'situacao',
            'DATA_ADMISSAO': 'data_adm',
            'DATA_DEMISSAO': 'data_dem'
        }

        df = df.copy()

        df = df[list(COLS.keys())]
        df = df.replace({'': None})
        df.rename(columns=COLS, inplace=True)

        df['cod_funcionario'] = df['cod_funcionario'].astype(int)

        for col in ['data_adm','data_dem']:
            df[col] = pd.to_datetime(
                df[col],
                dayfirst=True,
                errors='coerce'
            ).dt.date
            df[col] = df[col].astype(object).replace(np.nan, None)

        df = self.__buscar_infos_funcionarios(id_empresa=id_empresa, df=df)

        df = self.__buscar_infos_unidades(id_empresa=id_empresa, df=df)

        df['id_empresa'] = id_empresa
        df['cod_empresa_principal'] = cod_emp_princ

        return df

    @staticmethod
    def __buscar_infos_funcionarios(
        id_empresa: int,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        query = (
                database.session.query(
                    Funcionario.id_funcionario,
                    Funcionario.cod_funcionario
            )
            .filter(Funcionario.id_empresa == id_empresa)
        )
        df_db = pd.read_sql(sql=query.statement, con=database.session.bind)

        df = df.merge(df_db, how='left', on='cod_funcionario')
        return df

    @staticmethod
    def __buscar_infos_unidades(
        id_empresa: int,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        query = (
                database.session.query(
                Unidade.id_unidade,
                Unidade.cod_unidade
            )
            .filter(Unidade.id_empresa == id_empresa)
        )
        df_db = pd.read_sql(sql=query.statement, con=database.session.bind)

        df = df.merge(df_db, how='left', on='cod_unidade')
        return df

    @classmethod
    def __inserir_funcionarios(
        self,
        df: pd.DataFrame,
        infos: JobInfos
    ) -> JobInfos:
        df = df[df['id_funcionario'].isna()].copy()

        if df.empty:
            infos.qtd_inseridos = 0
            infos.add_error(error='df vazio ao inserir')
            return infos

        df = df.drop(columns='id_funcionario')
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
    def __atualizar_funcionarios(
        self,
        df: pd.DataFrame,
        infos: JobInfos
    ) -> JobInfos:
        df = df[df['id_funcionario'].notna()].copy()

        if df.empty:
            infos.qtd_atualizados = 0
            infos.add_error(error='df vazio ao atualizar')
            return infos

        df_mappings = df.to_dict(orient='records')

        try:
            database.session.bulk_update_mappings(self, df_mappings)
            database.session.commit()
            infos.qtd_atualizados = len(df_mappings)
        except IntegrityError:
            infos.ok = False
            infos.add_error(error='IntegrityError ao atualizar')

        return infos

