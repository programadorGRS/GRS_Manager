from datetime import datetime

import pandas as pd
from pytz import timezone

from src import database

from ..empresa_principal.empresa_principal import EmpresaPrincipal

from ..grupo.grupo import grupo_prestador


class Prestador(database.Model):
    __tablename__ = 'Prestador'
    id_prestador = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod_prestador = database.Column(database.Integer)
    nome_prestador = database.Column(database.String(255), nullable=False)
    emails = database.Column(database.String(500))
    ativo = database.Column(database.Boolean, nullable=False)
    # se recebe ou nao emails de solicitacao de ASOs
    solicitar_asos = database.Column(database.Boolean, default=True)
    cnpj = database.Column(database.String(100))
    uf = database.Column(database.String(4))
    razao_social = database.Column(database.String(255))

    pedidos = database.relationship('Pedido', backref='prestador', lazy=True) # one to many
    pedidos_socnet = database.relationship('PedidoSOCNET', backref='prestador', lazy=True) # one to many
    grupo = database.relationship('Grupo', secondary=grupo_prestador, backref='prestadores', lazy=True) # many to many

    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_prestador}> {self.nome_prestador}'

    @classmethod
    def buscar_prestadores(
        self,
        cod_empresa_principal: int | None = None,
        id_prestador: int | None = None,
        cod_prestador: int | None = None,
        nome: str | None = None,
        ativo: int | None = None
    ):
        params = []

        if cod_empresa_principal:
            params.append(self.cod_empresa_principal == cod_empresa_principal)
        if id_prestador:
            params.append(self.id_prestador == id_prestador)
        if cod_prestador:
            params.append(self.cod_prestador == cod_prestador)
        if nome:
            params.append(self.nome_prestador.like(f'%{nome}%'))
        if ativo == 0 or ativo == 1:
            params.append(self.ativo == ativo)

        query = (
            database.session.query(self)
            .filter(*params)
            .order_by(self.nome_prestador)
        )
        return query


    @classmethod
    def inserir_prestadores(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas os Prestadores no exporta dados da EmpresaPrincipal selecionada (ativos e inativos)

        Insere apenas Prestadores não existem na db
        '''
        

        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           prestadores)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = prestadores(
            cod_empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['PRESTADORES_COD'],
            chave=credenciais['PRESTADORES_KEY'],
            ativo='' # carregar todos
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:

            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Prestador.id_prestador,
                        Prestador.cod_prestador
                    )
                    .filter(Prestador.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_exporta_dados['codigoPrestador'] = df_exporta_dados['codigoPrestador'].astype(int)
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='left',
                    left_on='codigoPrestador',
                    right_on='cod_prestador'
                )
                df_final = df_final[~df_final['id_prestador'].isin(df_database['id_prestador'])]
            else:
                df_final = df_exporta_dados

            # tratar df
            df_final = df_final[[
                'codigoPrestador',
                'nomePrestador',
                'razaoSocial',
                'cnpj',
                'estado',
                'email',
                'situacao'
            ]]
            df_final = df_final.replace(to_replace={'': None})
            df_final = df_final.rename(columns={
                    'codigoPrestador': 'cod_prestador',
                    'nomePrestador': 'nome_prestador',
                    'razaoSocial': 'razao_social',
                    'email': 'emails',
                    'estado': 'uf',
                    'situacao': 'ativo'
                })
            df_final['ativo'] = df_final['ativo'].replace({'Sim': True, 'Não': False})
            df_final['cod_empresa_principal'] = cod_empresa_principal
            df_final['data_inclusao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
            df_final['incluido_por'] = 'Servidor'

            # tratar emails
            df_final['emails'] = df_final['emails'].str.replace(',', ';')
            df_final['emails'] = df_final['emails'].str.replace(' ', '')
            df_final['emails'] = df_final['emails'].str.lower()
            df_final['emails'] = list(map(self.tratar_emails, df_final['emails']))

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
    def atualizar_prestadores(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas os Prestadores no exporta dados da EmpresaPrincipal selecionada

        Atualiza infos dos Prestadores que ja existem na db

        '''
        

        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           prestadores)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = prestadores(
            cod_empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['PRESTADORES_COD'],
            chave=credenciais['PRESTADORES_KEY'],
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:

            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Prestador.id_prestador,
                        Prestador.cod_prestador
                    )
                    .filter(Prestador.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_exporta_dados['codigoPrestador'] = df_exporta_dados['codigoPrestador'].astype(int)
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='right',
                    left_on='codigoPrestador',
                    right_on='cod_prestador'
                )
                df_final.dropna(axis=0, subset=['id_prestador', 'codigoPrestador'], inplace=True)

                # tratar df
                df_final = df_final[[
                    'id_prestador',
                    'nomePrestador',
                    'razaoSocial',
                    'cnpj',
                    'estado',
                    'email',
                    'situacao'
                ]]
                df_final = df_final.replace(to_replace={'': None})
                df_final = df_final.rename(columns={
                        'nomePrestador': 'nome_prestador',
                        'razaoSocial': 'razao_social',
                        'email': 'emails',
                        'estado': 'uf',
                        'situacao': 'ativo'
                })
                df_final['ativo'] = df_final['ativo'].replace({'Sim': True, 'Não': False})
                df_final['data_alteracao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df_final['alterado_por'] = 'Servidor'

                # tratar emails
                df_final['emails'] = df_final['emails'].str.replace(',', ';')
                df_final['emails'] = df_final['emails'].str.replace(' ', '')
                df_final['emails'] = df_final['emails'].str.lower()
                df_final['emails'] = list(map(self.tratar_emails, df_final['emails']))

                df_final = df_final.to_dict(orient='records')

                database.session.bulk_update_mappings(Prestador, df_final)
                database.session.commit()
        
            return len(df_final)
    
    @staticmethod
    def tratar_emails(emails: str):
        if emails:
            emails = emails.split(sep=';')
            for indice, email in enumerate(emails):
                if not email:
                    emails.pop(indice)
            return ';'.join(emails)
        else:
            return None
