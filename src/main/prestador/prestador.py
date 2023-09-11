from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd
from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from src import TIMEZONE_SAO_PAULO, app
from src.extensions import database as db
from src.main.job.job_infos import JobInfos
from src.soc_web_service.exporta_dados_v2 import ExportaDados
from src.utils import tratar_emails

from ..grupo.grupo import grupo_prestador


class Prestador(db.Model):
    __tablename__ = "Prestador"

    id_prestador = db.Column(db.Integer, primary_key=True)

    cod_empresa_principal = db.Column(
        db.Integer, db.ForeignKey("EmpresaPrincipal.cod"), nullable=False
    )
    cod_prestador = db.Column(db.Integer)
    nome_prestador = db.Column(db.String(255), nullable=False)

    emails = db.Column(db.String(500))
    ativo = db.Column(db.Boolean, nullable=False)

    # se recebe ou nao emails de solicitacao de ASOs
    solicitar_asos = db.Column(db.Boolean, default=True)

    cnpj = db.Column(db.String(100))
    uf = db.Column(db.String(4))
    razao_social = db.Column(db.String(255))

    data_inclusao = db.Column(db.DateTime)
    data_alteracao = db.Column(db.DateTime)

    incluido_por = db.Column(db.String(50))
    alterado_por = db.Column(db.String(50))

    last_server_update = db.Column(db.DateTime)

    # relationships
    pedidos = db.relationship("Pedido", backref="prestador", lazy=True)  # one to many
    pedidos_socnet = db.relationship(
        "PedidoSOCNET", backref="prestador", lazy=True
    )  # one to many
    grupo = db.relationship(
        "Grupo", secondary=grupo_prestador, backref="prestadores", lazy=True
    )  # many to many

    def __repr__(self) -> str:
        return f"<{self.id_prestador}> {self.nome_prestador}"

    @classmethod
    def buscar_prestadores(
        cls,
        cod_emp_princ: int | None = None,
        id_prestador: int | None = None,
        cod_prestador: int | None = None,
        nome_prestador: str | None = None,
        prestador_ativo: int | None = None,
    ):
        params = []

        if cod_emp_princ:
            params.append(cls.cod_empresa_principal == cod_emp_princ)
        if id_prestador:
            params.append(cls.id_prestador == id_prestador)
        if cod_prestador:
            params.append(cls.cod_prestador == cod_prestador)
        if nome_prestador:
            params.append(cls.nome_prestador.like(f"%{nome_prestador}%"))
        if prestador_ativo in (0, 1):
            params.append(cls.ativo == prestador_ativo)

        query = (
            db.session.query(cls)  # type: ignore
            .filter(*params)
            .order_by(cls.nome_prestador)
        )

        return query

    @classmethod
    def carregar_prestadores(
        cls, cod_emp_princ: int, wsdl: str | BytesIO, ed_keys: dict[str, Any]
    ):
        ed = ExportaDados()
        ed.set_ed_keys(keys=ed_keys)
        ed.set_client(wsdl=wsdl)
        ed.set_factory()

        PARAM = ed.prestadores(
            empresa=cod_emp_princ,
            codigo=ed.ED_KEYS["PRESTADORES_COD"],
            chave=ed.ED_KEYS["PRESTADORES_KEY"],
        )

        body = ed.build_request_body(param=PARAM)

        infos = JobInfos(tabela=cls.__tablename__, cod_empresa_principal=cod_emp_princ)

        try:
            resp = ed.call_service(request_body=body)
        except Exception as e:
            infos.add_error(f"Erro no request: {str(e)}")
            infos.ok = False
            return infos

        erro = getattr(resp, "erro", None)
        if erro:
            msg_erro = getattr(resp, "mensagemErro", None)
            infos.add_error(f"Erro SOC: {msg_erro}")
            infos.ok = False
            return infos

        df = ed.df_from_zeep(response=resp)

        if df.empty:
            infos.add_error("df vazio")
            infos.ok = False
            return infos

        df = cls.__tratar_df(df=df)

        df = cls.__get_infos_prestador(df=df, cod_emp_princ=cod_emp_princ)

        df["cod_empresa_principal"] = cod_emp_princ

        infos = cls.__inserir(df=df.copy(), infos=infos)
        infos = cls.__atualizar(df=df.copy(), infos=infos)

        return infos

    @classmethod
    def __tratar_df(cls, df: pd.DataFrame):
        df = df.copy()

        COLS = {
            "codigoPrestador": "cod_prestador",
            "nomePrestador": "nome_prestador",
            "razaoSocial": "razao_social",
            "cnpj": "cnpj",
            "email": "emails",
            "estado": "uf",
            "situacao": "ativo",
        }

        df = df.replace(to_replace={"": None})

        df = df[list(COLS.keys())]

        df = df.rename(columns=COLS)

        df["cod_prestador"] = df["cod_prestador"].astype(int)

        df["ativo"] = df["ativo"].replace({"Sim": True, "Não": False})

        # tratar emails
        df["emails"] = df["emails"].fillna("").astype(str)
        df["emails"] = list(map(tratar_emails, df["emails"]))
        df["emails"] = df["emails"].replace("", None)

        return df

    @classmethod
    def __get_infos_prestador(cls, df: pd.DataFrame, cod_emp_princ: int):
        df = df.copy()

        query = db.session.query(cls.id_prestador, cls.cod_prestador).filter(  # type: ignore
            cls.cod_empresa_principal == cod_emp_princ
        )
        df_db = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

        df = df.merge(right=df_db, how="left", on="cod_prestador")

        return df

    @classmethod
    def __inserir(cls, df: pd.DataFrame, infos: JobInfos):
        df = df[df["id_prestador"].isna()]

        if df.empty:
            return infos

        df["data_inclusao"] = datetime.now(TIMEZONE_SAO_PAULO)

        try:
            qtd = df.to_sql(
                name=cls.__tablename__,
                con=db.session.bind,  # type: ignore
                if_exists="append",
                index=False,
            )
            db.session.commit()  # type: ignore
            infos.qtd_inseridos = qtd if qtd else 0
        except (SQLAlchemyError, DatabaseError) as e:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=e, exc_info=True)
            infos.add_error(f"Erro ao inserir: {str(e)}")
            infos.ok = False

        return infos

    @classmethod
    def __atualizar(cls, df: pd.DataFrame, infos: JobInfos):
        df = df[df["id_prestador"].notna()]

        if df.empty:
            return infos

        df["last_server_update"] = datetime.now(TIMEZONE_SAO_PAULO)

        df_mappings = df.to_dict(orient="records")

        try:
            db.session.bulk_update_mappings(cls, mappings=df_mappings)  # type: ignore
            db.session.commit()  # type: ignore
            infos.qtd_atualizados = len(df_mappings)
        except (SQLAlchemyError, DatabaseError) as e:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=e, exc_info=True)
            infos.add_error(f"Erro ao atualizar: {str(e)}")
            infos.ok = False

        return infos
