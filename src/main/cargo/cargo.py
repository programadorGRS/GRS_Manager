import pandas as pd

from src import database
from src.exporta_dados import ExportaDadosWS
from src.utils import get_json_configs

from ..empresa.empresa import Empresa
from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..job.job_infos import JobInfos


class Cargo(database.Model):
    __tablename__ = 'Cargo'

    id = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'), nullable=False)
    cod_cargo = database.Column(database.String(255), nullable=False)
    nome_cargo = database.Column(database.String(300))
    ativo = database.Column(database.Integer, nullable=False)
    cbo = database.Column(database.String(255))
    cod_rh = database.Column(database.String(255))

    @classmethod
    def carregar_cargos(self, cod_empresa_principal: int) -> JobInfos:
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(cod_empresa_principal)
        CREDENCIAIS = get_json_configs(EMPRESA_PRINCIPAL.configs_exporta_dados)

        PARAMETRO = ExportaDadosWS.cargos(
            empresa=EMPRESA_PRINCIPAL.cod,
            codigo=CREDENCIAIS.get('CARGOS_COD', ''),
            chave=CREDENCIAIS.get('CARGOS_KEY', '')
        )

        resp = ExportaDadosWS.request_exporta_dados_ws(parametro=PARAMETRO)

        infos = JobInfos(
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
        infos.qtd_inseridos = self.__inserir_cargos(df=df.copy())

        infos.qtd_atualizados = self.__atualizar_cargos(df=df.copy())

        return infos

    @classmethod
    def __tratar_df_exporta_dados(self, df: pd.DataFrame, cod_empresa_principal: int):
        COLS = {
            'CODIGOEMPRESA': 'cod_empresa',
            'CODIGOCARGO': 'cod_cargo',
            'NOMECARGO': 'nome_cargo',
            'CODIGORHCARGO': 'cod_rh',
            'CARGOATIVO': 'ativo',
            'CBO': 'cbo'
        }

        df = df[list(COLS.keys())]
        df = df.rename(columns=COLS)
        df = df.replace(to_replace={'': None})

        for col in ['cod_empresa', 'ativo']:
            df[col] = df[col].astype(int)

        df = self.__buscar_id_empresas(df=df, cod_empresa_principal=cod_empresa_principal)
        df = df.drop(columns='cod_empresa')
        # remover cargos sem empresa valida
        df = df[df['id_empresa'].notna()].copy()
        df['id_empresa'] = df['id_empresa'].astype(int)
        
        df = self.__buscar_id_cargos(df=df, cod_empresa_principal=cod_empresa_principal)

        df['cod_empresa_principal'] = cod_empresa_principal

        return df

    @classmethod
    def __buscar_id_cargos(self, df: pd.DataFrame, cod_empresa_principal: int):
        query = (
            database.session.query(self.id, self.id_empresa, self.cod_cargo)
            .filter(self.cod_empresa_principal == cod_empresa_principal)
        )
        df_db = pd.read_sql(query.statement, database.session.bind)

        # NOTE: cod dos cargos podem se repetir em empresas diferentes
        df = df.merge(
            right=df_db,
            how='left',
            on=['id_empresa', 'cod_cargo']
        )

        return df
    
    @classmethod
    def __buscar_id_empresas(self, df: pd.DataFrame, cod_empresa_principal: int):
        query = (
            database.session.query(Empresa.id_empresa, Empresa.cod_empresa)
            .filter(Empresa.cod_empresa_principal == cod_empresa_principal)
        )
        df_db = pd.read_sql(query.statement, database.session.bind)

        df = df.merge(
            right=df_db,
            how='left',
            on='cod_empresa'
        )

        return df

    @classmethod
    def __inserir_cargos(self, df: pd.DataFrame):
        df = df[df['id'].isna()].copy()

        if df.empty:
            return 0
        
        df.drop(columns='id', inplace=True)

        qtd = df.to_sql(
            name=self.__tablename__,
            con=database.session.bind,
            if_exists='append',
            index=False
        )
        database.session.commit()

        return qtd

    @classmethod
    def __atualizar_cargos(self, df: pd.DataFrame):
        df = df[df['id'].notna()].copy()

        if df.empty:
            return 0

        df = df[['id', 'nome_cargo', 'cod_rh', 'ativo', 'cbo']]

        df['id'] = df['id'].astype(int)

        df_mappings = df.to_dict(orient='records')

        database.session.bulk_update_mappings(self, df_mappings)
        database.session.commit()

        return len(df_mappings)


