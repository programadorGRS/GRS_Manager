from src import database

from ..grupo.grupo import grupo_empresa_socnet


class EmpresaSOCNET(database.Model):
    '''
    Empresas que fazem referencia ao acesso SOCNET recebido pela EmpresaPrincipal

    Exemplo: 736956 - SYNGENTA (SOCNET), faz referencia a (PRINCIPAL/PARÂMETROS) SYNGENTA. \
    Ela nao e uma Empresa real e existe apenas na Base da GRS, portanto sua EmpresaPrincipal e \
    a GRS.
    '''
    __tablename__ = 'EmpresaSOCNET'
    id_empresa = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    # EmpresaPrincipal que essa EmpresaSOCNET esta referenciando 
    cod_empresa_referencia = database.Column(database.Integer, nullable=False)
    cod_empresa = database.Column(database.Integer, nullable=False)
    nome_empresa =  database.Column(database.String(255), nullable=False)
    emails = database.Column(database.String(500))
    ativo = database.Column(database.Boolean, nullable=False)
    
    pedidos = database.relationship('PedidoSOCNET', backref='empresa', lazy=True) # one to many
    grupo = database.relationship('Grupo', secondary=grupo_empresa_socnet, backref='empresas_socnet', lazy=True) # many to many

    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.cod_empresa}> {self.nome_empresa}'

