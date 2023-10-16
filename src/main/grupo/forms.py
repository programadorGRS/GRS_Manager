from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField
from wtforms.validators import DataRequired, Length

from ..empresa.empresa import Empresa
from ..empresa_socnet.empresa_socnet import EmpresaSOCNET
from ..prestador.prestador import Prestador
from ..usuario.usuario import Usuario


class FormGrupo(FlaskForm):
    nome_grupo = StringField(
        "Nome do Grupo", validators=[DataRequired(), Length(3, 255)]
    )


class FormGrupoMembros(FlaskForm):
    select = SelectMultipleField(label="Select", choices=[], validate_choice=False)

    def load_usuarios_choices(self):
        self.select.choices = [(i.id_usuario, i.username) for i in Usuario.query.all()]
        # sort choices by name, ascending
        self.select.choices.sort(key=lambda tup: tup[1], reverse=False)
        return None

    def load_prestador_choices(self):
        self.select.choices = [
            (i.id_prestador, i.nome_prestador) for i in Prestador.query.all()
        ]
        # sort choices by name, ascending
        self.select.choices.sort(key=lambda tup: tup[1], reverse=False)
        return None

    def load_empresas_choices(self):
        self.select.choices = [
            (i.id_empresa, i.razao_social) for i in Empresa.query.all()
        ]
        # sort choices by name, ascending
        self.select.choices.sort(key=lambda tup: tup[1], reverse=False)
        return None

    def load_empresas_socnet_choices(self):
        self.select.choices = [
            (i.id_empresa, i.nome_empresa) for i in EmpresaSOCNET.query.all()
        ]
        # sort choices by name, ascending
        self.select.choices.sort(key=lambda tup: tup[1], reverse=False)
        return None
