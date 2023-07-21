from src import database

from .carregar_rtc import CarregarRTC

RTCExames = database.Table(
    "RTCExames",
    database.Column("id_rtc", database.Integer, database.ForeignKey("RTC.id_rtc")),
    database.Column(
        "cod_tipo_exame",
        database.Integer,
        database.ForeignKey("TipoExame.cod_tipo_exame"),
    ),
    database.Column("cod_exame", database.String(255)),
)


RTCCargos = database.Table(
    "RTCCargos",
    database.Column("cod_cargo", database.String(255)),
    database.Column("id_rtc", database.ForeignKey("RTC.id_rtc")),
)


class RTC(database.Model, CarregarRTC):
    __tablename__ = "RTC"
    id_rtc = database.Column(database.Integer, primary_key=True, autoincrement=False)
    nome_rtc = database.Column(database.String(255), nullable=False)
