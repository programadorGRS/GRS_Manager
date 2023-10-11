from datetime import date, datetime
from typing import Literal

import numpy as np
import pandas as pd
from flask_login import current_user
from flask_sqlalchemy import BaseQuery
from sqlalchemy import and_
from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from src import TIMEZONE_SAO_PAULO
from src.extensions import database as db

from ..empresa_socnet.empresa_socnet import EmpresaSOCNET
from ..grupo.grupo import Grupo, grupo_empresa_prestador_socnet
from ..job.job_infos import JobInfos
from ..prestador.prestador import Prestador
from ..status.status import Status
from ..status.status_rac import StatusRAC
from ..tipo_exame.tipo_exame import TipoExame


class PedidoSOCNET(db.Model):
    """
    Pedidos de Exames adiquiridos atraves do front end do SOC em \
    Administracao > Rede Credenciada SOCNET > Relatorio de Exames SOCNET.

    Os dados sao diferentes dos Pedidos de Exames adquiridos via Exporta Dados, ja que nos Exporta Dados \
    o Prestador que aparece nao e o Prestador final do atendimento, mas o intermediario (GRS).
    """

    __tablename__ = "PedidoSOCNET"

    id_ficha = db.Column(db.Integer, primary_key=True)
    seq_ficha = db.Column(db.Integer, nullable=False)
    cod_empresa_principal = db.Column(
        db.Integer, db.ForeignKey("EmpresaPrincipal.cod"), nullable=False
    )
    cod_empresa_referencia = db.Column(db.Integer, nullable=False)
    cod_funcionario = db.Column(db.Integer, nullable=False)
    cpf = db.Column(db.String(30))
    nome_funcionario = db.Column(db.String(150), nullable=False)
    data_ficha = db.Column(db.Date, nullable=False)
    cod_tipo_exame = db.Column(
        db.Integer,
        db.ForeignKey("TipoExame.cod_tipo_exame"),
        nullable=False,
    )
    id_prestador = db.Column(db.Integer, db.ForeignKey("Prestador.id_prestador"))
    id_empresa = db.Column(
        db.Integer,
        db.ForeignKey("EmpresaSOCNET.id_empresa"),
        nullable=False,
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
    data_recebido = db.Column(db.Date)
    data_comparecimento = db.Column(db.Date)
    obs = db.Column(db.String(255))

    data_inclusao = db.Column(db.DateTime)
    data_alteracao = db.Column(db.DateTime)
    incluido_por = db.Column(db.String(50))
    alterado_por = db.Column(db.String(50))

    # colunas para a planilha de pedidos
    COLS_CSV = [
        "cod_empresa_principal",
        "cod_empresa_referencia",
        "seq_ficha",
        "cod_funcionario",
        "nome_funcionario",
        "data_ficha",
        "tipo_exame",
        "cod_empresa",
        "empresa",
        "cod_prestador",
        "prestador",
        "status_aso",
        "status_rac",
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
        "nome_empresa": "Empresa",
    }

    @classmethod
    def buscar_pedidos(
        cls,
        id_grupos: int | list[int] | None = None,
        cod_emp_princ: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        id_status: int | None = None,
        id_status_rac: int | None = None,
        id_empresa: int | None = None,
        id_prestador: int | None = None,
        cod_tipo_exame: int | None = None,
        seq_ficha: int | None = None,
        nome_funcionario: str | None = None,
        obs: str | None = None,
    ) -> BaseQuery:
        PARAMS = (
            (cod_emp_princ, (cls.cod_empresa_principal == cod_emp_princ)),
            (id_empresa, (cls.id_empresa == id_empresa)),
            (id_status, (cls.id_status == id_status)),
            (id_status_rac, (cls.id_status_rac == id_status_rac)),
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
                grupo_empresa_prestador_socnet,
                and_(
                    cls.id_empresa == grupo_empresa_prestador_socnet.c.id_empresa,
                    cls.id_prestador == grupo_empresa_prestador_socnet.c.id_prestador,
                ),
            ),
            (Grupo, grupo_empresa_prestador_socnet.c.id_grupo == Grupo.id_grupo),
        ]

        query = (
            db.session.query(cls)  # type: ignore
            .outerjoin(*joins)
            .filter(*filtros)
            .order_by(PedidoSOCNET.data_ficha.desc(), PedidoSOCNET.nome_funcionario)
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
            EmpresaSOCNET.cod_empresa,
            EmpresaSOCNET.nome_empresa.label("empresa"),
            Prestador.cod_prestador,
            Prestador.nome_prestador.label("prestador"),
            Status.nome_status.label("status_aso"),
            StatusRAC.nome_status.label("status_rac"),
            Grupo.nome_grupo,
        ]

        joins = [
            (TipoExame, cls.cod_tipo_exame == TipoExame.cod_tipo_exame),
            (EmpresaSOCNET, cls.id_empresa == EmpresaSOCNET.id_empresa),
            (Prestador, cls.id_prestador == Prestador.id_prestador),
            (Status, cls.id_status == Status.id_status),
            (StatusRAC, cls.id_status_rac == StatusRAC.id_status),
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
    def tratar_df_socnet(cls, df: pd.DataFrame):
        INITIAL_COLS = [
            "Sequencial Ficha",
            "CPF",
            "Funcionario",
            "Código Funcionário",
            "Data Ficha",
            "Tipo de Exame",
            "Código Empresa",
            "Código Prestador",
        ]

        df = df[INITIAL_COLS]

        if df.empty:
            return df

        df = df.replace(to_replace={"": None})

        NOT_NULL_COLS = ["Sequencial Ficha", "Código Funcionário", "Código Empresa"]

        df = df.dropna(axis=0, subset=NOT_NULL_COLS)

        if df.empty:
            return df

        for col in ["Sequencial Ficha", "Código Funcionário", "Código Empresa"]:
            df[col] = df[col].astype(int)

        df = df.drop_duplicates(subset="Sequencial Ficha")

        df["CPF"] = df["CPF"].astype("string").str.replace("[.-]", "", regex=True)
        df["Data Ficha"] = pd.to_datetime(df["Data Ficha"], dayfirst=True).dt.date

        df = cls.__get_infos_pedido(df=df)

        df["Tipo de Exame"] = df["Tipo de Exame"].replace(
            "Mudança de Função", "Mudança de Riscos Ocupacionais"
        )
        df = cls.__get_infos_tipo_exame(df=df)

        df = cls.__get_infos_empresa(df=df)
        df = cls.__get_infos_prestador(df=df)

        RENAME_COLS = {
            "Sequencial Ficha": "seq_ficha",
            "CPF": "cpf",
            "Funcionario": "nome_funcionario",
            "Código Funcionário": "cod_funcionario",
            "Data Ficha": "data_ficha",
        }

        df = df.rename(columns=RENAME_COLS)

        FINAL_COLS = [
            "id_ficha",
            "seq_ficha",
            "cod_empresa_principal",
            "cod_empresa_referencia",
            "cod_funcionario",
            "cpf",
            "nome_funcionario",
            "data_ficha",
            "cod_tipo_exame",
            "id_prestador",
            "id_empresa",
        ]

        df = df[FINAL_COLS]

        return df

    @staticmethod
    def filtrar_empresas(df: pd.DataFrame):
        """Filtrar df e manter apenas empresas válidas"""
        df = df.copy()

        query = db.session.query(EmpresaSOCNET.id_empresa, EmpresaSOCNET.cod_empresa)  # type: ignore
        df_empresas = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore
        ids_empresas = df_empresas["id_empresa"].astype(int).tolist()

        df = df[df["id_empresa"].isin(ids_empresas)]
        return df

    @classmethod
    def __get_infos_pedido(cls, df: pd.DataFrame):
        df = df.copy()

        query = db.session.query(cls.id_ficha, cls.seq_ficha)  # type: ignore
        df_db = pd.read_sql(query.statement, con=db.session.bind)  # type: ignore

        df = df.merge(
            df_db, how="left", left_on="Sequencial Ficha", right_on="seq_ficha"
        )

        df = df.drop(columns="seq_ficha")

        return df

    @classmethod
    def inserir_pedidos(cls, df: pd.DataFrame):
        df = df[df["id_ficha"].isna()].copy()

        if df.empty:
            return 0

        df["incluido_por"] = current_user.username  # type: ignore
        df["data_inclusao"] = datetime.now(tz=TIMEZONE_SAO_PAULO)
        df["id_status"] = 1
        df["id_status_rac"] = 1

        qtd = df.to_sql(
            name=PedidoSOCNET.__tablename__,
            con=db.session.bind,  # type: ignore
            index=False,
            if_exists="append",
        )
        db.session.commit()  # type: ignore

        return qtd

    @staticmethod
    def __get_infos_tipo_exame(df: pd.DataFrame):
        df = df.copy()

        query = db.session.query(TipoExame)  # type: ignore
        df_db = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

        df = pd.merge(
            df,
            df_db,
            how="left",
            left_on="Tipo de Exame",
            right_on="nome_tipo_exame",
        )

        df = df.drop(columns="nome_tipo_exame")

        return df

    @staticmethod
    def __get_infos_empresa(df: pd.DataFrame):
        df = df.copy()

        query = db.session.query(  # type: ignore
            EmpresaSOCNET.id_empresa,
            EmpresaSOCNET.cod_empresa,
            EmpresaSOCNET.cod_empresa_principal,
            EmpresaSOCNET.cod_empresa_referencia,
        )
        df_db = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

        df = df.merge(
            df_db, how="left", left_on="Código Empresa", right_on="cod_empresa"
        )

        df = df.drop(columns="cod_empresa")

        return df

    @staticmethod
    def __get_infos_prestador(df: pd.DataFrame):
        df = df.copy()

        query = db.session.query(Prestador.id_prestador, Prestador.cod_prestador)  # type: ignore
        df_db = pd.read_sql(sql=(query.statement), con=db.session.bind)  # type: ignore

        # NOTE: adicionar uma linha Nan no df db para nao travar o merge quando
        # o prestador estiver vazio no df_exporta_dados
        df_aux = pd.DataFrame({"id_prestador": [None], "cod_prestador": [None]})
        df_db = pd.concat(
            [df_db, df_aux],
            axis=0,
            ignore_index=True,
        )

        df_db = df_db.astype("Int32")

        df["Código Prestador"] = df["Código Prestador"].astype("Int32")

        df = df.merge(
            df_db,
            how="left",
            left_on="Código Prestador",
            right_on="cod_prestador",
        )

        df = df.drop(columns="cod_prestador")

        return df

    @classmethod
    def __inserir_pedidos(cls, df: pd.DataFrame, infos: JobInfos):
        # manter apenas pedidos sem id (novos)
        df = df[df["id_ficha"].isna()].copy()

        if df.empty:
            infos.qtd_inseridos = 0
            infos.add_error(error="df vazio ao inserir")
            return infos

        df["id_status"] = 1  # Vazio
        df["id_status_rac"] = 1  # Vazio

        df["data_inclusao"] = datetime.now(tz=TIMEZONE_SAO_PAULO)
        df["incluido_por"] = current_user.username  # type: ignore

        try:
            qtd = df.to_sql(
                name=cls.__tablename__,
                con=db.session.bind,  # type: ignore
                if_exists="append",
                index=False,
            )
            db.session.commit()  # type: ignore
            infos.qtd_inseridos = qtd if qtd else 0
        except (SQLAlchemyError, DatabaseError):
            db.session.rollback()  # type: ignore
            infos.ok = False
            infos.add_error(error="Erro ao inserir")

        return infos

    @classmethod
    def __atualizar_pedidos(cls, df: pd.DataFrame, infos: JobInfos):
        # manter apenas pedidos com id validos (ja existem)
        df = df[df["id_ficha"].notna()].copy()

        if df.empty:
            infos.qtd_atualizados = 0
            infos.add_error(error="df vazio ao atualizar")
            return infos

        # remover colunas que nao mudam
        df.drop(columns="seq_ficha", inplace=True)

        # NOTE: fazer isso para evitar que df_mappings contenha 'np.nan'
        # esse valor nao é aceito em databases
        df["id_prestador"] = df["id_prestador"].astype(object)
        df["id_prestador"] = df["id_prestador"].replace(np.nan, None)

        df_mappings = df.to_dict(orient="records")

        try:
            db.session.bulk_update_mappings(cls, df_mappings)  # type: ignore
            db.session.commit()  # type: ignore
            infos.qtd_atualizados = len(df_mappings)
        except (SQLAlchemyError, DatabaseError):
            db.session.rollback()  # type: ignore
            infos.ok = False
            infos.add_error(error="Erro ao atualizar")

        return infos
