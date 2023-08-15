from sqlalchemy import text

from src.extensions import database as db


class MandatoConfigEmpresa(db.Model):
    __tablename__ = "MandatoConfigEmpresa"

    id = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(
        db.Integer, db.ForeignKey("Empresa.id_empresa"), nullable=False, unique=True
    )
    load_hist = db.Column(db.Boolean, server_default=text("0"), nullable=False)
    monit_erros = db.Column(db.Boolean, server_default=text("0"), nullable=False)
    monit_venc = db.Column(db.Boolean, server_default=text("0"), nullable=False)
    emails = db.Column(db.String(500))
