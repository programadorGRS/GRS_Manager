from datetime import date, timedelta
from typing import Any

from sqlalchemy import text

from src.extensions import database as db


class PedProcConfig(db.Model):
    __tablename__ = "PedProcConfig"

    id = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(
        db.Integer,
        db.ForeignKey("Empresa.id_empresa"),
        nullable=False,
        unique=True,
    )

    ativo = db.Column(db.Boolean, server_default=text("1"))
    # default 731 dias -> 24 meses
    periodo_timedelta_dias = db.Column(db.Integer, server_default=text("731"))
    selecao = db.Column(db.Integer, server_default=text("1"))
    convocar_clinico = db.Column(db.Boolean, server_default=text("0"))
    nunca_realizados = db.Column(db.Boolean, server_default=text("0"))
    per_nunca_realizados = db.Column(db.Boolean, server_default=text("0"))
    pendentes = db.Column(db.Boolean, server_default=text("0"))
    pendentes_pcmso = db.Column(db.Boolean, server_default=text("0"))

    @classmethod
    def get_periodo(cls, id_empresa: int):
        conf: cls = db.session.query(cls).filter(cls.id_empresa == id_empresa).first()

        date_format = "%m/%Y"
        data = date.today() + timedelta(days=conf.periodo_timedelta_dias)
        return data.strftime(date_format)

    @classmethod
    def get_configs(cls, id_empresa: int) -> dict[str, Any]:
        conf: cls = db.session.query(cls).filter(cls.id_empresa == id_empresa).first()

        param = {
            "empresa": conf.empresa.cod_empresa,
            "periodo": cls.get_periodo(conf.id_empresa),
            "convocarClinico": conf.convocar_clinico,
            "nuncaRealizados": conf.nunca_realizados,
            "periodicosNuncaRealizados": conf.per_nunca_realizados,
            "selecao": conf.selecao,
            "examesPendentes": conf.pendentes,
            "convocaPendentesPCMSO": conf.pendentes_pcmso,
        }

        return param
