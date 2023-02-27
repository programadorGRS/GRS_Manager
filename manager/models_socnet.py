from datetime import date
from io import StringIO

import pandas as pd
from flask_login import current_user

from manager import database
from manager.models import (Prestador, Status, StatusLiberacao, StatusRAC,
                            TipoExame, grupo_prestador)

grupo_empresa_socnet = database.Table('grupo_empresa_socnet',
    database.Column('id_grupo', database.Integer, database.ForeignKey('Grupo.id_grupo')),
    database.Column('id_empresa', database.Integer, database.ForeignKey('EmpresaSOCNET.id_empresa'))
)


class EmpresaSOCNET(database.Model):
    '''
    Empresas que fazem referencia ao acesso SOCNET recebido pela EmpresaPrincipal

    Exemplo: 736956 - SYNGENTA (SOCNET), faz referencia a (PRINCIPAL/PARÂMETROS) SYNGENTA. \
    Ela nao e uma Empresa real e existe apenas na Base da GRS, portanto sua EmpresaPrincipal e \
    a GRS.
    '''
    __tablename__ = 'EmpresaSOCNET'
    id_empresa = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    # EmpresaPrincipal que essa EmpresaSOCNET esta referenciando 
    cod_empresa_referencia = database.Column(database.Integer, nullable=False)
    cod_empresa = database.Column(database.Integer, nullable=False)
    nome_empresa =  database.Column(database.String(255), nullable=False)
    emails = database.Column(database.String(500))
    ativo = database.Column(database.Boolean, nullable=False)
    
    pedidos = database.relationship('PedidoSOCNET', backref='empresa', lazy=True) # one to many
    grupo = database.relationship('Grupo', secondary=grupo_empresa_socnet, backref='empresas_socnet', lazy=True) # many to many
   
    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.cod_empresa}> {self.nome_empresa}'


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
    colunas_planilha = [
        'seq_ficha',
        'cpf',
        'nome_funcionario',
        'data_ficha',
        'nome_tipo_exame',
        'nome_prestador',
        'nome_empresa',
        'nome_status',
        'nome_status_rac',
        'cod_funcionario',
        'cod_tipo_exame',
        'cod_prestador',
        'cod_empresa',
        'data_inclusao',
        'data_alteracao',
        'incluido_por',
        'alterado_por',
        'id_ficha',
        'id_status',
        'id_status_rac',
        'data_recebido',
        'data_comparecimento',
        'obs'
    ]

    # colunas para a tabela enviada no email
    colunas_tab_email = [
        'seq_ficha',
        'cpf',
        'nome_funcionario',
        'data_ficha',
        'nome_tipo_exame',
        'nome_prestador',
        'nome_empresa',
    ]

    colunas_tab_email2 = [
        'Seq. Ficha',
        'CPF',
        'Nome Funcionário',
        'Data Ficha',
        'Tipo Exame',
        'Prestador',
        'Empresa',
    ]

    @classmethod
    def buscar_pedidos(
        self,
        pesquisa_geral:  int | None = None,
        cod_empresa_principal: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        id_status: int | None = None,
        id_status_rac: int | None = None,
        id_empresa: int | None = None,
        id_prestador: int | None = None,
        seq_ficha: int | None = None,
        nome_funcionario: str | None = None,
        obs: str | None = None
    ):
        '''
        Realiza query filtrada pelos parametros passados

        Retorna BaseQuery com os pedidos filtrados ou com todos os pedidos
        '''
        models = [
            (PedidoSOCNET.id_ficha),
            (PedidoSOCNET.cod_empresa_principal), (PedidoSOCNET.seq_ficha), (PedidoSOCNET.data_ficha),
            (PedidoSOCNET.data_recebido), (PedidoSOCNET.data_comparecimento),
            (PedidoSOCNET.obs), (PedidoSOCNET.data_inclusao), (PedidoSOCNET.data_alteracao),
            (PedidoSOCNET.incluido_por), (PedidoSOCNET.alterado_por), (PedidoSOCNET.cpf),
            (PedidoSOCNET.cod_funcionario), (PedidoSOCNET.nome_funcionario),
            (TipoExame.nome_tipo_exame), (TipoExame.cod_tipo_exame),
            (EmpresaSOCNET.cod_empresa), (EmpresaSOCNET.nome_empresa),
            (Prestador.cod_prestador), (Prestador.nome_prestador),
            (PedidoSOCNET.id_status), (Status.nome_status),
            (PedidoSOCNET.id_status_rac), (StatusRAC.nome_status.label('nome_status_rac'))
        ]

        joins = [
            (EmpresaSOCNET, PedidoSOCNET.id_empresa == EmpresaSOCNET.id_empresa),
            (Prestador, PedidoSOCNET.id_prestador == Prestador.id_prestador),
            (TipoExame, PedidoSOCNET.cod_tipo_exame == TipoExame.cod_tipo_exame),
            (Status, PedidoSOCNET.id_status == Status.id_status),
            (StatusRAC, PedidoSOCNET.id_status_rac == StatusRAC.id_status),
        ]
        
        filtros = []
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
        
        # se nao for pesquisa geral, usar grupos do usuario atual
        if not pesquisa_geral:
            subquery_grupos = [grupo.id_grupo for grupo in current_user.grupo]

            joins.append((grupo_empresa_socnet, self.id_empresa == grupo_empresa_socnet.columns.id_empresa))
            joins.append((grupo_prestador, self.id_prestador == grupo_prestador.columns.id_prestador))
            filtros.append((grupo_prestador.columns.id_grupo.in_(subquery_grupos)))
            filtros.append((grupo_empresa_socnet.columns.id_grupo.in_(subquery_grupos)))

        query = (
            database.session.query(*models)
            .filter(*filtros)
            .outerjoin(*joins)
            .order_by(PedidoSOCNET.data_ficha.desc(), PedidoSOCNET.nome_funcionario)
        )
        
        return query


    @classmethod
    def inserir_pedidos():
        pass
    
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

