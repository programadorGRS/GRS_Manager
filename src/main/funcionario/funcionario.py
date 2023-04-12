from datetime import datetime

import numpy as np
import pandas as pd

from src import TIMEZONE_SAO_PAULO, database

from ..empresa.empresa import Empresa
from ..empresa_principal.empresa_principal import EmpresaPrincipal
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
    def inserir_funcionarios(self, id_empresa: int) -> int:
        from modules.exporta_dados import (cadastro_funcionarios,
                                           exporta_dados, get_json_configs)

        EMPRESA: Empresa = Empresa.query.get(id_empresa)
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(EMPRESA.cod_empresa_principal)
        CREDENCIAIS: dict[str, any] = get_json_configs(EMPRESA_PRINCIPAL.configs_exporta_dados)

        PARAMETRO = cadastro_funcionarios(
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            cod_exporta_dados=CREDENCIAIS['CAD_FUNCIONARIOS_EMPRESA_COD'],
            chave=CREDENCIAIS['CAD_FUNCIONARIOS_EMPRESA_KEY'],
            empresaTrabalho=EMPRESA.cod_empresa
        )
        
        df_exporta_dados = exporta_dados(parametro=PARAMETRO)

        if df_exporta_dados.empty:
            return 0

        df_exporta_dados.replace('', None, inplace=True)
        df_exporta_dados['CODIGOEMPRESA'] = df_exporta_dados['CODIGOEMPRESA'].astype(int)
        df_exporta_dados['CODIGO'] = df_exporta_dados['CODIGO'].astype(int)

        for col in ['DATA_ADMISSAO','DATA_DEMISSAO']:
            df_exporta_dados[col] = pd.to_datetime(df_exporta_dados[col], dayfirst=True, errors='coerce').dt.date
            df_exporta_dados[col] = df_exporta_dados[col].astype(object).replace(np.nan, None)

        # pegar ids dos funcionarios e remover ja existentes
        df_final: pd.DataFrame = self._buscar_infos_funcionarios(
            id_empresa=EMPRESA.id_empresa,
            df_exporta_dados=df_exporta_dados
        )
        df_final = df_final[df_final['id_funcionario'].isna()]
        if df_final.empty:
            return 0

        df_final = self._buscar_infos_unidades(
            id_empresa=EMPRESA.id_empresa,
            df_exporta_dados=df_final
        )

        df_final.dropna(axis=0, subset='id_unidade', inplace=True)
        if df_final.empty:
            return 0

        df_final = df_final[[
            'id_empresa',
            'id_unidade',
            'CODIGO',
            'NOME',
            'CPFFUNCIONARIO',
            'CODIGOSETOR',
            'NOMESETOR',
            'CODIGOCARGO',
            'NOMECARGO',
            'SITUACAO',
            'DATA_ADMISSAO',
            'DATA_DEMISSAO'
        ]]

        df_final.rename(
            columns={
                'CODIGO': 'cod_funcionario',
                'NOME': 'nome_funcionario',
                'CPFFUNCIONARIO': 'cpf_funcionario',
                'CODIGOSETOR': 'cod_setor',
                'NOMESETOR': 'nome_setor',
                'CODIGOCARGO': 'cod_cargo',
                'NOMECARGO': 'nome_cargo',
                'SITUACAO': 'situacao',
                'DATA_ADMISSAO': 'data_adm',
                'DATA_DEMISSAO': 'data_dem'
            },
            inplace=True
        )
        df_final['cod_empresa_principal'] = EMPRESA_PRINCIPAL.cod
        df_final['data_inclusao'] = datetime.now(tz=TIMEZONE_SAO_PAULO)

        qtd_inseridos = df_final.to_sql(name=self.__tablename__, con=database.session.bind, if_exists='append', index=False)
        database.session.commit()
        return qtd_inseridos
    
    @classmethod
    def atualizar_funcionarios(self, id_empresa: int) -> int:
        from modules.exporta_dados import (cadastro_funcionarios,
                                           exporta_dados, get_json_configs)

        EMPRESA: Empresa = Empresa.query.get(id_empresa)
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(EMPRESA.cod_empresa_principal)
        CREDENCIAIS: dict[str, any] = get_json_configs(EMPRESA_PRINCIPAL.configs_exporta_dados)

        PARAMETRO = cadastro_funcionarios(
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            cod_exporta_dados=CREDENCIAIS['CAD_FUNCIONARIOS_EMPRESA_COD'],
            chave=CREDENCIAIS['CAD_FUNCIONARIOS_EMPRESA_KEY'],
            empresaTrabalho=EMPRESA.cod_empresa
        )
        
        df_exporta_dados = exporta_dados(parametro=PARAMETRO)

        if df_exporta_dados.empty:
            return 0

        df_exporta_dados.replace('', None, inplace=True)
        df_exporta_dados['CODIGOEMPRESA'] = df_exporta_dados['CODIGOEMPRESA'].astype(int)
        df_exporta_dados['CODIGO'] = df_exporta_dados['CODIGO'].astype(int)

        for col in ['DATA_ADMISSAO','DATA_DEMISSAO']:
            df_exporta_dados[col] = pd.to_datetime(df_exporta_dados[col], dayfirst=True, errors='coerce').dt.date
            df_exporta_dados[col] = df_exporta_dados[col].astype(object).replace(np.nan, None)

        # pegar ids dos funcionarios e manter apenas os que ja existem
        df_final: pd.DataFrame = self._buscar_infos_funcionarios(
            id_empresa=EMPRESA.id_empresa,
            df_exporta_dados=df_exporta_dados
        )
        df_final = df_final[~df_final['id_funcionario'].isna()]
        if df_final.empty:
            return 0

        df_final = self._buscar_infos_unidades(
            id_empresa=EMPRESA.id_empresa,
            df_exporta_dados=df_final
        )

        df_final.dropna(axis=0, subset='id_unidade', inplace=True)
        if df_final.empty:
            return 0

        df_final = df_final[[
            'id_funcionario',
            'id_empresa',
            'id_unidade',
            'CODIGO',
            'NOME',
            'CPFFUNCIONARIO',
            'CODIGOSETOR',
            'NOMESETOR',
            'CODIGOCARGO',
            'NOMECARGO',
            'SITUACAO',
            'DATA_ADMISSAO',
            'DATA_DEMISSAO'
        ]]

        df_final.rename(
            columns={
                'CODIGO': 'cod_funcionario',
                'NOME': 'nome_funcionario',
                'CPFFUNCIONARIO': 'cpf_funcionario',
                'CODIGOSETOR': 'cod_setor',
                'NOMESETOR': 'nome_setor',
                'CODIGOCARGO': 'cod_cargo',
                'NOMECARGO': 'nome_cargo',
                'SITUACAO': 'situacao',
                'DATA_ADMISSAO': 'data_adm',
                'DATA_DEMISSAO': 'data_dem'
            },
            inplace=True
        )
        df_final['cod_empresa_principal'] = EMPRESA_PRINCIPAL.cod

        dict_maps: list[dict[str, any]] = df_final.to_dict(orient='records')
        database.session.bulk_update_mappings(Funcionario, dict_maps)
        database.session.commit()
        return len(dict_maps)

    @staticmethod
    def _buscar_infos_funcionarios(id_empresa: int, df_exporta_dados: pd.DataFrame) -> pd.DataFrame:
        query = (
                database.session.query(
                    Funcionario.id_funcionario,
                    Funcionario.cod_funcionario
            )
            .filter(Funcionario.id_empresa == id_empresa)
        )
        df_database = pd.read_sql(sql=query.statement, con=database.session.bind)
    
        df_final = pd.merge(
            df_exporta_dados,
            df_database,
            how='left',
            left_on='CODIGO',
            right_on='cod_funcionario'
        )
        return df_final
    
    @staticmethod
    def _buscar_infos_unidades(id_empresa: int, df_exporta_dados: pd.DataFrame) -> pd.DataFrame:
        query = (
                database.session.query(
                Unidade.id_empresa,
                Unidade.id_unidade,
                Unidade.cod_unidade,
                Empresa.cod_empresa
            )
            .filter(Unidade.id_empresa == id_empresa)
            .filter(Empresa.id_empresa == id_empresa)
            .outerjoin(Empresa, Unidade.id_empresa == Empresa.id_empresa)
        )
        df_database = pd.read_sql(sql=query.statement, con=database.session.bind)

        df_final = pd.merge(
            df_exporta_dados,
            df_database,
            how='left',
            left_on=['CODIGOEMPRESA', 'CODIGOUNIDADE'],
            right_on=['cod_empresa', 'cod_unidade']
        )
        return df_final
