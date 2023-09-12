from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import DateField, SelectField, ValidationError
from wtforms.validators import DataRequired

from ..empresa_principal.empresa_principal import EmpresaPrincipal


class FormAtualizarTabela(FlaskForm):
    opcoes_tabela = [("", "Selecione"), (1, "Empresas"), (2, "Unidades"), (3, "Exames")]

    tabela = SelectField(
        "Tabela para Atualizar", choices=opcoes_tabela, validators=[DataRequired()]
    )
    csv = FileField(
        "Escolher arquivo",
        validators=[
            FileRequired(),
            FileAllowed(["csv"], message="Apenas arquivos CSV"),
        ],
    )


class FormImportarDados(FlaskForm):
    """
    Validações:
        - limite de 30 dias entre data_inicio e data_fim
    """

    LIMITE_DIAS = 30

    cod_emp_princ = SelectField(
        "Empresa Principal", choices=[], validators=[DataRequired()]
    )
    id_empresa = SelectField(
        "Empresa", choices=[], validators=[DataRequired()], validate_choice=False
    )
    tabela = SelectField(
        "Selecione uma Tabela", choices=[], validators=[DataRequired()]
    )
    data_inicio = DateField("Data Inicio", validators=[DataRequired()])
    data_fim = DateField("Data Fim", validators=[DataRequired()])

    def validate_data_inicio(self, data_inicio):
        if data_inicio.data > self.data_fim.data:
            raise ValidationError("Data Inicio deve ser menor que Data Fim")

        inicio = self.data_inicio.data
        fim = self.data_fim.data
        if (fim - inicio).days > self.LIMITE_DIAS:  # type: ignore
            raise ValidationError(f"Máximo {self.LIMITE_DIAS} dias")

    def load_choices(self):
        self.tabela.choices = [("", "Selecione"), (1, "Pedidos"), (2, "Funcionários")]

        self.cod_emp_princ.choices = [("", "Selecione")] + [
            (emp.cod, emp.nome) for emp in EmpresaPrincipal.query.all()
        ]

        return None
