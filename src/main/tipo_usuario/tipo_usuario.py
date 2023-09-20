from src.extensions import database


class TipoUsuario(database.Model):
    __tablename__ = 'TipoUsuario'
    id_role = database.Column(database.Integer, primary_key=True)
    nome = database.Column(database.String(255), nullable=False)
    usuarios = database.relationship('Usuario', backref='role', lazy=True) # one to many

