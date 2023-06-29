from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, StringField
from wtforms.validators import Length, Optional

from src.utils import validate_email_fields

from ..empresa_principal.empresa_principal import EmpresaPrincipal


class FormBuscarUnidade(FlaskForm):
    kws_emp_princ = {
        'onchange': "carregarOpcoesEmpresa('cod_emp_princ', 'id_empresa')"
    }

    cod_emp_princ = SelectField(
        'Empresa Principal',
        choices=[],
        validators=[Optional()],
        render_kw=kws_emp_princ
    )
    id_empresa = SelectField(
        'Empresa',
        choices=[],
        validators=[Optional()],
        validate_choice=False
    )
    id_unidade = IntegerField('ID Unidade', validators=[Optional()])
    cod_unidade = IntegerField('Código Unidade', validators=[Optional()])
    nome_unidade = StringField('Nome Unidade', validators=[Optional()])
    unidade_ativa = SelectField('Unidade Ativa', choices=[], validators=[Optional()])

    def load_choices(self):
        self.cod_emp_princ.choices = (
            [('', 'Selecione')] +
            [(emp.cod, emp.nome) for emp in EmpresaPrincipal.query.all()]
        )

        self.id_empresa.choices = [('', 'Selecione uma Empresa Principal')]

        self.unidade_ativa.choices = [('', 'Selecione'), (1, 'Sim'), (0, 'Não')]
        return None

class FormUnidade(FlaskForm):
    kws = {'placeholder': "E-mails"}

    # relatorios
    conv_exames = BooleanField('Conv. de Exames', validators=[Optional()])
    conv_exames_emails = StringField('E-mails Convocação Exames', validators=[Optional(), Length(0, 500)], render_kw=kws)

    exames_realizados = BooleanField('Exames Realizados', validators=[Optional()])
    exames_realizados_emails = StringField('E-mails Exames Realizados', validators=[Optional(), Length(0, 500)], render_kw=kws)

    absenteismo = BooleanField('Absenteísmo', validators=[Optional()])
    absenteismo_emails = StringField('E-mails Absenteísmo', validators=[Optional(), Length(0, 500)], render_kw=kws)

    mandatos_cipa = BooleanField('Mandatos CIPA', validators=[Optional()])
    mandatos_cipa_emails = StringField('E-mails Mandato CIPA', validators=[Optional(), Length(0, 500)], render_kw=kws)

    # override Flaskform validate method to validate multiple fields
    def validate(self, *args, **kwargs):
        return validate_email_fields(form=self, *args, **kwargs)

