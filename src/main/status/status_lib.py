from src import database


class StatusLiberacao(database.Model):
    '''
    Status da previsão de liberacao do ASO

    Baseado na data de prev_liberacao
    '''
    __tablename__ = 'StatusLiberacao'
    id_status_lib = database.Column(database.Integer, primary_key=True)
    nome_status_lib = database.Column(database.String(50), nullable=False)
    cor_tag = database.Column(database.String(50))
    
    pedidos = database.relationship('Pedido', backref='status_lib', lazy=True) # one to many

    def __repr__(self) -> str:
        return f'<{self.id_status_lib}> {self.nome_status_lib}'

