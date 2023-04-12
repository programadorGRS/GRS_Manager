from src import database


class Status(database.Model):
    __tablename__ = 'Status'
    id_status = database.Column(database.Integer, primary_key=True)
    nome_status = database.Column(database.String(100), nullable=False)
    finaliza_processo = database.Column(database.Boolean, nullable=False, default=False)
    status_padrao = database.Column(database.Boolean) # se for padrao, nunca exluir nem editar

    pedidos = database.relationship('Pedido', backref='status', lazy=True) # one to many
    pedidos_socnet = database.relationship('PedidoSOCNET', backref='status', lazy=True) # one to many
    
    data_inclusao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    data_alteracao = database.Column(database.DateTime)
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_status}> {self.nome_status}'

