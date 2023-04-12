from src import database


class EmpresaPrincipal(database.Model):
    __tablename__ = 'EmpresaPrincipal'
    cod = database.Column(database.Integer, primary_key=True, autoincrement=False)
    nome = database.Column(database.String(255), nullable=False)
    ativo = database.Column(database.Boolean, nullable=False, default=True)
    socnet = database.Column(database.Boolean, nullable=False, default=True)
    configs_exporta_dados = database.Column(database.String(255))
    
    empresas = database.relationship('Empresa', backref='empresa_principal', lazy=True) # one to many
    empresas_socnet = database.relationship('EmpresaSOCNET', backref='empresa_principal', lazy=True) # one to many
    unidades = database.relationship('Unidade', backref='empresa_principal', lazy=True) # one to many
    exames = database.relationship('Exame', backref='empresa_principal', lazy=True) # one to many
    
    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.cod}> {self.nome}'

