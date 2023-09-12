from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField
from wtforms.validators import DataRequired, Length


class FormCriarGrupo(FlaskForm):
    nome_grupo = StringField(
        "Nome do Grupo", validators=[DataRequired(), Length(3, 255)]
    )


class FormGrupoPrestadores(FlaskForm):
    select = SelectMultipleField(label="Select", choices=[], validate_choice=False)
