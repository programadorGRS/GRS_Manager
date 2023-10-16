from datetime import datetime
from typing import Literal

from sqlalchemy import Table

from src import TIMEZONE_SAO_PAULO
from src.extensions import database as db

grupo_usuario = db.Table(
    "grupo_usuario",
    db.Column("id_grupo", db.Integer, db.ForeignKey("Grupo.id_grupo")),
    db.Column("id_usuario", db.Integer, db.ForeignKey("Usuario.id_usuario")),
)


grupo_empresa = db.Table(
    "grupo_empresa",
    db.Column("id_grupo", db.Integer, db.ForeignKey("Grupo.id_grupo")),
    db.Column("id_empresa", db.Integer, db.ForeignKey("Empresa.id_empresa")),
)


grupo_empresa_socnet = db.Table(
    "grupo_empresa_socnet",
    db.Column("id_grupo", db.Integer, db.ForeignKey("Grupo.id_grupo")),
    db.Column("id_empresa", db.Integer, db.ForeignKey("EmpresaSOCNET.id_empresa")),
)


grupo_prestador = db.Table(
    "grupo_prestador",
    db.Column("id_grupo", db.Integer, db.ForeignKey("Grupo.id_grupo")),
    db.Column("id_prestador", db.Integer, db.ForeignKey("Prestador.id_prestador")),
)


class Grupo(db.Model):
    __tablename__ = "Grupo"

    id_grupo = db.Column(db.Integer, primary_key=True)
    nome_grupo = db.Column(db.String(255), nullable=False)  # many to many

    data_inclusao = db.Column(db.DateTime)
    data_alteracao = db.Column(db.DateTime)

    incluido_por = db.Column(db.String(50))
    alterado_por = db.Column(db.String(50))

    @staticmethod
    def handle_group_filter(
        id_usuario: int, tabela: Table, grupo: int | Literal["my_groups", "all", "null"]
    ) -> tuple | None:
        match grupo:
            case "my_groups":
                from ..usuario.usuario import Usuario

                usuario = Usuario.query.get(id_usuario)
                grupos_usuario = [gp.id_grupo for gp in usuario.grupo]
                return tabela.c.id_grupo.in_(grupos_usuario)
            case "all":
                return None
            case "null":
                return tabela.c.id_grupo == None  # noqa
            case _:
                return tabela.c.id_grupo == int(grupo)

    @classmethod
    def set_usuarios(cls, id_grupo: int, id_usuarios: list[int], alterado_por: str):
        from ..usuario.usuario import Usuario

        grupo = cls.query.get(id_grupo)

        usuarios: list[Usuario] = (
            db.session.query(Usuario)  # type: ignore
            .filter(Usuario.id_usuario.in_(id_usuarios))
            .all()
        )

        grupo.usuarios = usuarios

        grupo.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        grupo.alterado_por = alterado_por

        db.session.commit()  # type: ignore
        return None

    @classmethod
    def set_prestadores(
        cls, id_grupo: int, id_prestadores: list[int], alterado_por: str
    ):
        from ..prestador.prestador import Prestador

        grupo = cls.query.get(id_grupo)

        prestadores = (
            db.session.query(Prestador)  # type: ignore
            .filter(Prestador.id_prestador.in_(id_prestadores))
            .all()
        )

        grupo.prestadores = prestadores

        grupo.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        grupo.alterado_por = alterado_por

        db.session.commit()  # type: ignore
        return None

    @classmethod
    def set_empresas(cls, id_grupo: int, id_empresas: list[int], alterado_por: str):
        from ..empresa.empresa import Empresa

        grupo = cls.query.get(id_grupo)

        empresas = (
            db.session.query(Empresa)  # type: ignore
            .filter(Empresa.id_empresa.in_(id_empresas))
            .all()
        )

        grupo.empresas = empresas

        grupo.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        grupo.alterado_por = alterado_por

        db.session.commit()  # type: ignore
        return None

    @classmethod
    def set_empresas_socnet(
        cls, id_grupo: int, id_empresas: list[int], alterado_por: str
    ):
        from ..empresa_socnet.empresa_socnet import EmpresaSOCNET

        grupo = cls.query.get(id_grupo)

        empresas = (
            db.session.query(EmpresaSOCNET)  # type: ignore
            .filter(EmpresaSOCNET.id_empresa.in_(id_empresas))
            .all()
        )

        grupo.empresas_socnet = empresas

        grupo.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        grupo.alterado_por = alterado_por

        db.session.commit()  # type: ignore
        return None
