from src.extensions import database as db


class EmpresaPrincipal(db.Model):
    __tablename__ = "EmpresaPrincipal"

    cod = db.Column(db.Integer, primary_key=True, autoincrement=False)
    nome = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    socnet = db.Column(db.Boolean, nullable=False, default=True)
    configs_exporta_dados = db.Column(db.String(255))
    chaves_exporta_dados = db.Column(db.String(255))

    # relationships
    empresas = db.relationship(
        "Empresa", backref="empresa_principal", lazy=True
    )  # one to many
    unidades = db.relationship(
        "Unidade", backref="empresa_principal", lazy=True
    )  # one to many
    pedidos = db.relationship(
        "Pedido", backref="empresa_principal", lazy=True
    )  # one to many
    exames = db.relationship(
        "Exame", backref="empresa_principal", lazy=True
    )  # one to many
    jobs = db.relationship("Job", backref="empresa_principal", lazy=True)  # one to many

    data_inclusao = db.Column(db.DateTime)
    data_alteracao = db.Column(db.DateTime)
    incluido_por = db.Column(db.String(50))
    alterado_por = db.Column(db.String(50))

    def __repr__(self) -> str:
        return f"<{self.cod}> {self.nome}"
