from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField
from wtforms.validators import Optional, ValidationError


class FormLogAcoes(FlaskForm):
    data_inicio = DateField('Inicio', validators=[Optional()])
    data_fim = DateField('Fim', validators=[Optional()])
    usuario = SelectField('Usuário', choices=[], validators=[Optional()])
    tabela = SelectField('Tabela', validators=[Optional()])
    botao_buscar = SubmitField('Buscar')

    def validate_data_inicio(self, data_inicio):
        if data_inicio.data and self.data_fim.data:
            if data_inicio.data > self.data_fim.data:
                raise ValidationError('Inicio deve ser menor do que Fim')
