from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField
from wtforms.validators import InputRequired, Optional


class FormBuscarExames(FlaskForm):
    cod_emp_princ = SelectField(
        "Empresa Principal", choices=[], validators=[Optional()]
    )
    id_exame = IntegerField("Id", validators=[Optional()])
    cod_exame = IntegerField("Código", validators=[Optional()])
    nome_exame = StringField("Nome", validators=[Optional()])
    prazo_exame = IntegerField("Prazo", validators=[Optional()])


class FormExame(FlaskForm):
    prazo_exame = IntegerField("Prazo (Dias úteis)", validators=[InputRequired()])
