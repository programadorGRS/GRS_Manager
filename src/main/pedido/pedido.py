from datetime import date, datetime, timedelta
from typing import Literal

import numpy as np
import pandas as pd
from flask_login import current_user
from flask_sqlalchemy import BaseQuery
from pytz import timezone
from sqlalchemy import and_, update
from sqlalchemy.inspection import inspect
from workalendar.america import Brazil

from src import TIMEZONE_SAO_PAULO, database

from ..empresa.empresa import Empresa
from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..exame.exame import Exame
from ..grupo.grupo import Grupo, grupo_empresa_prestador
from ..prestador.prestador import Prestador
from ..status.status import Status
from ..status.status_lib import StatusLiberacao
from ..status.status_rac import StatusRAC
from ..tipo_exame.tipo_exame import TipoExame
from ..unidade.unidade import Unidade


class Pedido(database.Model):
    __tablename__ = 'Pedido'
    id_ficha = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    seq_ficha = database.Column(database.Integer, nullable=False, unique=True)
    cod_funcionario = database.Column(database.Integer, nullable=False)
    cpf = database.Column(database.String(30))
    nome_funcionario = database.Column(database.String(150))
    data_ficha = database.Column(database.Date, nullable=False)
    cod_tipo_exame = database.Column(database.Integer, database.ForeignKey('TipoExame.cod_tipo_exame'), nullable=False)
    id_prestador = database.Column(database.Integer, database.ForeignKey('Prestador.id_prestador'))
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'), nullable=False)
    id_unidade = database.Column(database.Integer, database.ForeignKey('Unidade.id_unidade'), nullable=False)
    id_status = database.Column(database.Integer, database.ForeignKey('Status.id_status'), default=1, nullable=False)
    id_status_rac = database.Column(database.Integer, database.ForeignKey('StatusRAC.id_status'), default=1, nullable=False)
    prazo = database.Column(database.Integer, default=0)
    prev_liberacao = database.Column(database.Date)
    id_status_lib = database.Column(database.Integer, database.ForeignKey('StatusLiberacao.id_status_lib'), default=1, nullable=False)
    data_recebido = database.Column(database.Date)
    data_comparecimento = database.Column(database.Date)
    obs = database.Column(database.String(255))

    data_inclusao = database.Column(database.DateTime, nullable=False, default=datetime.now(tz=timezone('America/Sao_Paulo')))
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    # colunas para a planilha de pedidos
    COLS_CSV = [
        'cod_empresa_principal',
        'seq_ficha',
        'cod_funcionario',
        'nome_funcionario',
        'data_ficha',
        'tipo_exame',
        'cod_prestador',
        'prestador',
        'cod_empresa',
        'empresa',
        'cod_unidade',
        'unidade',
        'status_aso',
        'status_rac',
        'prev_liberacao',
        'tag',
        'nome_grupo',
        'id_ficha',
        'id_status',
        'id_status_rac',
        'data_recebido',
        'data_comparecimento',
        'obs'
    ]

    COLS_EMAIL = {
        'seq_ficha': 'Seq. Ficha',
        'cpf': 'CPF',
        'nome_funcionario': 'Nome Funcionário',
        'data_ficha': 'Data Ficha',
        'nome_tipo_exame': 'Tipo Exame',
        'nome_prestador': 'Prestador',
        'razao_social': 'Empresa',
        'nome_status_lib': 'Status'
    }

    @classmethod
    def inserir_pedidos(
        self,
        id_empresa: int,
        dataInicio: str,
        dataFim: str
    ) -> int:
        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           pedido_exame)


        EMPRESA: Empresa = Empresa.query.get(id_empresa)
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(EMPRESA.cod_empresa_principal)
        CREDENCIAIS = get_json_configs(EMPRESA_PRINCIPAL.configs_exporta_dados)


        PARAMETRO = pedido_exame(
            empresa=EMPRESA.cod_empresa,
            cod_exporta_dados=CREDENCIAIS['PEDIDO_EXAMES_COD'],
            chave=CREDENCIAIS['PEDIDO_EXAMES_KEY'],
            dataInicio=dataInicio,
            dataFim=dataFim
        )
        
        df_exporta_dados = exporta_dados(parametro=PARAMETRO)

        if df_exporta_dados.empty:
            return 0

        # validar duplicados
        df_exporta_dados = df_exporta_dados.replace({'': None})
        df_exporta_dados['SEQUENCIAFICHA'] = df_exporta_dados['SEQUENCIAFICHA'].astype(int)

        query_pedidos_db = (
            database.session.query(Pedido.seq_ficha)
            .filter(Pedido.seq_ficha.in_(df_exporta_dados['SEQUENCIAFICHA'].drop_duplicates()))
        )
        df_database = pd.read_sql(sql=query_pedidos_db.statement, con=database.session.bind)

        # remover seq_fichas que ja existem
        df_exporta_dados = df_exporta_dados[~df_exporta_dados['SEQUENCIAFICHA'].isin(df_database['seq_ficha'])]

        if df_exporta_dados.empty:
            return 0


        df_final = df_exporta_dados
        df_final['id_empresa'] = EMPRESA.id_empresa
        df_final['cod_empresa_principal'] = EMPRESA_PRINCIPAL.cod


        # pegar id do Exame e prazo
        df_final = self._buscar_infos_exames(
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            df_exporta_dados=df_exporta_dados
        )

        # pegar id Unidade
        df_final = self._buscar_infos_unidades(
            id_empresa=EMPRESA.id_empresa,
            df_exporta_dados=df_final
        )

        # pegar id do Prestador
        df_final = self._buscar_infos_prestadores(
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            df_exporta_dados=df_final
        )


        # organizar Prestador principal e Prazo maximo de cada Pedido
        df_final = self._buscar_prestador_final(df_exporta_dados=df_final)


        # inserir prev de liberacao
        df_final = self._gerar_prev_liberacao(df_exporta_dados=df_final)

        # calcular tag de previsao de liberacao
        df_final['id_status_lib'] = 1
        df_final['id_status_lib'] = list(
            map(
                self.calcular_tag_prev_lib,
                df_final['prev_liberacao']
            )
        )


        # tratar colunas
        for col in ['SEQUENCIAFICHA', 'CODIGOFUNCIONARIO', 'CODIGOTIPOEXAME', 'CODIGOEMPRESA']:
            df_final[col] = df_final[col].astype(int)
        
        df_final['CPFFUNCIONARIO'] = df_final['CPFFUNCIONARIO'].astype('string')
        
        df_final['id_status'] = int(1)
        df_final['data_inclusao'] = datetime.now(tz=TIMEZONE_SAO_PAULO)
        df_final['incluido_por'] = 'Servidor'

        df_final = df_final.rename(columns={
            'SEQUENCIAFICHA': 'seq_ficha',
            'CODIGOFUNCIONARIO': 'cod_funcionario',
            'CPFFUNCIONARIO': 'cpf',
            'NOMEFUNCIONARIO': 'nome_funcionario',
            'DATAFICHA': 'data_ficha',
            'CODIGOTIPOEXAME': 'cod_tipo_exame',
            'CODIGOPRESTADOR': 'cod_prestador',
            'CODIGOEMPRESA': 'cod_empresa',
            'CODIGOUNIDADE': 'cod_unidade'
        })


        # selecionar apenas as colunas q constam na tabela
        colunas_finais = self._selecionar_colunas_finais(
            tabela=self,
            df_columns=df_final.columns
        )
        df_final = df_final[colunas_finais]


        df_final.dropna(
            axis=0,
            subset=['id_empresa', 'id_unidade'],
            inplace=True
        )
        qtd_inseridos = df_final.to_sql(name=self.__tablename__, con=database.session.bind, if_exists='append', index=False)
        database.session.commit()
        return qtd_inseridos

    @classmethod
    def atualizar_pedidos(
        self,
        id_empresa: int,
        dataInicio: str,
        dataFim: str
    ) -> int:
        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           pedido_exame)


        EMPRESA: Empresa = Empresa.query.get(id_empresa)
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(EMPRESA.cod_empresa_principal)
        CREDENCIAIS = get_json_configs(EMPRESA_PRINCIPAL.configs_exporta_dados)


        PARAMETRO = pedido_exame(
            empresa=EMPRESA.cod_empresa,
            cod_exporta_dados=CREDENCIAIS['PEDIDO_EXAMES_COD'],
            chave=CREDENCIAIS['PEDIDO_EXAMES_KEY'],
            dataInicio=dataInicio,
            dataFim=dataFim
        )
        
        df_exporta_dados = exporta_dados(parametro=PARAMETRO)

        if df_exporta_dados.empty:
            return 0

        # validar duplicados
        df_exporta_dados = df_exporta_dados.replace({'': None})
        df_exporta_dados['SEQUENCIAFICHA'] = df_exporta_dados['SEQUENCIAFICHA'].astype(int)

        query_pedidos_db = (
            database.session.query(Pedido.seq_ficha)
            .filter(Pedido.seq_ficha.in_(df_exporta_dados['SEQUENCIAFICHA'].drop_duplicates()))
        )
        df_database = pd.read_sql(sql=query_pedidos_db.statement, con=database.session.bind)

        # manter apenas seq_fichas que ja existem
        df_exporta_dados = df_exporta_dados[df_exporta_dados['SEQUENCIAFICHA'].isin(df_database['seq_ficha'])]

        if df_exporta_dados.empty:
            return 0


        df_final = df_exporta_dados
        df_final['id_empresa'] = EMPRESA.id_empresa
        df_final['cod_empresa_principal'] = EMPRESA_PRINCIPAL.cod


        # pegar id do Exame e prazo
        df_final = self._buscar_infos_exames(
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            df_exporta_dados=df_exporta_dados
        )

        # pegar id Unidade
        df_final = self._buscar_infos_unidades(
            id_empresa=EMPRESA.id_empresa,
            df_exporta_dados=df_final
        )

        # pegar id do Prestador
        df_final = self._buscar_infos_prestadores(
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            df_exporta_dados=df_final
        )


        # organizar Prestador principal e Prazo maximo de cada Pedido
        df_final = self._buscar_prestador_final(df_exporta_dados=df_final)


        # inserir prev de liberacao
        df_final = self._gerar_prev_liberacao(df_exporta_dados=df_final)

        df_final = self._buscar_infos_pedidos(df_exporta_dados=df_final)

        # calcular tag de previsao de liberacao
        df_final['id_status_lib'] = 1
        df_final['id_status_lib'] = list(
            map(
                self.calcular_tag_prev_lib,
                df_final['prev_liberacao']
            )
        )

        df_final = self._atualizar_tags_finais(df_exporta_dados=df_final)


        # tratar colunas
        for col in ['SEQUENCIAFICHA', 'CODIGOFUNCIONARIO', 'CODIGOTIPOEXAME', 'CODIGOEMPRESA']:
            df_final[col] = df_final[col].astype(int)
        
        df_final['CPFFUNCIONARIO'] = df_final['CPFFUNCIONARIO'].astype('string')
        
        df_final['data_alteracao'] = datetime.now(tz=TIMEZONE_SAO_PAULO)
        df_final['alterado_por'] = 'Servidor'

        df_final = df_final.rename(columns={
            'SEQUENCIAFICHA': 'seq_ficha',
            'CODIGOFUNCIONARIO': 'cod_funcionario',
            'CPFFUNCIONARIO': 'cpf',
            'NOMEFUNCIONARIO': 'nome_funcionario',
            'DATAFICHA': 'data_ficha',
            'CODIGOTIPOEXAME': 'cod_tipo_exame',
            'CODIGOPRESTADOR': 'cod_prestador',
            'CODIGOEMPRESA': 'cod_empresa',
            'CODIGOUNIDADE': 'cod_unidade'
        })


        # selecionar apenas as colunas q constam na tabela
        colunas_finais = self._selecionar_colunas_finais(
            tabela=self,
            df_columns=df_final.columns
        )
        df_final = df_final[colunas_finais]

        # remover colunas que nao mudam
        df_final.drop(
            columns=['seq_ficha', 'id_status'],
            inplace=True
        )

        df_final.dropna(
            axis=0,
            subset='id_unidade',
            inplace=True
        )

        # NOTE: fazer isso para evitar que dicts_atualizar contenha np.nan
        # esse valor nao e aceito em databases
        df_final['id_prestador'] = df_final['id_prestador'].astype(object)
        df_final['id_prestador'] = df_final['id_prestador'].replace(np.nan, None)

        dicts_atualizar: list[dict[str, any]] = df_final.to_dict(orient='records')
        database.session.bulk_update_mappings(self, dicts_atualizar)
        database.session.commit()
        return len(dicts_atualizar)

    @staticmethod
    def calcular_tag_prev_lib(data_prev: pd.Timestamp) -> int:
        '''
            Calcula o status_lib baseado na data de previsao de liberacao recebida

            Retorna id do status lib
        '''
        
        hoje = datetime.now().date()

        datas_solicitar = (
            [hoje] +
            [hoje + timedelta(days=i) for i in range(1, 3)]
        ) # folga de dois dias p solicitar

        if not data_prev:
            return 1 # Sem previsao
        elif data_prev < hoje:
            return 5 # Atrasado
        elif data_prev in datas_solicitar:
            return 3 # Solicitar
        elif data_prev > hoje:
            return 4 # Em dia
        else:
            return 1 # Sem previsao

    @classmethod
    def atualizar_tags_prev_liberacao(self):
        '''
        Atualiza todas as tags de previsao de liberacao \
        de acordo com as condicoes:

        1=Sem previsao, 2=OK, 3=Solicitar, 4=Em dia, 5=Atrasado

        Retorna num de linhas afetadas.
        '''
        hoje = datetime.now().date()

        datas_solicitar = (
            [hoje] +
            [hoje + timedelta(days=i) for i in range(1, 3)]
        ) # folga de dois dias p solicitar

        finaliza_processo = [
            int(status.id_status)
            for status in Status.query.filter_by(finaliza_processo=True)
        ]
        
        parametros = [
            (Pedido.prev_liberacao == None, 1),
            (Pedido.prev_liberacao < hoje, 5),
            (Pedido.prev_liberacao > hoje, 4),
            (Pedido.prev_liberacao.in_(datas_solicitar), 3),
            (Pedido.id_status.in_(finaliza_processo), 2)
        ]

        linhas_afetadas = 0
        # afeta as mesmas linhas varias vezes, \
        # pode gerar numero maior do que o total de linhas na tabela

        for par, tag in parametros:
            q = database.session.execute(
                update(Pedido).
                where(par).
                values(id_status_lib=tag)
            )
            database.session.commit()

            linhas_afetadas = linhas_afetadas + q.rowcount
        
        return linhas_afetadas

    @staticmethod
    def _buscar_infos_exames(cod_empresa_principal: int, df_exporta_dados: pd.DataFrame) -> pd.DataFrame:
        query = (
            database.session.query(
                Exame.id_exame,
                Exame.cod_exame,
                Exame.prazo
            )
            .filter(Exame.cod_empresa_principal == cod_empresa_principal)
        )
        df_database = pd.read_sql(sql=query.statement, con=database.session.bind)
        
        df_final = pd.merge(
            df_exporta_dados,
            df_database,
            how='left',
            left_on='CODIGOINTERNOEXAME',
            right_on='cod_exame'
        )
        return df_final

    @staticmethod
    def _buscar_infos_unidades(id_empresa: int, df_exporta_dados: pd.DataFrame) -> pd.DataFrame:
        query = (
            database.session.query(
                Unidade.id_unidade,
                Unidade.cod_unidade
            )
            .filter(Unidade.id_empresa == id_empresa)
        )
        df_database = pd.read_sql(sql=query.statement, con=database.session.bind)

        df_final = pd.merge(
            df_exporta_dados,
            df_database,
            how='left',
            left_on='CODIGOUNIDADE',
            right_on='cod_unidade'
        )
        return df_final

    @staticmethod
    def _buscar_infos_prestadores(cod_empresa_principal: int, df_exporta_dados: pd.DataFrame) -> pd.DataFrame:
        query = (
            database.session.query(
                Prestador.id_prestador,
                Prestador.cod_prestador
            )
            .filter(Prestador.cod_empresa_principal == cod_empresa_principal)
        )
        df_database = pd.read_sql(sql=query.statement, con=database.session.bind)
        
        # adicionar uma linha Nan no df database para nao travar o merge quando o prestador \
        # estiver vazio no df_exporta_dados
        df_database = pd.concat(
            [df_database, pd.DataFrame({'id_prestador': [None], 'cod_prestador': [None]})],
            axis=0,
            ignore_index=True
        )
        df_database = df_database.astype('Int32')

        df_exporta_dados['CODIGOPRESTADOR'] = df_exporta_dados['CODIGOPRESTADOR'].astype('Int32')
        
        df_final = pd.merge(
            df_exporta_dados,
            df_database,
            how='left',
            left_on='CODIGOPRESTADOR',
            right_on='cod_prestador'
        )
        return df_final

    @staticmethod
    def _buscar_prestador_final(df_exporta_dados: pd.DataFrame) -> pd.DataFrame:
        """Busca prestadores dos exames com menor prazo. Geralmente é o clinico ou \
            outro exame do prestador que pegou o ASO por ultimo.
        """
        df_exporta_dados['prazo'] = df_exporta_dados['prazo'].fillna(0).astype(int)

        # prestadores principais
        df_prestadores = df_exporta_dados.sort_values(by='prazo', ascending=True).drop_duplicates('SEQUENCIAFICHA')
        df_prestadores = df_prestadores[['SEQUENCIAFICHA', 'id_prestador']]
        df_prestadores.rename(columns={'id_prestador': 'id_prestador_final'}, inplace=True)

        # prezos maximos
        df_prazos = df_exporta_dados.sort_values(by='prazo', ascending=False)
        df_prazos.drop_duplicates('SEQUENCIAFICHA', inplace=True)

        df_final = pd.merge(
            df_prazos,
            df_prestadores,
            how='left',
            on='SEQUENCIAFICHA'
        )
        df_final.drop(labels='id_prestador', axis=1, inplace=True)
        df_final.rename(columns={'id_prestador_final': 'id_prestador'}, inplace=True)
        return df_final

    @staticmethod
    def _gerar_prev_liberacao(df_exporta_dados: pd.DataFrame) -> pd.DataFrame:
        cal = Brazil() # usar workalendar
        
        df_exporta_dados['DATAFICHA'] = pd.to_datetime(df_exporta_dados['DATAFICHA'], dayfirst=True).dt.date
        df_exporta_dados['prev_liberacao'] = list(
            map(
                cal.add_working_days, # adicionar dias uteis
                df_exporta_dados['DATAFICHA'].values,
                df_exporta_dados['prazo'].values
            )
        )
        return df_exporta_dados

    @staticmethod
    def _selecionar_colunas_finais(tabela: object, df_columns: list):
        cols_db = [col.name for col in inspect(tabela).c]
        cols_df = list(dict.fromkeys([col for col in df_columns if col in cols_db]))
        return cols_df

    @staticmethod
    def _buscar_infos_pedidos(df_exporta_dados: pd.DataFrame) -> pd.DataFrame:
        SEQ_FICHAS: pd.Series[int] = df_exporta_dados['SEQUENCIAFICHA'].drop_duplicates().astype(int)
        
        query = (
            database.session.query(
                Pedido.seq_ficha,
                Pedido.id_ficha,
                Pedido.id_status
            )
            .filter(Pedido.seq_ficha.in_(SEQ_FICHAS))
        )
        df_infos = pd.read_sql(sql=query.statement, con=database.session.bind)

        df_final = pd.merge(
            df_exporta_dados,
            df_infos,
            how='left',
            left_on='SEQUENCIAFICHA',
            right_on='seq_ficha'
        )
        return df_final

    @staticmethod
    def _atualizar_tags_finais(df_exporta_dados: pd.DataFrame) -> pd.DataFrame:
        query_status_finais = (
            database.session.query(Status.id_status)
            .filter(Status.finaliza_processo == True)
            .all()
        )

        STATUS_FINAIS: list[int] = [i.id_status for i in query_status_finais]
        STATUS_OK: StatusLiberacao = (
            database.session.query(StatusLiberacao)
            .filter(StatusLiberacao.nome_status_lib == 'OK')
            .first()
        )

        df_exporta_dados.loc[
            df_exporta_dados['id_status'].isin(STATUS_FINAIS),
            'id_status_lib'
        ] = STATUS_OK.id_status_lib
        
        return df_exporta_dados

    @classmethod
    def buscar_pedidos(
        self,
        id_grupos: int | list[int],
        cod_empresa_principal: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        id_status: int | None = None,
        id_status_rac: int | None = None,
        id_tag: int | None = None,
        id_empresa: int | None = None,
        id_unidade: int | None = None,
        id_prestador: int | None = None,
        seq_ficha: int | None = None,
        nome_funcionario: str | None = None,
        obs: str | None = None
    ) -> BaseQuery:
        filtros = []
        if id_grupos is not None:
            if id_grupos == 0:
                filtros.append(Grupo.id_grupo == None)
            elif isinstance(id_grupos, list):
                filtros.append(Grupo.id_grupo.in_(id_grupos))
            else:
                filtros.append(Grupo.id_grupo == id_grupos)
        if cod_empresa_principal:
            filtros.append(self.cod_empresa_principal == cod_empresa_principal)
        if data_inicio:
            filtros.append(self.data_ficha >= data_inicio)
        if data_fim:
            filtros.append(self.data_ficha <= data_fim)
        if id_empresa:
            filtros.append(self.id_empresa == id_empresa)
        if id_unidade:
            filtros.append(self.id_unidade == id_unidade)
        if id_prestador is not None:
            if id_prestador == 0:
                filtros.append(self.id_prestador == None)
            else:
                filtros.append(self.id_prestador == id_prestador)
        if nome_funcionario:
            filtros.append(self.nome_funcionario.like(f'%{nome_funcionario}%'))
        if seq_ficha:
            filtros.append(self.seq_ficha == seq_ficha)
        if id_status:
            filtros.append(self.id_status == id_status)
        if id_status_rac:
            filtros.append(self.id_status_rac == id_status_rac)
        if obs:
            filtros.append(self.obs.like(f'%{obs}%'))
        if id_tag:
            filtros.append(self.id_status_lib == id_tag)

        joins = [
            (
                grupo_empresa_prestador,
                and_(
                    self.id_empresa == grupo_empresa_prestador.c.id_empresa,
                    self.id_prestador == grupo_empresa_prestador.c.id_prestador
                )
            ),
            (Grupo, grupo_empresa_prestador.c.id_grupo == Grupo.id_grupo)
        ]

        query = (
            database.session.query(self)
            .outerjoin(*joins)
            .filter(*filtros)
            .order_by(Pedido.data_ficha.desc(), Pedido.nome_funcionario)
        )
        
        return query

    @staticmethod
    def handle_group_choice(choice: int | Literal['my_groups', 'all', 'null']):
        match choice:
            case 'my_groups':
                return [gp.id_grupo for gp in current_user.grupo]
            case 'all':
                return None
            case 'null':
                return 0
            case _:
                return int(choice)
    
    @classmethod
    def add_csv_cols(self, query: BaseQuery):
        cols = [
            TipoExame.nome_tipo_exame.label('tipo_exame'),
            Empresa.cod_empresa, Empresa.razao_social.label('empresa'),
            Unidade.cod_unidade, Unidade.nome_unidade.label('unidade'),
            Prestador.cod_prestador, Prestador.nome_prestador.label('prestador'),
            Status.nome_status.label('status_aso'), StatusRAC.nome_status.label('status_rac'),
            StatusLiberacao.nome_status_lib.label('tag'),
            Grupo.nome_grupo
        ]

        joins = [
            (TipoExame, Pedido.cod_tipo_exame == TipoExame.cod_tipo_exame),
            (Empresa, Pedido.id_empresa == Empresa.id_empresa),
            (Unidade, Pedido.id_unidade == Unidade.id_unidade),
            (Prestador, Pedido.id_prestador == Prestador.id_prestador),
            (Status, Pedido.id_status == Status.id_status),
            (StatusRAC, Pedido.id_status_rac == StatusRAC.id_status),
            (StatusLiberacao, Pedido.id_status_lib == StatusLiberacao.id_status_lib)
        ]

        query = query.outerjoin(*joins)
        query = query.add_columns(*cols)

        return query

    @staticmethod
    def get_total_busca(query: BaseQuery) -> int:
        fichas = [i.id_ficha for i in query.all()]
        fichas = dict.fromkeys(fichas)
        return len(fichas)

