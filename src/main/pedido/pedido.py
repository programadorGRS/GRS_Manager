from datetime import date, datetime
from typing import Literal

from flask_login import current_user
from flask_sqlalchemy import BaseQuery
from sqlalchemy import and_

from src import TIMEZONE_SAO_PAULO
from src.extensions import database as db

from ..empresa.empresa import Empresa
from ..grupo.grupo import Grupo, grupo_empresa_prestador
from ..prestador.prestador import Prestador
from ..status.status import Status
from ..status.status_lib import StatusLiberacao
from ..status.status_rac import StatusRAC
from ..tipo_exame.tipo_exame import TipoExame
from ..unidade.unidade import Unidade
from .__carregar_pedidos import CarregarPedidos


class Pedido(db.Model, CarregarPedidos):
    __tablename__ = "Pedido"

    id_ficha = db.Column(db.Integer, primary_key=True)

    cod_empresa_principal = db.Column(
        db.Integer, db.ForeignKey("EmpresaPrincipal.cod"), nullable=False
    )
    seq_ficha = db.Column(db.Integer, nullable=False, unique=True)
    cod_funcionario = db.Column(db.Integer, nullable=False)

    cpf = db.Column(db.String(30))
    nome_funcionario = db.Column(db.String(150))

    data_ficha = db.Column(db.Date, nullable=False)
    cod_tipo_exame = db.Column(
        db.Integer,
        db.ForeignKey("TipoExame.cod_tipo_exame"),
        nullable=False,
    )
    id_prestador = db.Column(db.Integer, db.ForeignKey("Prestador.id_prestador"))

    id_empresa = db.Column(
        db.Integer, db.ForeignKey("Empresa.id_empresa"), nullable=False
    )
    id_unidade = db.Column(
        db.Integer, db.ForeignKey("Unidade.id_unidade"), nullable=False
    )

    id_status = db.Column(
        db.Integer,
        db.ForeignKey("Status.id_status"),
        default=1,
        nullable=False,
    )
    id_status_rac = db.Column(
        db.Integer,
        db.ForeignKey("StatusRAC.id_status"),
        default=1,
        nullable=False,
    )

    prazo = db.Column(db.Integer, default=0)
    prev_liberacao = db.Column(db.Date)
    id_status_lib = db.Column(
        db.Integer,
        db.ForeignKey("StatusLiberacao.id_status_lib"),
        default=1,
        nullable=False,
    )

    data_recebido = db.Column(db.Date)
    data_comparecimento = db.Column(db.Date)
    obs = db.Column(db.String(255))

    data_inclusao = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now(tz=TIMEZONE_SAO_PAULO),
    )
    data_alteracao = db.Column(db.DateTime)
    incluido_por = db.Column(db.String(50))
    alterado_por = db.Column(db.String(50))

    last_server_update = db.Column(db.DateTime)

    # colunas para a planilha de pedidos
    COLS_CSV = [
        "cod_empresa_principal",
        "seq_ficha",
        "cod_funcionario",
        "nome_funcionario",
        "data_ficha",
        "tipo_exame",
        "cod_prestador",
        "prestador",
        "cod_empresa",
        "empresa",
        "cod_unidade",
        "unidade",
        "status_aso",
        "status_rac",
        "prev_liberacao",
        "tag",
        "nome_grupo",
        "id_ficha",
        "id_status",
        "id_status_rac",
        "data_recebido",
        "data_comparecimento",
        "obs",
    ]

    COLS_EMAIL = {
        "seq_ficha": "Seq. Ficha",
        "cpf": "CPF",
        "nome_funcionario": "Nome Funcionário",
        "data_ficha": "Data Ficha",
        "nome_tipo_exame": "Tipo Exame",
        "nome_prestador": "Prestador",
        "razao_social": "Empresa",
        "nome_status_lib": "Status",
    }

    @classmethod
    def buscar_pedidos(
        cls,
        id_grupos: int | list[int],
        cod_emp_princ: int | None = None,
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
        obs: str | None = None,
    ) -> BaseQuery:
        PARAMS = (
            (cod_emp_princ, (cls.cod_empresa_principal == cod_emp_princ)),
            (id_empresa, (cls.id_empresa == id_empresa)),
            (id_unidade, (cls.id_unidade == id_unidade)),
            (id_status, (cls.id_status == id_status)),
            (id_status_rac, (cls.id_status_rac == id_status_rac)),
            (id_tag, (cls.id_status_lib == id_tag)),
            (cod_tipo_exame, (cls.cod_tipo_exame == cod_tipo_exame)),
            (data_inicio, (cls.data_ficha >= data_inicio) if data_inicio else None),
            (data_fim, (cls.data_ficha <= data_fim) if data_fim else None),
            (seq_ficha, (cls.seq_ficha == seq_ficha)),
            (nome_funcionario, (cls.nome_funcionario.like(f"%{nome_funcionario}%"))),
            (obs, (cls.obs.like(f"%{obs}%"))),
        )

        filtros = []

        for par, fltr in PARAMS:
            if par:
                filtros.append(fltr)

        if id_grupos is not None:
            if id_grupos == 0:
                filtros.append(Grupo.id_grupo == None)  # noqa
            elif isinstance(id_grupos, list):
                filtros.append(Grupo.id_grupo.in_(id_grupos))
            else:
                filtros.append(Grupo.id_grupo == id_grupos)

        if id_prestador is not None:
            if id_prestador == 0:
                filtros.append(cls.id_prestador == None)  # noqa
            else:
                filtros.append(cls.id_prestador == id_prestador)

        joins = [
            (
                grupo_empresa_prestador,
                and_(
                    cls.id_empresa == grupo_empresa_prestador.c.id_empresa,
                    cls.id_prestador == grupo_empresa_prestador.c.id_prestador,
                ),
            ),
            (Grupo, grupo_empresa_prestador.c.id_grupo == Grupo.id_grupo),
        ]

        query = (
            db.session.query(cls)  # type: ignore
            .outerjoin(*joins)
            .filter(*filtros)
            .order_by(Pedido.data_ficha.desc(), Pedido.nome_funcionario)
        )

        return query

    @staticmethod
    def handle_group_choice(choice: int | Literal["my_groups", "all", "null"]):
        match choice:
            case "my_groups":
                return [gp.id_grupo for gp in current_user.grupo]  # type: ignore
            case "all":
                return None
            case "null":
                return 0
            case _:
                return int(choice)

    @classmethod
    def add_csv_cols(cls, query: BaseQuery):
        cols = [
            TipoExame.nome_tipo_exame.label("tipo_exame"),
            Empresa.cod_empresa,
            Empresa.razao_social.label("empresa"),
            Unidade.cod_unidade,
            Unidade.nome_unidade.label("unidade"),
            Prestador.cod_prestador,
            Prestador.nome_prestador.label("prestador"),
            Status.nome_status.label("status_aso"),
            StatusRAC.nome_status.label("status_rac"),
            StatusLiberacao.nome_status_lib.label("tag"),
            Grupo.nome_grupo,
        ]

        joins = [
            (TipoExame, Pedido.cod_tipo_exame == TipoExame.cod_tipo_exame),
            (Empresa, Pedido.id_empresa == Empresa.id_empresa),
            (Unidade, Pedido.id_unidade == Unidade.id_unidade),
            (Prestador, Pedido.id_prestador == Prestador.id_prestador),
            (Status, Pedido.id_status == Status.id_status),
            (StatusRAC, Pedido.id_status_rac == StatusRAC.id_status),
            (StatusLiberacao, Pedido.id_status_lib == StatusLiberacao.id_status_lib),
        ]

        query = query.outerjoin(*joins)
        query = query.add_columns(*cols)  # type: ignore

        return query

    @staticmethod
    def get_total_busca(query: BaseQuery) -> int:
        fichas = [i.id_ficha for i in query.all()]
        fichas = dict.fromkeys(fichas)
        return len(fichas)

    @classmethod
    def set_id_status(cls, id_ficha: int, id_status: int):
        """Seta id_status e calcula tag prev_lib correspondente"""
        pedido: cls = cls.query.get(id_ficha)

        status_novo: Status = Status.query.get(id_status)

        if status_novo.finaliza_processo:
            pedido.id_status_lib = 2
        else:
            pedido.id_status_lib = cls.calcular_tag_prev_lib(pedido.prev_liberacao)

        pedido.id_status = status_novo.id_status

        db.session.commit()  # type: ignore

        return None
