from flask import Blueprint, abort, flash, redirect, render_template, url_for
from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from src import app
from src.extensions import database as db
from src.utils import get_data_from_form, tratar_emails

from ..empresa.empresa import Empresa
from ..mandato_cipa.mandato_configs.mandato_config_unidade import \
    MandatoConfigUnidade
from ..unidade.unidade import Unidade
from .auth import filter_token_required
from .forms import FormCentralUnidades
from .utils import filter_emails_by_domain, get_allowed_domains

_central_avisos = Blueprint(
    name="central_avisos",
    import_name=__name__,
    url_prefix="/central-avisos",
    template_folder="templates",
    cli_group="central-avisos",
)


@_central_avisos.route("/unidades", methods=["GET", "POST"])
@filter_token_required
def unidades(token: str, token_data: dict, *args, **kwargs):
    # NOTE: token data comes from @filter_token_required
    ids_empresas: list[int] = token_data.get("empresas")  # type: ignore

    # NOTE: apenas uma empresa por token por enquanto
    empresa: Empresa = Empresa.query.get(ids_empresas[0])

    if not empresa:
        return abort(404)

    domains = get_allowed_domains(id_empresas=ids_empresas)

    if not domains:
        flash(
            "Ainda não temos nenhum domínio de E-mail registrado para sua Empresa. \
            Por favor entre em contato com o Suporte SOC da GRS Núcleo \
            e solicite a autorização do domínio de sua Empresa para poder \
            configurar seus avisos aqui.",
            "alert-info",
        )
        return abort(404)

    form: FormCentralUnidades = FormCentralUnidades()
    form.load_choices(id_empresas=ids_empresas)

    if form.validate_on_submit():
        form_data = get_data_from_form(form.data)

        ids_unidades: list[int] = form_data.get("id_unidades")  # type: ignore

        emails = __get_emails(form_data=form_data, allowed_domains=domains)

        if not emails:
            flash("Dados enviados com Sucesso!", "alert-success")
            return redirect(url_for("central_avisos.unidades", token=token))

        for id_un in ids_unidades:
            try:
                __update_unidade(
                    id_unidade=id_un,
                    conv_exames=emails.get("conv_exames_emails"),
                    exames_rel=emails.get("exames_realizados_emails"),
                    absenteimso=emails.get("absenteismo_emails"),
                    cipa=emails.get("mandatos_cipa_emails")
                )
            except (SQLAlchemyError, DatabaseError) as e:
                db.session.rollback()  # type: ignore
                flash("Erro interno", "alert-danger")
                app.logger.error(str(e))

                return redirect(url_for("central_avisos.unidades", token=token))

        flash("Dados enviados com Sucesso!", "alert-success")
        return redirect(url_for("central_avisos.unidades", token=token))

    return render_template(
        "central_avisos/unidades.html",
        form=form,
        form_title="Central de Avisos Connect",
        form_sub_title=f"Unidades da Empresa: {empresa.razao_social}",
    )


def __get_emails(form_data: dict[str, str], allowed_domains: str):
    field_list = [
        "conv_exames_emails",
        "exames_realizados_emails",
        "absenteismo_emails",
        "mandatos_cipa_emails",
    ]

    emails_tratados: dict[str, str] = {}
    for key in field_list:
        email = form_data.get(key)

        if not email:
            continue

        email = tratar_emails(email_str=email)
        email = filter_emails_by_domain(email_str=email, allowed_domains=allowed_domains)

        if email:
            emails_tratados[key] = email

    return emails_tratados


def __update_unidade(
    id_unidade: int,
    conv_exames: str | None = None,
    exames_rel: str | None = None,
    absenteimso: str | None = None,
    cipa: str | None = None,
    sep: str = ";"
):
    unidade: Unidade = Unidade.query.get(id_unidade)

    # colunas direto na tabela de Unidade
    attribs = {
        "conv_exames_emails": conv_exames,
        "exames_realizados_emails": exames_rel,
        "absenteismo_emails": absenteimso,
    }

    for attr_name, new_email in attribs.items():
        curr_email = getattr(unidade, attr_name)

        if not new_email:
            continue

        if not curr_email:
            setattr(unidade, attr_name, new_email)
            continue

        new_email = curr_email + sep + new_email
        setattr(unidade, attr_name, new_email)

    db.session.commit()  # type: ignore

    # colunas em tabelas de configuracao
    __update_cipa(id_unidade=id_unidade, emails=cipa)

    return None


def __update_cipa(id_unidade: int, emails: str | None = None, sep: str = ";"):
    if not emails:
        return None

    conf: MandatoConfigUnidade = MandatoConfigUnidade.query.filter_by(
        id_unidade=id_unidade
    ).first()

    if not conf.emails:
        conf.emails = emails
    else:
        conf.emails = conf.emails + sep + emails

    db.session.commit()  # type: ignore
    return None
