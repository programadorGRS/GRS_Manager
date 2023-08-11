from datetime import datetime

import pandas as pd
from pytz import timezone

from src import database

from ..empresa_principal.empresa_principal import EmpresaPrincipal


class Exame(database.Model):
    __tablename__ = 'Exame'
    id_exame = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod_exame = database.Column(database.String(255), nullable=False)
    nome_exame = database.Column(database.String(255), nullable=False)

    prazo = database.Column(database.Integer, default=0) # dias

    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_exame}> {self.nome_exame}'

    @classmethod
    def buscar_exames(
        cls,
        cod_emp_princ: int | None = None,
        id_exame: int | None = None,
        cod_exame: str | None = None,
        nome_exame: str | None = None,
        prazo_exame: int | None = None
    ):
        params = []

        if cod_emp_princ:
            params.append(cls.cod_empresa_principal == cod_emp_princ)
        if id_exame:
            params.append(cls.id_exame == id_exame)
        if cod_exame:
            params.append(cls.cod_exame.like(f'%{cod_exame}%'))
        if nome_exame:
            params.append(cls.nome_exame.like(f'%{nome_exame}%'))
        if prazo_exame is not None:
            params.append(cls.prazo == prazo_exame)

        query = (
            database.session.query(cls)  # type: ignore
            .filter(*params)
            .order_by(cls.nome_exame)
        )

        return query

    @classmethod
    def inserir_exames(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas os Exames no exporta dados da EmpresaPrincipal selecionada

        Insere os exames que ainda nao existem na db
        '''
        from modules.exporta_dados import (exames, exporta_dados,
                                           get_json_configs)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = exames(
            cod_empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXAMES_COD'],
            chave=credenciais['EXAMES_KEY'],
        )
        df = exporta_dados(parametro=par)
        
        if not df.empty:
            exames_db = (
                database.session.query(Exame.cod_exame)
                .filter(Exame.cod_empresa_principal == cod_empresa_principal)
                .all()
            )
            exames_db = [i.cod_exame for i in exames_db]

            df = df[~df['CODIGO'].isin(exames_db)]

            # tratar df
            df = df.replace(to_replace={'': None})
            df = df.rename(columns={
                'CODIGO': 'cod_exame',
                'NOME': 'nome_exame',
            })
            df['cod_empresa_principal'] = cod_empresa_principal
            df['data_inclusao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
            df['incluido_por'] = 'Servidor'

            # inserir
            linhas_inseridas = df.to_sql(
                name=self.__tablename__,
                con=database.session.bind,
                if_exists='append',
                index=False
            )
            database.session.commit()
            
            return linhas_inseridas


    @classmethod
    def atualizar_exames(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas os Exames no exporta dados da EmpresaPrincipal selecionada

        Atualiza as infos dos exames que ja existem na db
        '''
        from modules.exporta_dados import (exames, exporta_dados,
                                           get_json_configs)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = exames(
            cod_empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXAMES_COD'],
            chave=credenciais['EXAMES_KEY'],
        )
        df = exporta_dados(parametro=par)
        
        if not df.empty:
            exames_db = pd.read_sql(
                sql=(
                    database.session.query(
                        Exame.id_exame,
                        Exame.cod_exame
                    )
                    .filter(Exame.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not exames_db.empty:
                df = pd.merge(
                    df,
                    exames_db,
                    how='right',
                    left_on='CODIGO',
                    right_on='cod_exame'
                )

                # tratar df
                df = df.replace(to_replace={'': None})
                df = df[['id_exame', 'NOME']]
                df = df.rename(columns={'NOME': 'nome_exame'})
                df['data_alteracao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df['alterado_por'] = 'Servidor'

                df = df.to_dict(orient='records')

                database.session.bulk_update_mappings(Exame, df)
                database.session.commit()
                
                return len(df)
