from src.extensions import database


class TipoExame(database.Model):
    '''
        Tipo de Ficha a que os exames pertencem
    '''
    __tablename__ = 'TipoExame'
    # cod definido pela base do SOC
    cod_tipo_exame = database.Column(database.Integer, primary_key=True, autoincrement=False)
    nome_tipo_exame = database.Column(database.String(100), nullable=False)
    
    pedidos = database.relationship('Pedido', backref='tipo_exame', lazy=True) # one to many
    pedidos_socnet = database.relationship('PedidoSOCNET', backref='tipo_exame', lazy=True) # one to many

    def __repr__(self) -> str:
        return f'<{self.cod_tipo_exame}> {self.nome_tipo_exame}'

