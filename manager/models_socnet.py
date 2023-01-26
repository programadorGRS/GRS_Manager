from io import StringIO

import pandas as pd
from flask_login import current_user

from manager import database
from manager.models import (Prestador, Status, StatusLiberacao, TipoExame,
                            grupo_prestador)

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
    prazo = database.Column(database.Integer, default=0)
    prev_liberacao = database.Column(database.Date)
    id_status_lib = database.Column(database.Integer, database.ForeignKey('StatusLiberacao.id_status_lib'), default=1, nullable=False)
    data_recebido = database.Column(database.Date)
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
        'prazo',
        'prev_liberacao',
        'data_recebido',
        'obs',
        'cod_funcionario',
        'cod_tipo_exame',
        'cod_prestador',
        'cod_empresa',
        'id_status',
        'data_inclusao',
        'data_alteracao',
        'incluido_por',
        'alterado_por',
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
        cod_empresa_principal: int,
        pesquisa_geral: bool=False,
        inicio: str=None,
        fim: str=None,
        status: int=None,
        # tag: int=None,
        empresa: int=None,
        # unidade: int=None,
        prestador: int=None,
        seq_ficha: int=None,
        nome: str=None,
        obs: str=None
    ):
        '''
        Realiza query filtrada pelos parametros passados

        Retorna BaseQuery com os pedidos filtrados ou com todos os pedidos
        '''
        models = [
            (PedidoSOCNET.id_ficha),
            (PedidoSOCNET.cod_empresa_principal), (PedidoSOCNET.seq_ficha), (PedidoSOCNET.data_ficha),
            (PedidoSOCNET.prazo), (PedidoSOCNET.prev_liberacao), (PedidoSOCNET.data_recebido),
            (PedidoSOCNET.obs), (PedidoSOCNET.data_inclusao), (PedidoSOCNET.data_alteracao),
            (PedidoSOCNET.incluido_por), (PedidoSOCNET.alterado_por), (PedidoSOCNET.cpf),
            (PedidoSOCNET.cod_funcionario), (PedidoSOCNET.nome_funcionario),
            (TipoExame.nome_tipo_exame), (TipoExame.cod_tipo_exame),
            (EmpresaSOCNET.cod_empresa), (EmpresaSOCNET.nome_empresa),
            (Prestador.cod_prestador), (Prestador.nome_prestador),
            (Status.id_status), (Status.nome_status),
            (StatusLiberacao.id_status_lib), (StatusLiberacao.nome_status_lib), (StatusLiberacao.cor_tag),            
        ]

        filtros = [(self.cod_empresa_principal == cod_empresa_principal)]
       
        joins = [
            (EmpresaSOCNET, PedidoSOCNET.id_empresa == EmpresaSOCNET.id_empresa),
            (Prestador, PedidoSOCNET.id_prestador == Prestador.id_prestador),
            (TipoExame, PedidoSOCNET.cod_tipo_exame == TipoExame.cod_tipo_exame),
            (Status, PedidoSOCNET.id_status == Status.id_status),
            (StatusLiberacao, PedidoSOCNET.id_status_lib == StatusLiberacao.id_status_lib)
        ]
        
        if inicio:
            filtros.append(self.data_ficha >= inicio)
        if fim:
            filtros.append(self.data_ficha <= fim)
        if empresa:
            filtros.append(self.id_empresa == empresa)
        # if unidade:
        #     filtros.append(self.id_unidade == unidade)
        if prestador != None:
            if prestador == 0:
                filtros.append(self.id_prestador == None)
            else:
                filtros.append(self.id_prestador == prestador)
        if nome:
            filtros.append(self.nome_funcionario.like(f'%{nome}%'))
        if seq_ficha:
            filtros.append(self.seq_ficha == seq_ficha)
        if status:
            filtros.append(self.id_status == status)
        if obs:
            filtros.append(self.obs.like(f'%{obs}%'))
        # if tag:
        #     filtros.append(self.id_status_lib == tag)
        
        if not pesquisa_geral:
            # grupos do usuario atual
            subquery_grupos = [grupo.id_grupo for grupo in current_user.grupo]

            joins.append((grupo_empresa_socnet, self.id_empresa == grupo_empresa_socnet.columns.id_empresa))
            joins.append((grupo_prestador, self.id_prestador == grupo_prestador.columns.id_prestador))
            filtros.append((grupo_prestador.columns.id_grupo.in_(subquery_grupos)))
            filtros.append((grupo_empresa_socnet.columns.id_grupo.in_(subquery_grupos)))

        query = (
            database.session.query(*models)
            .filter(*filtros)
            .outerjoin(*joins)
            .order_by(PedidoSOCNET.data_ficha, PedidoSOCNET.nome_funcionario)
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
        df['id_status_lib'] = 1

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
            'id_status',
            'id_status_lib'
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

