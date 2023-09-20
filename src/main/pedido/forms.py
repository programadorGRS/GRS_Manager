from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (DateField, IntegerField, SelectField, StringField,
                     SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..grupo.grupo import Grupo
from ..status.status import Status
from ..status.status_lib import StatusLiberacao
from ..status.status_rac import StatusRAC
from ..tipo_exame.tipo_exame import TipoExame


class FormBuscarASO(FlaskForm):
    data_inicio = DateField("Data Inicio", validators=[Optional()])
    data_fim = DateField("Data Fim", validators=[Optional()])
    id_status = SelectField("Status ASO", choices=[], validators=[Optional()])
    id_status_rac = SelectField("Status RAC", choices=[], validators=[Optional()])
    id_grupos = SelectField("Grupo", choices=[], validators=[Optional()])
    id_tag = SelectField("Prazo Liberação", choices=[], validators=[Optional()])

    # busca avancada
    cod_emp_princ = SelectField(
        "Empresa Principal", choices=[], validators=[Optional()]
    )
    id_empresa = SelectField(
        "Empresa", choices=[], validators=[Optional()], validate_choice=False
    )
    id_unidade = SelectField(
        "Unidade", choices=[], validators=[Optional()], validate_choice=False
    )
    id_prestador = SelectField(
        "Prestador", choices=[], validators=[Optional()], validate_choice=False
    )
    cod_tipo_exame = SelectField("Tipo Exame", choices=[], validators=[Optional()])
    seq_ficha = IntegerField("Seq. Ficha", validators=[Optional()])
    obs = StringField("Observação", validators=[Optional(), Length(0, 100)])
    nome_funcionario = StringField(
        "Nome Funcionário", validators=[Optional(), Length(0, 255)]
    )

    def validate_data_inicio(self, data_inicio):
        if data_inicio.data and self.data_fim.data:
            if data_inicio.data > self.data_fim.data:
                raise ValidationError("Inicio deve ser menor do que Fim")

    def load_choices(self):
        self.cod_emp_princ.choices = [("", "Selecione")] + [
            (i.cod, i.nome) for i in EmpresaPrincipal.query.all()
        ]

        self.id_status.choices = [("", "Selecione")] + [
            (i.id_status, i.nome_status)
            for i in Status.query.order_by(Status.nome_status).all()
        ]
        self.id_status_rac.choices = [("", "Selecione")] + [
            (i.id_status, i.nome_status)
            for i in StatusRAC.query.order_by(StatusRAC.nome_status).all()
        ]

        self.id_tag.choices = [("", "Selecione")] + [
            (i.id_status_lib, i.nome_status_lib)
            for i in StatusLiberacao.query.order_by(
                StatusLiberacao.nome_status_lib
            ).all()
        ]

        self.id_grupos.choices = [
            ("my_groups", "Meus Grupos"),
            ("all", "Todos"),
            ("null", "Sem Grupo"),
        ] + [(gp.id_grupo, gp.nome_grupo) for gp in Grupo.query.all()]

        self.cod_tipo_exame.choices = [("", "Selecione")] + [
            (i.cod_tipo_exame, i.nome_tipo_exame)
            for i in TipoExame.query.order_by(TipoExame.nome_tipo_exame).all()
        ]
        return None


class FormAtualizarStatus(FlaskForm):
    status_aso = SelectField("Status ASO*", choices=[], validators=[DataRequired()])
    status_rac = SelectField("Status RAC", choices=[], validators=[Optional()])
    data_recebido = DateField("Data Recebimento", validators=[Optional()])
    data_comparecimento = DateField("Data Comparecimento", validators=[Optional()])
    obs = TextAreaField(
        "Observação (Max 255 caracteres)", validators=[Optional(), Length(0, 255)]
    )

    def load_choices(self):
        default_choice = [("", "Selecione")]

        self.status_aso.choices = default_choice + [
            (status.id_status, status.nome_status)
            for status in Status.query.order_by(Status.nome_status).all()
        ]

        self.status_rac.choices = default_choice + [
            (status.id_status, status.nome_status)
            for status in StatusRAC.query.order_by(StatusRAC.nome_status).all()
        ]

        return None


class FormEnviarEmails(FlaskForm):
    assunto_email = StringField(
        "Assunto",
        validators=[Optional(), Length(0, 255)],
        render_kw={"placeholder": "Incluir um Assunto para os E-mails (Max 255)"},
    )
    email_copia = StringField(
        "E-mail CC",
        validators=[Optional(), Length(0, 255)],
        render_kw={"placeholder": "Incluir Pessoas em Cópia (Max 255)"},
    )
    obs_email = TextAreaField(
        "Observação",
        validators=[Optional(), Length(0, 255)],
        render_kw={
            "placeholder": "Incluir uma Observação no corpo do E-mail (Max 255)"
        },
    )


class FormPedidoBulkUpdate(FlaskForm):
    csv = FileField(
        "Escolher arquivo",
        validators=[
            FileRequired(),
            FileAllowed(["csv"], message="Apenas arquivos CSV"),
        ],
    )
    btn_upload = SubmitField("Upload")
