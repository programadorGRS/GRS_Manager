import pandas as pd
import requests

from src import database
from src.exporta_dados import ExportaDadosWS
from src.utils import get_json_configs

from ..empresa_principal.empresa_principal import EmpresaPrincipal


class UsuarioSOC(database.Model):
    __tablename__ = 'UsuarioSOC'

    id = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod = database.Column(database.Integer, nullable=False)
    nome = database.Column(database.String(300))
    email = database.Column(database.String(400))
    tipo = database.Column(database.String(255))
    ativo = database.Column(database.Boolean)

    @classmethod
    def carregar_usuarios(self, cod_empresa_principal: int, ativo: int):
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(cod_empresa_principal)
        CREDENCIAIS = get_json_configs(EMPRESA_PRINCIPAL.configs_exporta_dados)

        PARAM = ExportaDadosWS.cadastro_pessoas_usuarios(
            empresa=EMPRESA_PRINCIPAL.cod,
            codigo=CREDENCIAIS.get('CAD_PESSOAS_USUARIOS_COD'),
            chave=CREDENCIAIS.get('CAD_PESSOAS_USUARIOS_KEY'),
            ativo=ativo
        )

        resp = ExportaDadosWS.request_exporta_dados_ws(parametro=PARAM)
        response: requests.Response = resp.get('response')

        if response.status_code != 200:
            return None
        
        if resp.get('erro_soc'):
            return None
        
        df = ExportaDadosWS.xml_to_dataframe(xml_string=response.text)

        if df.empty:
            return None
        
        df = self.__tratar_df_exporta_dados(df=df, cod_empresa_principal=cod_empresa_principal)

        inseridos = self.__inserir_usuarios(df=df.copy(deep=True))
        atualizados = self.__atualizar_usuarios(df=df.copy(deep=True))

        return {'inseridos': inseridos, 'atualizados': atualizados}
    
    @classmethod
    def __tratar_df_exporta_dados(self, df: pd.DataFrame, cod_empresa_principal: int):
        COLS = {
            'CODIGO': 'cod',
            'NOME': 'nome',
            'EMAIL': 'email',
            'TIPO': 'tipo',
            'ATIVO': 'ativo'
        }

        df = df[list(COLS.keys())]

        df.rename(columns=COLS, inplace=True)

        for col in ['cod', 'ativo']:
            df[col] = df[col].astype(int)

        df['cod_empresa_principal'] = cod_empresa_principal

        df = self.__buscar_id_usuarios(df=df, cod_empresa_principal=cod_empresa_principal)

        return df
    
    @classmethod
    def __buscar_id_usuarios(self, df: pd.DataFrame, cod_empresa_principal: int):
        query = (
            database.session.query(self.id, self.cod)
            .filter(self.cod_empresa_principal == cod_empresa_principal)
        )
        df_db = pd.read_sql(sql=query.statement, con=database.session.bind)

        df = df.merge(
            right=df_db,
            how='left',
            on='cod'
        )

        return df
    
    @classmethod
    def __inserir_usuarios(self, df: pd.DataFrame):
        df = df[df['id'].isna()]

        if df.empty:
            return 0

        df.drop(columns='id', inplace=True)

        qtd = df.to_sql(
            name=self.__tablename__,
            con=database.session.bind,
            if_exists='append',
            index=False
        )

        return qtd

    @classmethod
    def __atualizar_usuarios(self, df: pd.DataFrame):
        df = df[df['id'].notna()]

        if df.empty:
            return 0

        df['id'] = df['id'].astype(int)

        df_mappings = df.to_dict(orient='records')

        database.session.bulk_update_mappings(self, df_mappings)

        return len(df_mappings)

