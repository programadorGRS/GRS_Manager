from src.extensions import database as db


class StatusLiberacao(db.Model):
    """
    Status da previsão de liberacao do ASO

    Baseado na data de prev_liberacao
    """

    __tablename__ = "StatusLiberacao"

    id_status_lib = db.Column(db.Integer, primary_key=True)
    nome_status_lib = db.Column(db.String(50), nullable=False)
    cor_tag = db.Column(db.String(50))

    pedidos = db.relationship("Pedido", backref="status_lib", lazy=True)  # one to many

    def __repr__(self) -> str:
        return f"<{self.id_status_lib}> {self.nome_status_lib}"

    @classmethod
    def get_id_status_ok(cls) -> int:
        q = cls.query.filter_by(nome_status_lib="OK").first()
        return q.id_status_lib
