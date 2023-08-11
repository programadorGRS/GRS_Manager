from flask_wtf import FlaskForm
from wtforms import DateField, SelectField
from wtforms.validators import DataRequired, Optional


class FormBuscarAbsenteismo(FlaskForm):
    opcoes = [("", "Selecione")]
    cod_emp_princ = SelectField(
        "Empresa Principal",
        validators=[DataRequired()],
        render_kw={
            "onchange": "CarregarOpcoesAbsenteismo('cod_emp_princ', 'id_empresa', 'id_unidade')"
        },
    )
    id_empresa = SelectField(
        "Empresa",
        validators=[Optional()],
        render_kw={
            "onchange": "carregarOpcoesUnidade('cod_emp_princ', 'id_empresa', 'id_unidade')"
        },
        choices=opcoes,
        validate_choice=False,
    )
    id_unidade = SelectField(
        "Unidade", validators=[Optional()], choices=opcoes, validate_choice=False
    )
    data_inicio = DateField("Data Exame Inicio", validators=[Optional()])
    data_fim = DateField("Data Exame Fim", validators=[Optional()])
