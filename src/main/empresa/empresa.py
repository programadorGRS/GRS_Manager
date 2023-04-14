from datetime import datetime

import pandas as pd
from pytz import timezone

from src import database

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..grupo.grupo import grupo_empresa


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
    
    pedidos = database.relationship('Pedido', backref='empresa', lazy=True) # one to many
    pedidos_proc = database.relationship('PedidoProcessamento', backref='empresa', lazy=True) # one to many
    grupo = database.relationship('Grupo', secondary=grupo_empresa, backref='empresas', lazy=True) # many to many
    unidades = database.relationship('Unidade', backref='empresa', lazy=True) # one to many
    jobs = database.relationship('Job', backref='empresa', lazy=True) # one to many

    # convocacao de exames
    conv_exames = database.Column(database.Boolean, default=True)
    conv_exames_emails = database.Column(database.String(500))
    conv_exames_corpo_email = database.Column(database.Integer, default=1)
    
    conv_exames_convocar_clinico = database.Column(database.Boolean, default=False)
    conv_exames_nunca_realizados = database.Column(database.Boolean, default=True)
    conv_exames_per_nunca_realizados = database.Column(database.Boolean, default=False)
    conv_exames_pendentes = database.Column(database.Boolean, default=True)
    conv_exames_pendentes_pcmso = database.Column(database.Boolean, default=False)
    conv_exames_selecao = database.Column(database.Integer, default=1)

    # exames realizados
    exames_realizados = database.Column(database.Boolean, default=True)
    exames_realizados_emails = database.Column(database.String(500))

    # absenteismo
    absenteismo = database.Column(database.Boolean, default=True)
    absenteismo_emails = database.Column(database.String(500))
    
    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_empresa}> {self.razao_social}'

    @classmethod
    def buscar_empresas(
        self,
        cod_empresa_principal: int | None = None,
        id_empresa: int = None,
        cod_empresa: int = None,
        nome: str = None,
        ativo: int = None
    ):
        params = []

        if cod_empresa_principal:
            params.append((self.cod_empresa_principal == cod_empresa_principal))
        if id_empresa:
            params.append(self.id_empresa == id_empresa)
        if cod_empresa:
            params.append(self.cod_empresa == cod_empresa)
        if nome:
            params.append(self.razao_social.like(f'%{nome}%'))
        if ativo == 0 or ativo == 1:
            params.append(self.ativo == ativo)

        query = (
            database.session.query(self)
            .filter(*params)
            .order_by(self.razao_social)
        )
        return query


    @classmethod
    def inserir_empresas(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas as Empresas no exporta dados da EmpresaPrincipal selecionada (ativas e inativas)

        Insere apenas Empresas não existem na db
        '''
        

        from modules.exporta_dados import (empresas, exporta_dados,
                                           get_json_configs)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = empresas(
            empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EMPRESAS_COD'],
            chave=credenciais['EMPRESAS_KEY'],
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:
            df_exporta_dados = df_exporta_dados[[
                'CODIGO',
                'NOMEABREVIADO',
                'RAZAOSOCIALINICIAL',
                'RAZAOSOCIAL',
                'ATIVO',
                'CNPJ',
                'UF'
            ]]
            df_exporta_dados['CODIGO'] = df_exporta_dados['CODIGO'].astype(int)
            df_exporta_dados['ATIVO'] = df_exporta_dados['ATIVO'].astype(int)

            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Empresa.id_empresa,
                        Empresa.cod_empresa
                    )
                    .filter(Empresa.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='left',
                    left_on='CODIGO',
                    right_on='cod_empresa'
                )
                df_final = df_final[[
                    'id_empresa',
                    'CODIGO',
                    'NOMEABREVIADO',
                    'RAZAOSOCIALINICIAL',
                    'RAZAOSOCIAL',
                    'ATIVO',
                    'CNPJ',
                    'UF'
                ]]
                df_final = df_final[~df_final['id_empresa'].isin(df_database['id_empresa'])]
            else:
                df_final = df_exporta_dados

            # tratar df
            df_final = df_final.replace(to_replace={'': None})
            df_final = df_final.rename(columns={
                'CODIGO': 'cod_empresa',
                'NOMEABREVIADO': 'nome_abrev',
                'RAZAOSOCIALINICIAL': 'razao_social_inicial',
                'RAZAOSOCIAL': 'razao_social',
                'ATIVO': 'ativo',
                'CNPJ': 'cnpj',
                'UF': 'uf'
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

    @classmethod
    def atualizar_empresas(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas as Empresas no exporta dados da EmpresaPrincipal selecionada

        Atualiza infos das Empresas que ja existem na db

        '''
        

        from modules.exporta_dados import (empresas, exporta_dados,
                                           get_json_configs)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = empresas(
            empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EMPRESAS_COD'],
            chave=credenciais['EMPRESAS_KEY'],
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:
            df_exporta_dados = df_exporta_dados[[
                'CODIGO',
                'NOMEABREVIADO',
                'RAZAOSOCIALINICIAL',
                'RAZAOSOCIAL',
                'ATIVO',
                'CNPJ',
                'UF'
            ]]
            df_exporta_dados['CODIGO'] = df_exporta_dados['CODIGO'].astype(int)
            df_exporta_dados['ATIVO'] = df_exporta_dados['ATIVO'].astype(int)

            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Empresa.id_empresa,
                        Empresa.cod_empresa
                    )
                    .filter(Empresa.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='right',
                    left_on='CODIGO',
                    right_on='cod_empresa'
                )

                df_final.dropna(axis=0, subset=['id_empresa', 'CODIGO'], inplace=True)

                df_final = df_final[[
                    'id_empresa',
                    'NOMEABREVIADO',
                    'RAZAOSOCIALINICIAL',
                    'RAZAOSOCIAL',
                    'ATIVO',
                    'CNPJ',
                    'UF'
                ]]

                # tratar df
                df_final = df_final.replace(to_replace={'': None})
                df_final = df_final.rename(columns={
                    'NOMEABREVIADO': 'nome_abrev',
                    'RAZAOSOCIALINICIAL': 'razao_social_inicial',
                    'RAZAOSOCIAL': 'razao_social',
                    'ATIVO': 'ativo',
                    'CNPJ': 'cnpj',
                    'UF': 'uf'
                })
                df_final['data_alteracao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df_final['alterado_por'] = 'Servidor'

                df_final = df_final.to_dict(orient='records')

                database.session.bulk_update_mappings(Empresa, df_final)
                database.session.commit()
        
            return len(df_final)
