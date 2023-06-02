from datetime import date
from io import StringIO
from typing import Literal

import pandas as pd
from flask_login import current_user
from flask_sqlalchemy import BaseQuery
from sqlalchemy import and_

from src import database

from ..empresa_socnet.empresa_socnet import EmpresaSOCNET
from ..grupo.grupo import Grupo, grupo_empresa_prestador_socnet
from ..prestador.prestador import Prestador
from ..status.status import Status
from ..status.status_rac import StatusRAC
from ..tipo_exame.tipo_exame import TipoExame


class PedidoSOCNET(database.Model):
    '''
    Pedidos de Exames adiquiridos atraves do front end do SOC em \
    Administracao > Rede Credenciada SOCNET > Relatorio de Exames SOCNET.

    Os dados sao diferentes dos Pedidos de Exames adquiridos via Exporta Dados, ja que nos Exporta Dados \
    o Prestador que aparece nao e o Prestador final do atendimento, mas o intermediario (GRS).
    '''
    __tablename__ = 'PedidoSOCNET'
    id_ficha = database.Column(database.Integer, primary_key=True)
    seq_ficha = database.Column(database.Integer, nullable=False)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod_empresa_referencia = database.Column(database.Integer, nullable=False)
    cod_funcionario = database.Column(database.Integer, nullable=False)
    cpf = database.Column(database.String(30))
    nome_funcionario = database.Column(database.String(150), nullable=False)
    data_ficha = database.Column(database.Date, nullable=False)
    cod_tipo_exame = database.Column(database.Integer, database.ForeignKey('TipoExame.cod_tipo_exame'), nullable=False)
    id_prestador = database.Column(database.Integer, database.ForeignKey('Prestador.id_prestador'))
    id_empresa = database.Column(database.Integer, database.ForeignKey('EmpresaSOCNET.id_empresa'), nullable=False)
    id_status = database.Column(database.Integer, database.ForeignKey('Status.id_status'), default=1, nullable=False)
    id_status_rac = database.Column(database.Integer, database.ForeignKey('StatusRAC.id_status'), default=1, nullable=False)
    data_recebido = database.Column(database.Date)
    data_comparecimento = database.Column(database.Date)
    obs = database.Column(database.String(255))

    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    # colunas para a planilha de pedidos
    COLS_CSV = [
        'cod_empresa_principal',
        'cod_empresa_referencia',
        'seq_ficha',
        'cod_funcionario',
        'nome_funcionario',
        'data_ficha',
        'tipo_exame',
        'cod_empresa',
        'empresa',
        'cod_prestador',
        'prestador',
        'status_aso',
        'status_rac',
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
        'nome_empresa': 'Empresa'
    }

    @classmethod
    def buscar_pedidos(
        self,
        id_grupos: int | list[int],
        cod_empresa_principal: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        id_status: int | None = None,
        id_status_rac: int | None = None,
        id_empresa: int | None = None,
        id_prestador: int | None = None,
        cod_tipo_exame: int | None = None,
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
        if id_prestador != None:
            if id_prestador == 0:
                filtros.append(self.id_prestador == None)
            else:
                filtros.append(self.id_prestador == id_prestador)
        if cod_tipo_exame:
            filtros.append(self.cod_tipo_exame == cod_tipo_exame)
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

        joins = [
            (
                grupo_empresa_prestador_socnet,
                and_(
                    self.id_empresa == grupo_empresa_prestador_socnet.c.id_empresa,
                    self.id_prestador == grupo_empresa_prestador_socnet.c.id_prestador
                )
            ),
            (Grupo, grupo_empresa_prestador_socnet.c.id_grupo == Grupo.id_grupo)
        ]

        query = (
            database.session.query(self)
            .outerjoin(*joins)
            .filter(*filtros)
            .order_by(PedidoSOCNET.data_ficha.desc(), PedidoSOCNET.nome_funcionario)
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
            EmpresaSOCNET.cod_empresa, EmpresaSOCNET.nome_empresa.label('empresa'),
            Prestador.cod_prestador, Prestador.nome_prestador.label('prestador'),
            Status.nome_status.label('status_aso'), StatusRAC.nome_status.label('status_rac'),
            Grupo.nome_grupo
        ]

        joins = [
            (TipoExame, self.cod_tipo_exame == TipoExame.cod_tipo_exame),
            (EmpresaSOCNET, self.id_empresa == EmpresaSOCNET.id_empresa),
            (Prestador, self.id_prestador == Prestador.id_prestador),
            (Status, self.id_status == Status.id_status),
            (StatusRAC, self.id_status_rac == StatusRAC.id_status)
        ]

        query = query.outerjoin(*joins)
        query = query.add_columns(*cols)

        return query

    @staticmethod
    def get_total_busca(query: BaseQuery) -> int:
        fichas = [i.id_ficha for i in query.all()]
        fichas = dict.fromkeys(fichas)
        return len(fichas)

    @staticmethod
    def tratar_pedidos_socnet(
        caminho_arqv: str = None,
        file_contents: str = None,
        header: int = 2,
        encoding: str = 'iso-8859-1',
        sep: str = ';'
    ):
        '''
        Recebe arquivo ou str csv e retorna df tratado para a tabela pedidos socnet

        - caminho_arqv: caminho para o arquivo csv
        - file_contents: string lido a partir do csv
        '''
        if caminho_arqv:
            # ler arquivo csv diretamente
            df = pd.read_csv(
                filepath_or_buffer=caminho_arqv,
                sep=sep,
                encoding=encoding,
                header=header
            )
        else:
            # ler string como objeto para csv
            df = pd.read_csv(
                filepath_or_buffer=StringIO(file_contents),
                sep=sep,
                encoding=encoding,
                header=header
            )

        print('Removendo Vazios...')
        df = df.replace(to_replace={'': None})
        df.dropna(
            axis=0,
            subset=['Sequencial Ficha', 'Código Funcionário', 'Código Empresa'],
            inplace=True
        )

        for col in ['Sequencial Ficha', 'Código Funcionário', 'Código Empresa']:
            df[col] = df[col].astype(int)

        print('Filtrando Empresas...')
        empresas = [int(empresa.cod_empresa) for empresa in EmpresaSOCNET.query.all()]
        df = df[df['Código Empresa'].isin(empresas)]

        # buscar cods dos tipos de exame
        df_tipos_exames = pd.read_sql(sql=TipoExame.query.statement, con=database.session.bind)
        df["Tipo de Exame"] = df["Tipo de Exame"].replace('Mudança de Função', 'Mudança de Riscos Ocupacionais')
        df = pd.merge(df, df_tipos_exames, how='left', left_on='Tipo de Exame', right_on='nome_tipo_exame')

        # tratar outras cols
        df['CPF'] = df['CPF'].astype('string').str.replace('[.-]', '', regex=True)
        df['Data Ficha'] = pd.to_datetime(df['Data Ficha'], dayfirst=True).dt.date

        # buscar ids
        df_database = pd.read_sql(
            sql=(
                database.session.query(
                    EmpresaSOCNET.id_empresa,
                    EmpresaSOCNET.cod_empresa,
                    EmpresaSOCNET.cod_empresa_principal,
                    EmpresaSOCNET.cod_empresa_referencia
                )
                .statement
            ),
            con=database.session.bind
        )

        df = df.merge(
            df_database,
            how='left',
            left_on='Código Empresa',
            right_on='cod_empresa'
        ) # pegar ids de: Empresa, EmpresaPrincipal

        df_database = pd.read_sql(
            sql=(
                database.session.query(
                    Prestador.id_prestador,
                    Prestador.cod_prestador
                )
                .statement
            ),
            con=database.session.bind
        )
        # adicionar uma linha Nan no df database para nao travar o merge quando o prestador \
        # estiver vazio no df_exporta_dados
        df_database = pd.concat(
            [df_database, pd.DataFrame({'id_prestador': [None], 'cod_prestador': [None]})],
            axis=0,
            ignore_index=True
        )
        df_database = df_database.astype('Int32')

        df['Código Prestador'] = df['Código Prestador'].astype('Int32')
        df = df.merge(
            df_database,
            how='left',
            left_on='Código Prestador',
            right_on='cod_prestador'
        ) # pegar ids de: Prestador

        df['id_status'] = 1

        df.rename(columns={
            'Sequencial Ficha': 'seq_ficha',
            'CPF': 'cpf',
            'Funcionario': 'nome_funcionario',
            'Código Funcionário': 'cod_funcionario',
            'Data Ficha': 'data_ficha'
        }, inplace=True)

        df = df[[
            'seq_ficha',
            'cod_empresa_principal',
            'cod_empresa_referencia',
            'cod_funcionario',
            'cpf',
            'nome_funcionario',
            'data_ficha',
            'cod_tipo_exame',
            'id_prestador',
            'id_empresa',
            'id_status'
        ]]

        df.drop_duplicates(subset='seq_ficha', inplace=True)

        # remover pedidos que ja existem
        pedidos = [
            i.seq_ficha
            for i in
            database.session.query(PedidoSOCNET.seq_ficha).all()
        ]

        df = df[~df['seq_ficha'].isin(pedidos)]

        return df
