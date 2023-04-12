from datetime import datetime

import pandas as pd
from pytz import timezone

from src import database

from ..empresa.empresa import Empresa
from ..empresa_principal.empresa_principal import EmpresaPrincipal


class Unidade(database.Model):
    __tablename__ = 'Unidade'
    id_unidade = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'), nullable=False)
    cod_unidade = database.Column(database.String(255), nullable=False)
    nome_unidade = database.Column(database.String(255), nullable=False)
    emails = database.Column(database.String(500))
    ativo = database.Column(database.Boolean, nullable=False, default=True)
    
    pedidos = database.relationship('Pedido', backref='Unidade', lazy=True) # one to many

    cod_rh = database.Column(database.String(255))
    cnpj = database.Column(database.String(255))
    uf = database.Column(database.String(10))
    razao_social = database.Column(database.String(255))

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
    
    data_inclusao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    data_alteracao = database.Column(database.DateTime)
    alterado_por = database.Column(database.String(50))

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
        cod_empresa_principal: int | None = None,
        id_empresa: int = None,
        id_unidade: int = None,
        cod_unidade: int = None,
        nome: str = None,
        ativo: int = None
    ):
        models = [
            (self.id_unidade), (self.cod_empresa_principal), (self.id_empresa),
            (self.cod_unidade), (self.nome_unidade), (self.emails),
            (self.ativo), (self.conv_exames), (self.cod_rh),
            (self.cnpj), (self.uf), (self.data_inclusao), (self.data_alteracao),
            (self.incluido_por), (self.alterado_por), (self.conv_exames_emails),
            (self.conv_exames_corpo_email), (self.exames_realizados), (self.exames_realizados_emails),
            (self.absenteismo), (self.absenteismo_emails),
            (Empresa.id_empresa), (Empresa.cod_empresa), (Empresa.razao_social)
        ]

        params = []

        if cod_empresa_principal:
            params.append((self.cod_empresa_principal == cod_empresa_principal))
        if id_empresa:
            params.append(self.id_empresa == id_empresa)
        if id_unidade:
            params.append(self.id_unidade == id_unidade)
        if cod_unidade:
            params.append(self.cod_unidade.like(f'%{cod_unidade}%'))
        if nome:
            params.append(self.nome_unidade.like(f'%{nome}%'))
        if ativo == 0 or ativo == 1:
            params.append(self.ativo == ativo)

        query = (
            database.session.query(*models)
            .filter(*params)
            .join(Empresa, Empresa.id_empresa == self.id_empresa)
            .order_by(self.id_empresa)
            .order_by(self.nome_unidade)
        )
        return query

    @classmethod
    def inserir_unidades(
        self,
        cod_empresa_principal: int
    ) -> int | None:
        '''
        Carrega todas as Unidades no exporta dados da EmpresaPrincipal selecionada

        Insere apenas Unidades que cuja chave (cod_empresa + cod_unidade) não existe na db
        '''
        

        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           unidades)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = unidades(
            empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['UNIDADES_COD'],
            chave=credenciais['UNIDADES_KEY']
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:
            df_exporta_dados = df_exporta_dados[[
                'CODIGOEMPRESA',
                'CODIGOUNIDADE',
                'NOMEUNIDADE',
                'UNIDADEATIVA',
                'CODIGORHUNIDADE',
                'CNPJUNIDADE',
                'UF',
                'RAZAOSOCIAL'
            ]]
            df_exporta_dados['CODIGOEMPRESA'] = df_exporta_dados['CODIGOEMPRESA'].astype(int)
            df_exporta_dados['UNIDADEATIVA'] = df_exporta_dados['UNIDADEATIVA'].astype(int)

            # carregar empresas da db
            empresas_db = pd.read_sql(
                sql=(
                    database.session.query(
                        Empresa.id_empresa,
                        Empresa.cod_empresa
                    )
                    .filter(Empresa.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not empresas_db.empty:
                # pegar ids empresas
                df_final = pd.merge(
                    df_exporta_dados,
                    empresas_db,
                    how='left',
                    left_on='CODIGOEMPRESA',
                    right_on='cod_empresa'
                )
                df_final.drop(columns='cod_empresa', inplace=True)

                # pegar ids unidades
                unidades_db = pd.read_sql(
                    sql=(
                        database.session.query(
                            Unidade.id_unidade,
                            Unidade.cod_unidade,
                            Empresa.cod_empresa
                        )
                        .join(Empresa, Unidade.id_empresa == Empresa.id_empresa)
                        .filter(Unidade.cod_empresa_principal == cod_empresa_principal)
                    ).statement,
                    con=database.session.bind
                )
                df_final = pd.merge(
                    df_final,
                    unidades_db,
                    how='left',
                    left_on=['CODIGOEMPRESA', 'CODIGOUNIDADE'],
                    right_on=['cod_empresa', 'cod_unidade']
                )
                df_final.drop(columns=['cod_empresa', 'cod_unidade'], inplace=True)

                # manter apenas unidades novas
                df_final = df_final[df_final['id_unidade'].isna()]

                # remover unidades sem empresa na db ou sem cod de unidade
                df_final.dropna(
                    axis=0,
                    subset=['id_empresa', 'CODIGOEMPRESA', 'CODIGOUNIDADE'],
                    inplace=True
                )

                # tratar df
                df_final = df_final[[
                    'id_empresa',
                    'CODIGOUNIDADE',
                    'NOMEUNIDADE',
                    'UNIDADEATIVA',
                    'CODIGORHUNIDADE',
                    'CNPJUNIDADE',
                    'UF',
                    'RAZAOSOCIAL'
                ]]
                df_final = df_final.replace(to_replace={'': None})
                df_final = df_final.rename(columns={
                    'CODIGOUNIDADE': 'cod_unidade',
                    'NOMEUNIDADE': 'nome_unidade',
                    'UNIDADEATIVA': 'ativo',
                    'CODIGORHUNIDADE': 'cod_rh',
                    'CNPJUNIDADE': 'cnpj',
                    'UF': 'uf',
                    'RAZAOSOCIAL': 'razao_social'
                })
                df_final['cod_empresa_principal'] = cod_empresa_principal
                df_final['data_inclusao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df_final['incluido_por'] = 'Servidor'

                # inserir
                linhas_inseridas = df_final.to_sql(
                    name=self.__tablename__,
                    con=database.session.bind,
                    if_exists='append',
                    index=False
                )
                database.session.commit()
                
                return linhas_inseridas
            else:
                return None
        else:
            return None

    @classmethod
    def atualizar_unidades(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas as Unidades no exporta dados da EmpresaPrincipal selecionada

        Atualiza infos das Unidades que ja existem na db

        '''
        

        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           unidades)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = unidades(
            empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['UNIDADES_COD'],
            chave=credenciais['UNIDADES_KEY'],
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:
            df_exporta_dados = df_exporta_dados[[
                'CODIGOEMPRESA',
                'CODIGOUNIDADE',
                'NOMEUNIDADE',
                'UNIDADEATIVA',
                'CODIGORHUNIDADE',
                'CNPJUNIDADE',
                'UF',
                'RAZAOSOCIAL'
            ]]
            df_exporta_dados['CODIGOEMPRESA'] = df_exporta_dados['CODIGOEMPRESA'].astype(int)
            df_exporta_dados['UNIDADEATIVA'] = df_exporta_dados['UNIDADEATIVA'].astype(int)

            # pegar ids das unidades
            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Unidade.id_unidade,
                        Unidade.cod_unidade,
                        Empresa.cod_empresa
                    )
                    .join(Empresa, Empresa.id_empresa == Unidade.id_empresa)
                    .filter(Unidade.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='right',
                    left_on=['CODIGOEMPRESA', 'CODIGOUNIDADE'],
                    right_on=['cod_empresa', 'cod_unidade']
                )

                df_final.dropna(axis=0, subset=['UNIDADEATIVA', 'CODIGOUNIDADE', 'CODIGOEMPRESA'], inplace=True)
                
                df_final = df_final[[
                    'id_unidade',
                    'NOMEUNIDADE',
                    'UNIDADEATIVA',
                    'CODIGORHUNIDADE',
                    'CNPJUNIDADE',
                    'UF',
                    'RAZAOSOCIAL'
                ]]

                # tratar df
                df_final = df_final.replace(to_replace={'': None})
                df_final = df_final.rename(columns={
                    'NOMEUNIDADE': 'nome_unidade',
                    'UNIDADEATIVA': 'ativo',
                    'CODIGORHUNIDADE': 'cod_rh',
                    'CNPJUNIDADE': 'cnpj',
                    'UF': 'uf',
                    'RAZAOSOCIAL': 'razao_social'
                })
                df_final['data_alteracao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df_final['alterado_por'] = 'Servidor'

                df_final = df_final.to_dict(orient='records')

                database.session.bulk_update_mappings(Unidade, df_final)
                database.session.commit()
        
            return len(df_final)
