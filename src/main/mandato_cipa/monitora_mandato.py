from datetime import date, datetime
from mimetypes import guess_type

import numpy as np
import pandas as pd
from flask_mail import Attachment, Message
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER, app
from src.email_connect import EmailConnect
from src.extensions import database, mail

from ..empresa.empresa import Empresa
from ..unidade.unidade import Unidade
from .mandato import Mandato


class MonitoraMandato(Mandato):
    def __init__(self) -> None:
        pass

    @classmethod
    def rotina_monitorar_mandatos(
        self,
        id_empresa: int,
        data_inicio: date,
        data_fim: date,
        mandatos_ativos: bool = True,
        dias_ate_vencimento: int = 90,
        cod_unidade: str | None = None
    ):
        '''
            Funçao main.
            Coleta dados do Exporta Dados, trata, gera indicadodes e envia para
            o email da Empresa/Unidade.
        '''
        infos = {'ok': True, 'erro': None}

        email_conf = self.__sub_rotina_email_configs(id_empresa=id_empresa, cod_unidade=cod_unidade)

        if not email_conf:
            infos['ok'] = False
            infos['erro'] = 'Sem Email cadastrado para Mandatos CIPA'
            return infos

        df = self.__sub_rotina_dados_mandatos(
            id_empresa=id_empresa,
            cod_unidade=cod_unidade,
            data_inicio=data_inicio,
            data_fim=data_fim,
            mandato_ativo=mandatos_ativos
        )

        if df is None or df.empty:
            infos['ok'] = False
            infos['erro'] = 'Sem dados/tabela vazia'
            return infos

        # find errors
        df_erros = self.gerar_df_erros(df=df)
        df_vencimentos = self.gerar_df_vencimentos(df=df, dias_limite=dias_ate_vencimento)

        if df_erros.empty and df_vencimentos.empty:
            infos['ok'] = False
            infos['erro'] = 'Nenhum Erro ou Vencimento para alertar'
            return infos

        tabelas_excel: list[tuple[str, pd.DataFrame]] = []
        indicadores_inline: dict[str, any] = {}

        if not df_erros.empty:
            # NOTE: gerar indicadores antes de passar o df pelo tratamento final

            # indicador
            indicadores_inline['pendencias'] = ('Pendencias', self.__sub_rotina_indicadores_erros(df=df_erros))

            # aba excel
            df_erros_final = self.__tratamento_final_erros(id_empresa=id_empresa, df=df_erros)
            tabelas_excel.append(('Pendencias', df_erros_final))

        if not df_vencimentos.empty:
            # indicador
            indicadores_inline['vencimentos'] = ('Vencimentos', len(df_vencimentos), dias_ate_vencimento)

            # aba excel
            df_vencimentos_final = self.__tratamento_final_vencimentos(df=df_vencimentos, id_empresa=id_empresa)
            tabelas_excel.append(('Vencimentos', df_vencimentos_final))

        # prepare email message
        msg = self.__sub_rotina_email_message(
            indicadores_inline=indicadores_inline,
            tabelas_excel=tabelas_excel,
            email_configs=email_conf
        )

        try:
            mail.send(msg)
        except:
            infos['ok'] = False
            infos['erro'] = 'Erro ao enviar o email'

        return infos

    @staticmethod
    def __sub_rotina_email_configs(id_empresa: int, cod_unidade: str | None = None):
        '''
            Prepara configurações para o envio de email para a Empresa/Unidade

            Retorna None se a Empresa/Unidade não tiver emails cadastrados para Mandatos Cipa
        '''
        conf = {}

        if cod_unidade:
            UNIDADE: Unidade = (
                database.session.query(Unidade)
                .filter(Unidade.id_empresa == id_empresa)
                .filter(Unidade.cod_unidade == cod_unidade)
                .first()
            )
            conf['destinatarios_email']: list[str] = UNIDADE.mandatos_cipa_emails
            conf['nome_arquivos']: str = secure_filename(UNIDADE.nome_unidade).replace('.', '_').upper()
            conf['assunto_email']: str = f'Monitoramento CIPA - {UNIDADE.nome_unidade}'
        else:
            EMPRESA: Empresa = Empresa.query.get(id_empresa)
            conf['destinatarios_email']: list[str] = EMPRESA.mandatos_cipa_emails
            conf['nome_arquivos']: str = secure_filename(EMPRESA.razao_social).replace('.', '_').upper()
            conf['assunto_email']: str = f'Monitoramento CIPA - {EMPRESA.razao_social}'

        if not conf.get('destinatarios_email'):
            return None
        else:
            # emails must be list of str even if just one
            conf['destinatarios_email'] = conf['destinatarios_email'].split(';')

        return conf

    @classmethod
    def __sub_rotina_dados_mandatos(
        self,
        id_empresa: int,
        data_inicio: date,
        data_fim: date,
        mandato_ativo: bool,
        cod_unidade: str | None = None
    ):
        '''
            Coleta mandatos, trata e filtra de acordo com unidade, se houver

            remove duplicidades em cod_mandato + cod_funcionario

            Retorna None se não hover dados
        '''
        EMPRESA: Empresa = Empresa.query.get(id_empresa)

        dados_json = self.get_dados_json_periodo(
            id_empresa=id_empresa,
            data_inicio=data_inicio,
            data_fim=data_fim,
            mandato_ativo=mandato_ativo
        )

        if not dados_json:
            return None

        # get dataframe
        df = pd.DataFrame(data=dados_json)

        if cod_unidade:
            # filtrar unidade o mais cedo possivel
            df = df[df['CODIGOUNIDADE'] == cod_unidade]

        if df.empty:
            return None

        df = self.tratar_df(
            df=df,
            id_empresa=id_empresa,
            cod_empresa_principal=EMPRESA.cod_empresa_principal,
            mandato_ativo=mandato_ativo
        )

        # NOTE: os funcionarios podem aparecer duplicados em seus mandatos
        df.drop_duplicates(subset=['cod_mandato', 'cod_funcionario'], inplace=True, ignore_index=True)

        if df.empty:
            return None

        return df

    @classmethod
    def __sub_rotina_indicadores_erros(self, df: pd.DataFrame) -> pd.DataFrame:
        indicadores = {}

        conf_ind = [
            (['cod_mandato', 'cod_funcionario'], 'erros_funcionario'),
            (['cod_mandato'], 'erros_mandato')
        ]

        for keys, patt in conf_ind:
            ind_aux = self.get_indicadores(
                df=df,
                key_cols=keys,
                data_cols=self.__get_cols(df=df, pattern=patt)
            )
            indicadores.update(ind_aux)

        indicadores = pd.Series(indicadores).sort_values(ascending=False)
        indicadores = indicadores.to_frame().reset_index()
        indicadores.rename(columns={'index': 'Descrição', 0: 'Qtd'}, inplace=True)

        return indicadores

    @classmethod
    def __sub_rotina_email_message(
        self,
        indicadores_inline: list[tuple[str, any]],
        tabelas_excel: list[tuple[str, pd.DataFrame]],
        email_configs: dict
    ) -> Message:
        '''
            Args:
                indicadores_inline (list[tuple[str, any]]): lista de tuplas (nome_indicados, dados)
                tabelas_excel (list[tuple[str, pd.DataFrame]]): lista de tuplas (nome_aba, dataframe)
        '''
        # attach signature as inline image
        assinatura = EmailConnect.get_assinatura_attachment()
        anexos: list[Attachment] = [assinatura]

        # set up email body configs
        body_params = {
            'template_path': 'src/email_templates/erros_mandatos_cipa.html',
            'cid_assinatura': assinatura.cid
        }

        # adicionar indicadores inline
        body_params.update(indicadores_inline)

        # render email body
        email_body = EmailConnect.render_email_body(**body_params)

        # add tables as excel attachment
        arquivo_path = self.gerar_excel(dfs=tabelas_excel, nome=email_configs.get('nome_arquivos'))

        arquivo = Attachment(
            filename=arquivo_path.split('/')[-1],
            content_type=guess_type(arquivo_path)[0],
            data=app.open_resource(arquivo_path).read()
        )

        anexos.append(arquivo)

        # make email Message
        msg = Message(
            subject=email_configs.get('assunto_email'),
            recipients=email_configs.get('destinatarios_email'),
            html=email_body,
            attachments=anexos
        )

        return msg

    @classmethod
    def get_indicadores(
        self,
        df: pd.DataFrame,
        key_cols: list[str],
        data_cols: list[str],
    ) -> dict[str, any]:
        '''
            realiza pd.Series.value_counts() em todas as colunas indicadas

            ignora valores vazios ou = 0

            ignora duplicidades baseado nas key_cols
        '''
        indicadores = {}

        aux = df[key_cols + data_cols]
        aux = aux.drop_duplicates(subset=key_cols)

        for col in data_cols:
            ind = aux[col].value_counts().items()
            for key, val in ind:
                if key and val > 0:
                    indicadores[key] = val

        return indicadores

    @classmethod
    def gerar_excel(self, dfs: list[tuple[str, pd.DataFrame]], nome: str):
        '''
            Args:
                dfs: lista de tuplas > (nome da aba, DataFrame)
                nome: nome da empresa/unidade (str)
        '''
        nome = 'MANDATOS_CIPA_' + nome.upper()
        nome = secure_filename(nome).replace('.', '_')

        timestamp = int(datetime.now().timestamp())

        nome_arquivo = f'{UPLOAD_FOLDER}/{nome}_{timestamp}.xlsx'
        with pd.ExcelWriter(path=nome_arquivo, engine='xlsxwriter') as writer:
            for nome_aba, df in dfs:
                df.to_excel(
                    excel_writer=writer,
                    sheet_name=nome_aba,
                    index=False,
                    freeze_panes=(1,0)
                )
                self.__adjust_cols_width(writer=writer, sheet_name=nome_aba,df=df)

        return nome_arquivo

    @staticmethod
    def __adjust_cols_width(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame):
        for column in df.columns:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets[sheet_name].set_column(col_idx, col_idx, column_width)
        return None

    @classmethod
    def __tratamento_final_erros(self, id_empresa: int, df: pd.DataFrame):
        '''
            Tratamento final para o df de erros.

            seleciona e renomeia cols, insere nomes das entidades
        '''
        COLS = {
            'cod_mandato': 'Codigo Mandato',
            'cod_empresa': 'Codigo Empresa',
            'nome_empresa': 'Nome Empresa',
            'cod_unidade': 'Codigo Unidade',
            'nome_unidade': 'Nome Unidade',
            'cod_funcionario': 'Codigo Funcionario',
            'nome_funcionario': 'Nome Funcionario',
            'erros_main_funcionario': 'Pendencias Funcionário',
            'erros_main_mandato': 'Pendencias Mandato'
        }

        df = df.copy()
        empresa = Empresa.query.get(id_empresa)

        df['cod_empresa'] = empresa.cod_empresa
        df['nome_empresa'] = empresa.razao_social

        df = self.__get_nomes_unidades(id_empresa=id_empresa, df=df)

        df = df[list(COLS.keys())]
        df.rename(columns=COLS, inplace=True)

        return df

    @classmethod
    def __tratamento_final_vencimentos(self, df: pd.DataFrame, id_empresa: int):
        '''
            Seleciona e renomeia colunas

            Insere nomes das entidates
        '''
        COLS = {
            'cod_mandato': 'Codigo Mandato',
            'cod_empresa': 'Codigo Empresa',
            'nome_empresa': 'Nome Empresa',
            'cod_unidade': 'Codigo Unidade',
            'nome_unidade': 'Nome Unidade',
            'data_fim_mandato': 'Data Fim Mandato',
            'status_venc_mandato': 'Aviso'
        }

        df = df.copy()
        empresa = Empresa.query.get(id_empresa)

        df['cod_empresa'] = empresa.cod_empresa
        df['nome_empresa'] = empresa.razao_social

        df['data_fim_mandato'] = pd.to_datetime(df['data_fim_mandato'])
        df['data_fim_mandato'] = df['data_fim_mandato'].dt.strftime('%d/%m/%Y')

        df = self.__get_nomes_unidades(id_empresa=id_empresa, df=df)

        df = df[list(COLS.keys())]
        df.rename(columns=COLS, inplace=True)

        return df

    @staticmethod
    def __get_nomes_unidades(id_empresa: int, df: pd.DataFrame):
        '''
        realiza query na db e insere col nome_unidade

        cols merge: id_empresa, cod_unidade
        '''
        df = df.copy()

        cod_unidades = df['cod_unidade'].drop_duplicates().tolist()
        unidades = (
            database.session.query(Unidade.cod_unidade, Unidade.nome_unidade)
            .filter(Unidade.id_empresa == id_empresa)
            .filter(Unidade.cod_unidade.in_(cod_unidades))
        )

        df_unidades = pd.read_sql(sql=unidades.statement, con=database.session.bind)

        df = df.merge(
            right=df_unidades,
            how='left',
            on='cod_unidade'
        )
        return df

    @classmethod
    def gerar_df_erros(self, df: pd.DataFrame):
        '''
            trata de e gera todas as cols de erro

            remove linhas que não possuem nenhum erro
        '''
        df = df.copy()

        df = self.__checar_erros(df=df)

        # remove rows without any errors
        df = df[
            (df['erros_main_funcionario'].notna()) |
            (df['erros_main_mandato'].notna())
        ]

        df.sort_values(by='erros_main_funcionario', ascending=False, inplace=True, ignore_index=True)

        return df

    @classmethod
    def __checar_erros(self, df: pd.DataFrame):
        '''gera todas as colunas de erro'''
        df = self.__membro_ativo(df=df)
        df = self.__erros_funcao(df=df)
        df = self.__erros_situacao(df=df)
        df = self.__erros_eleicao(df=df)
        df = self.__erros_membros(df=df)
        df = self.__get_main_err_cols(df=df)
        return df

    @staticmethod
    def __membro_ativo(df: pd.DataFrame):
        '''gera coluna membro_ativo'''
        df = df.copy()

        condicoes = (
            (df['funcionario_renunciou'] == True),
            (df['funcionario_eleito'] == True),
            (df['tipo_representacao'] == 'Empregador')
        )

        valores = (False, True, True)

        df['membro_ativo'] = np.select(
            condlist=condicoes,
            choicelist=valores,
            default=False
        )

        return df

    @staticmethod
    def __erros_funcao(df: pd.DataFrame, msg_erro: str = 'Candidato sem Função definida'):
        '''gera coluna erros_funcionario_funcao'''
        df = df.copy()

        df['erros_funcionario_funcao'] = np.where(df['funcao'].isna(), msg_erro, None)  # type: ignore

        return df

    @staticmethod
    def __erros_situacao(df: pd.DataFrame, msg_erro: str = 'Candidato sem definição de Titular/Suplente'):
        '''gera coluna erros_funcionario_situacao'''
        df = df.copy()

        df['erros_funcionario_situacao'] = np.where(df['tipo_situacao'].isna(), msg_erro, None)  # type: ignore

        return df

    @staticmethod
    def __erros_eleicao(df: pd.DataFrame, msg_erro: str = 'Eleição em sem Data Final'):
        '''gera coluna erros_mandato_eleicao'''
        df = df.copy()

        df['erros_mandato_eleicao'] = np.where(df['data_eleicao'].isna(), msg_erro, None)  # type: ignore

        return df

    @staticmethod
    def __erros_membros(df: pd.DataFrame, msg_erro: str = 'Mandato sem eleitos'):
        '''gera coluna possui_membros'''
        df = df.copy()

        df_membros = df[['cod_mandato', 'membro_ativo']]

        df_membros = df_membros.loc[df_membros['membro_ativo'] == True]

        df_membros.drop_duplicates(subset='cod_mandato', inplace=True)

        df_membros['possui_membros'] = True

        df_membros = df_membros[['cod_mandato', 'possui_membros']]

        df = df.merge(
            right=df_membros,
            how='left',
            on='cod_mandato'
        )

        df['possui_membros'].fillna(value=False, inplace=True)

        df['erros_mandato_membros'] = np.where(df['possui_membros'] == False, msg_erro, None)  # type: ignore

        return df

    @classmethod
    def __get_main_err_cols(self, df: pd.DataFrame):
        '''
            concatena todas as colunas de erro em suas respectivas colunas finais

            gera cols: erros_main_funcionario, erros_main_mandato
        '''
        df = df.copy()

        cols_chave = ['cod_mandato', 'cod_funcionario']
        cols_err_func = self.__get_cols(df=df, pattern='erros_funcionario')
        cols_err_mand = self.__get_cols(df=df, pattern='erros_mandato')

        conf = [
            (cols_err_func, 'erros_main_funcionario'),
            (cols_err_mand, 'erros_main_mandato')
        ]

        for cols, col_final in conf:
            df = self.__join_err_cols(
                df=df,
                err_cols=cols,
                key_cols=cols_chave,
                final_col_name=col_final
            )

        return df

    @staticmethod
    def __join_err_cols(
        df: pd.DataFrame,
        err_cols: list[str],
        key_cols: list[str],
        final_col_name: str
    ):
        '''concatena as colunas de erro em uma coluna final'''
        df_aux = df.copy()

        df_aux = df_aux[key_cols + err_cols]

        for col in err_cols:
            df_aux[col] = df_aux[col].astype(str)

        df_aux[final_col_name] = df_aux[err_cols].apply(';'.join, axis=1)

        df_aux[final_col_name] = df_aux[final_col_name].str.replace('None;', '')
        df_aux[final_col_name] = df_aux[final_col_name].str.replace(';None', '')
        df_aux[final_col_name] = df_aux[final_col_name].replace('None', None)

        df_aux = df_aux[key_cols + [final_col_name]]

        df = df.merge(
            right=df_aux,
            how='left',
            on=key_cols,
        )

        return df

    @staticmethod
    def __get_cols(df: pd.DataFrame, pattern: str):
        '''get df cols based on pattern for cols name'''
        cols = []
        for col in df.columns:
            if pattern in col:
                cols.append(col)
        return cols

    @classmethod
    def gerar_df_vencimentos(self, df: pd.DataFrame, dias_limite: int):
        df = df.copy()

        df.drop_duplicates('cod_mandato', inplace=True, ignore_index=True)

        df = self.__dias_vencimento_mandatos(df=df)

        df = df[df['dias_vencimento'].notna()]
        df = df[df['dias_vencimento'] >= 0]
        df = df[df['dias_vencimento'] <= dias_limite]

        df.sort_values(by='dias_vencimento', ascending=True, inplace=True, ignore_index=True)

        return df

    @classmethod
    def __dias_vencimento_mandatos(self, df: pd.DataFrame):
        df = df.copy()

        hoje = datetime.now().date()

        df['data_fim_mandato'] = pd.to_datetime(df['data_fim_mandato']).dt.date

        df['dias_vencimento'] = (df['data_fim_mandato'] - hoje).dt.days

        df['status_venc_mandato'] = df['dias_vencimento'].apply(self.__gerar_status_venc)

        return df

    @staticmethod
    def __gerar_status_venc(dias_venc: int):
        match dias_venc:
            case 0:
                return 'Mandato vencerá hoje'
            case 1:
                return 'Mandato vencerá amanhã'
            case _:
                return f'Mandato vencerá em {dias_venc} dias'

