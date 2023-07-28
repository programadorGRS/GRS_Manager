from flask import Blueprint, abort, flash, redirect, render_template, url_for

from src.utils import get_data_from_form

from ..empresa.empresa import Empresa
from .auth import filter_token_required
from .forms import FormCentralUnidades
from .utils import (EMAIL_FIELDS, get_allowed_domains,
                    tratar_emails_from_form_data, update_emails_unidades)


# TODO: adicionar botao para gerar link de acesso (url + token) nos forms de Empresa
# TODO: criar testes para as funcoes desse modulo


central_avisos = Blueprint(
    name="central_avisos",
    import_name=__name__,
    url_prefix="/central-avisos",
    template_folder="templates",
    cli_group="central-avisos",
)


@central_avisos.route("/unidades", methods=["GET", "POST"])
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

        form_data = tratar_emails_from_form_data(
            form_data=form_data, allowed_domains=domains
        )

        update_emails_unidades(form_data=form_data, email_fields=EMAIL_FIELDS)

        flash("Dados enviados com Sucesso!", "alert-success")
        return redirect(url_for("central_avisos.unidades", token=token))

    return render_template(
        "central_avisos/unidades.html",
        form=form,
        form_title="Central de Avisos Connect",
        form_sub_title=f"Unidades da Empresa: {empresa.razao_social}",
    )
