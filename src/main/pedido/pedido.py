from datetime import date, datetime
from typing import Literal

from flask_login import current_user
from flask_sqlalchemy import BaseQuery
from pytz import timezone
from sqlalchemy import and_

from src import database

from ..empresa.empresa import Empresa
from ..grupo.grupo import Grupo, grupo_empresa_prestador
from ..prestador.prestador import Prestador
from ..status.status import Status
from ..status.status_lib import StatusLiberacao
from ..status.status_rac import StatusRAC
from ..tipo_exame.tipo_exame import TipoExame
from ..unidade.unidade import Unidade
from .__carregar_pedidos import CarregarPedidos


class Pedido(database.Model, CarregarPedidos):
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

    last_server_update = database.Column(database.DateTime)

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
        if id_unidade:
            filtros.append(self.id_unidade == id_unidade)
        if id_prestador is not None:
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

