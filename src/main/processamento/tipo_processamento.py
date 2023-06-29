from src.extensions import database


class TipoProcessamento(database.Model):
    __tablename__ = 'TipoProcessamento'

    id = database.Column(database.Integer, primary_key=True, nullable=False)
    nome = database.Column(database.String(100), nullable=False)

    # relationships
    processamentos = database.relationship(
        'Processamento',
        backref='tipo_processamento',
        lazy=True
    ) # one to many