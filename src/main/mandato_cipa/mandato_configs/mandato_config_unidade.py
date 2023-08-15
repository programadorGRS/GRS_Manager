from sqlalchemy import text

from src.extensions import database as db


class MandatoConfigUnidade(db.Model):
    __tablename__ = "MandatoConfigUnidade"

    id = db.Column(db.Integer, primary_key=True)
    id_unidade = db.Column(
        db.Integer, db.ForeignKey("Unidade.id_unidade"), nullable=False, unique=True
    )
    monit_erros = db.Column(db.Boolean, server_default=text("0"), nullable=False)
    monit_venc = db.Column(db.Boolean, server_default=text("0"), nullable=False)
    emails = db.Column(db.String(500))
