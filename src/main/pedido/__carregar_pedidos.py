from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from workalendar.america import Brazil

from src import TIMEZONE_SAO_PAULO, database
from src.soc_web_service.exporta_dados import ExportaDados

from ..empresa.empresa import Empresa
from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..exame.exame import Exame
from ..job.job_infos import JobInfos
from ..prestador.prestador import Prestador
from ..status.status import Status
from ..status.status_lib import StatusLiberacao
from ..unidade.unidade import Unidade


class CarregarPedidos:
    '''
        Helper class para operações de inserir e atualizar Pedidos

        Não deve ser usada diretamente
    '''
    @classmethod
    def carregar_pedidos(
        self,
        id_empresa: int,
        dataInicio: date,
        dataFim: date
    ) -> JobInfos:
        """Coleta Pedidos da Empresa no período selecionado, insere Pedidos novos \
            e Atualiza os já existentes.

        Args:
            dataInicio (str): dd/mm/yyyy
            dataFim (str): dd/mm/yyyy

        Returns:
            JobInfos: Dataclass com informações sobre o carregamento
        """
        ex = ExportaDados(
            wsdl_filename='prod/ExportaDadosWs.xml',
            exporta_dados_keys_filename='grs.json'
        )

        EMPRESA: Empresa = Empresa.query.get(id_empresa)
        EMPRESA_PRINCIPAL: EmpresaPrincipal = (
            EmpresaPrincipal.query.get(EMPRESA.cod_empresa_principal)
        )

        PARAMETRO = ex.pedido_exame(
            empresa=EMPRESA.cod_empresa,
            codigo=ex.EXPORTA_DADOS_KEYS.get('PEDIDO_EXAMES_COD'),
            chave=ex.EXPORTA_DADOS_KEYS.get('PEDIDO_EXAMES_KEY'),
            dataInicio=dataInicio,
            dataFim=dataFim
        )

        infos = JobInfos(
            tabela=self.__tablename__,
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            id_empresa=EMPRESA.id_empresa,
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
            cod_empresa_principal=EMPRESA_PRINCIPAL.cod,
            id_empresa=EMPRESA.id_empresa
        )

        # NOTE: passar cópia para que o df original não seja modificado
        infos = self.__inserir_pedidos(df=df.copy(), infos=infos)
        infos = self.__atualizar_pedidos(df=df.copy(), infos=infos)

        return infos

    @classmethod
    def __tratar_df_exporta_dados(
        self,
        df: pd.DataFrame,
        cod_empresa_principal: int,
        id_empresa: int
    ):
        COLS = {
            'SEQUENCIAFICHA': 'seq_ficha',
            'CODIGOFUNCIONARIO': 'cod_funcionario',
            'CPFFUNCIONARIO': 'cpf',
            'NOMEFUNCIONARIO': 'nome_funcionario',
            'DATAFICHA': 'data_ficha',
            'CODIGOINTERNOEXAME': 'cod_exame',
            'CODIGOTIPOEXAME': 'cod_tipo_exame',
            'CODIGOPRESTADOR': 'cod_prestador',
            'CODIGOEMPRESA': 'cod_empresa',
            'CODIGOUNIDADE': 'cod_unidade'
        }

        df = df[list(COLS.keys())]
        df = df.replace({'': None})
        df.rename(columns=COLS, inplace=True)

        for col in [
            'seq_ficha',
            'cod_funcionario',
            'cod_tipo_exame',
            # 'CODIGOPRESTADOR',
            'cod_empresa'
        ]:
            df[col] = df[col].astype(int)

        df['id_empresa'] = id_empresa
        df['cod_empresa_principal'] = cod_empresa_principal

        df = self.__buscar_infos_pedidos(df=df)

        df = self.__buscar_infos_exames(df=df, cod_empresa_principal=cod_empresa_principal)

        # NOTE: remover pedidos cuja unidade ainda não existe na db
        df = self.__buscar_infos_unidades(df=df, id_empresa=id_empresa)
        df.dropna(axis=0, subset='id_unidade', inplace=True)

        df = self.__buscar_infos_prestadores(df=df, cod_empresa_principal=cod_empresa_principal)

        df = self.__buscar_prestador_final(df=df)

        df = self.__gerar_prev_liberacao(df=df)

        df = self.__resetar_nao_compareceu(df=df)

        df = self.__gerar_tags(df=df)

        df = self.__selecionar_colunas_finais(df=df)

        return df

    @classmethod
    def __buscar_infos_pedidos(self, df: pd.DataFrame):
        '''Busca id_ficha e id_status'''
        SEQ_FICHAS: pd.Series[int] = df['seq_ficha'].drop_duplicates().astype(int)
        
        query = (
            database.session.query(
                self.id_ficha,
                self.seq_ficha,
                self.data_ficha.label('data_ficha_anterior'),
                self.id_status.label('id_status_anterior')
            )
            .filter(self.seq_ficha.in_(SEQ_FICHAS))
        )
        df_infos = pd.read_sql(sql=query.statement, con=database.session.bind)

        df = df.merge(
            right=df_infos,
            how='left',
            on='seq_ficha'
        )
        return df

    @staticmethod
    def __buscar_infos_exames(df: pd.DataFrame, cod_empresa_principal: int):
        '''Busca id_exame e prazo'''
        query = (
            database.session.query(
                Exame.id_exame,
                Exame.cod_exame,
                Exame.prazo
            )
            .filter(Exame.cod_empresa_principal == cod_empresa_principal)
        )
        df_db = pd.read_sql(sql=query.statement, con=database.session.bind)
        
        df = df.merge(
            right=df_db,
            how='left',
            on='cod_exame'
        )
        return df

    @staticmethod
    def __buscar_infos_unidades(df: pd.DataFrame, id_empresa: int):
        '''Busca id da unidade'''
        query = (
            database.session.query(
                Unidade.id_unidade,
                Unidade.cod_unidade
            )
            .filter(Unidade.id_empresa == id_empresa)
        )
        df_db = pd.read_sql(sql=query.statement, con=database.session.bind)

        df = df.merge(
            right=df_db,
            how='left',
            on='cod_unidade'
        )
        return df

    @staticmethod
    def __buscar_infos_prestadores(df: pd.DataFrame, cod_empresa_principal: int):
        '''Busca id_prestador'''
        query = (
            database.session.query(
                Prestador.id_prestador,
                Prestador.cod_prestador
            )
            .filter(Prestador.cod_empresa_principal == cod_empresa_principal)
        )
        df_db = pd.read_sql(sql=query.statement, con=database.session.bind)

        # NOTE: adicionar uma linha Nan no df db para nao travar o \
        # merge quando o prestador estiver vazio no df_exporta_dados
        df_db = pd.concat(
            [df_db, pd.DataFrame({'id_prestador': [None], 'cod_prestador': [None]})],
            axis=0,
            ignore_index=True
        )
        df_db = df_db.astype('Int32')

        df['cod_prestador'] = df['cod_prestador'].astype('Int32')

        df = df.merge(
            right=df_db,
            how='left',
            on='cod_prestador'
        )
        return df

    @staticmethod
    def __buscar_prestador_final(df: pd.DataFrame):
        """Busca prestadores dos exames com menor prazo. Geralmente é o clinico ou \
            outro exame do prestador que pegou o ASO por ultimo.
        """
        df['prazo'] = df['prazo'].fillna(0).astype(int)

        # prestadores principais (menor prazo)
        df_prestadores = df.sort_values(by='prazo', ascending=True).drop_duplicates('seq_ficha')
        df_prestadores = df_prestadores[['seq_ficha', 'id_prestador']]
        df_prestadores.rename(columns={'id_prestador': 'id_prestador_final'}, inplace=True)

        # prazos maximos
        df_prazos = df.sort_values(by='prazo', ascending=False)
        df_prazos.drop_duplicates('seq_ficha', inplace=True)

        df_final = pd.merge(
            left=df_prazos,
            right=df_prestadores,
            how='left',
            on='seq_ficha'
        )
        df_final.drop(labels='id_prestador', axis=1, inplace=True)
        df_final.rename(columns={'id_prestador_final': 'id_prestador'}, inplace=True)

        return df_final

    @staticmethod
    def __gerar_prev_liberacao(df: pd.DataFrame):
        '''Adiciona coluna prev_liberacao'''
        cal = Brazil() # usar workalendar
        
        df['data_ficha'] = pd.to_datetime(df['data_ficha'], dayfirst=True).dt.date
        df['prev_liberacao'] = list(
            map(
                cal.add_working_days, # adicionar dias uteis
                df['data_ficha'].values,
                df['prazo'].values
            )
        )
        return df

    @classmethod
    def __gerar_tags(self, df: pd.DataFrame):
        '''Adiciona coluna id_status_lib e calcula as tags de StatusLiberacao'''
        df['id_status_lib'] = 1

        # calcular tags
        df['id_status_lib'] = list(
            map(
                self.calcular_tag_prev_lib,
                df['prev_liberacao']
            )
        )

        df = self.__atualizar_tags_finais(df=df)

        return df

    @staticmethod
    def __atualizar_tags_finais(df: pd.DataFrame):
        '''
            Atualiza tag StatusLiberacao para OK onde o Status do ASO \
            for marcado como finaliza_processo = True
        '''
        query = (
            database.session.query(Status.id_status)
            .filter(Status.finaliza_processo == True)
            .all()
        )

        STATUS_FINAIS: list[int] = [i.id_status for i in query]

        STATUS_OK: StatusLiberacao = (
            database.session.query(StatusLiberacao)
            .filter(StatusLiberacao.nome_status_lib == 'OK')
            .first()
        )

        df.loc[df['id_status'].isin(STATUS_FINAIS), 'id_status_lib'] = STATUS_OK.id_status_lib
        
        return df

    @classmethod
    def __selecionar_colunas_finais(self, df: pd.DataFrame):
        cols_db = [col.name for col in inspect(self).c]

        cols_df = list(dict.fromkeys([col for col in df.columns if col in cols_db]))

        df = df[cols_df]

        return df

    @classmethod
    def __inserir_pedidos(self, df: pd.DataFrame, infos: JobInfos):
        # manter apenas pedidos sem id (novos)
        df = df[df['id_ficha'].isna()].copy()

        if df.empty:
            infos.qtd_inseridos = 0
            infos.add_error(error='df vazio ao inserir')
            return infos

        df['id_status'] = 1 # Vazio
        df['data_inclusao'] = datetime.now(tz=TIMEZONE_SAO_PAULO)
        df['incluido_por'] = 'Servidor'

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
    def __atualizar_pedidos(self, df: pd.DataFrame, infos: JobInfos):
        # manter apenas pedidos com id validos (ja existem)
        df = df[df['id_ficha'].notna()].copy()

        if df.empty:
            infos.qtd_atualizados = 0
            infos.add_error(error='df vazio ao atualizar')
            return infos

        df['last_server_update'] = datetime.now(TIMEZONE_SAO_PAULO)

        # remover colunas que nao mudam
        df.drop(
            columns='seq_ficha',
            inplace=True
        )

        # NOTE: fazer isso para evitar que df_mappings contenha 'np.nan'
        # esse valor nao é aceito em databases
        df['id_prestador'] = df['id_prestador'].astype(object)
        df['id_prestador'] = df['id_prestador'].replace(np.nan, None)

        df_mappings = df.to_dict(orient='records')

        try:
            database.session.bulk_update_mappings(self, df_mappings)
            database.session.commit()
            infos.qtd_atualizados = len(df_mappings)
        except IntegrityError:
            infos.ok = False
            infos.add_error(error='IntegrityError ao atualizar')

        return infos

    @classmethod
    def __resetar_nao_compareceu(self, df: pd.DataFrame):
        '''
            Reseta Status dos Pedidos de "Não compareceu" se houver mudança \
            em data_ficha.
        '''
        NAO_COMP: Status = Status.query.filter_by(nome_status='Não compareceu').first()
        VAZIO: Status = Status.query.filter_by(nome_status='Vazio').first()

        df['data_ficha'] = pd.to_datetime(df['data_ficha'], dayfirst=True).dt.date

        df['id_status'] = df['id_status_anterior']

        df.loc[
            (df['id_status_anterior'] == NAO_COMP.id_status) &
            (df['data_ficha_anterior'] != df['data_ficha']),
            'id_status'
        ] = VAZIO.id_status

        return df

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

        # NOTE: neste caso, entenda self como a classe Pedido
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
            (self.prev_liberacao == None, 1),
            (self.prev_liberacao < hoje, 5),
            (self.prev_liberacao > hoje, 4),
            (self.prev_liberacao.in_(datas_solicitar), 3),
            (self.id_status.in_(finaliza_processo), 2)
        ]

        linhas_afetadas = 0
        # afeta as mesmas linhas varias vezes, \
        # pode gerar numero maior do que o total de linhas na tabela

        for par, tag in parametros:
            q = database.session.execute(
                update(self).
                where(par).
                values(id_status_lib=tag)
            )
            database.session.commit()

            linhas_afetadas = linhas_afetadas + q.rowcount
        
        return linhas_afetadas

