from flask_wtf import FlaskForm
from wtforms import DateField, SelectField
from wtforms.validators import DataRequired, Optional


class FormBuscarExamesRealizados(FlaskForm):
    opcoes = [('', 'Selecione')]
    cod_empresa_principal = SelectField(
        'Empresa Principal',
        validators=[DataRequired()],
        render_kw={'onchange': "CarregarOpcoesExamesRealizados('cod_empresa_principal', 'cod_empresa', 'cod_unidade', 'cod_exame')"}
    )
    cod_empresa = SelectField(
        'Empresa',
        validators=[Optional()],
        render_kw={'onchange': "carregarOpcoesUnidade('cod_empresa_principal', 'cod_empresa', 'cod_unidade')"},
        choices=opcoes,
        validate_choice=False
    )
    cod_unidade = SelectField('Unidade', validators=[Optional()], choices=opcoes, validate_choice=False)
    cod_exame = SelectField('Exame', validators=[Optional()], choices=opcoes, validate_choice=False)
    data_inicio = DateField('Data Exame Inicio', validators=[Optional()])
    data_fim = DateField('Data Exame Fim', validators=[Optional()])
