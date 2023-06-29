from src.extensions import database


class StatusProcessamento(database.Model):
    __tablename__ = 'StatusProcessamento'

    id = database.Column(database.Integer, primary_key=True, nullable=False)
    nome = database.Column(database.String(100), nullable=False)

    # relationships
    processamentos = database.relationship(
        'Processamento',
        backref='status_processamento',
        lazy=True
    ) # one to many