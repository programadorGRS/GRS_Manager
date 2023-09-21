from src.extensions import database as db

from .carregar_rtc import CarregarRTC

RTCExames = db.Table(
    "RTCExames",
    db.Column("id_rtc", db.Integer, db.ForeignKey("RTC.id_rtc")),
    db.Column(
        "cod_tipo_exame",
        db.Integer,
        db.ForeignKey("TipoExame.cod_tipo_exame"),
    ),
    db.Column("cod_exame", db.String(255)),
)


RTCCargos = db.Table(
    "RTCCargos",
    db.Column("cod_cargo", db.String(255)),
    db.Column("id_rtc", db.ForeignKey("RTC.id_rtc")),
)


class RTC(db.Model, CarregarRTC):
    __tablename__ = "RTC"
    id_rtc = db.Column(db.Integer, primary_key=True, autoincrement=False)
    nome_rtc = db.Column(db.String(255), nullable=False)
