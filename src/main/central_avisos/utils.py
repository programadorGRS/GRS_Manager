from src.extensions import database
from src.utils import tratar_emails

from ..empresa.empresa import Empresa
from ..unidade.unidade import Unidade


# fields from the form that must contain the emails. Those field names also \
#  match the column names in the db tables: Empresa, Unidade
EMAIL_FIELDS = [
    "conv_exames_emails",
    "exames_realizados_emails",
    "absenteismo_emails",
    "mandatos_cipa_emails",
]


def get_allowed_domains(id_empresas: list[int], sep: str = ';') -> str:
    query: list[Empresa] = (
        database.session.query(Empresa)
        .filter(Empresa.id_empresa.in_(id_empresas))
        .all()
    )

    domains = [emp.dominios_email for emp in query if emp.dominios_email]
    # remove duplicates from list
    domains = list(dict.fromkeys(domains))
    return sep.join(domains)


def tratar_emails_from_form_data(form_data: dict[str, str], allowed_domains: str):
    for key, val in form_data.items():
        if "_email" in key:
            email_tratado = tratar_emails(email_str=val)
            email_tratado = filter_emails_by_domain(
                email_str=email_tratado, allowed_domains=allowed_domains
            )
            form_data[key] = email_tratado
    return form_data


def filter_emails_by_domain(
    email_str: str, allowed_domains: str, sep: str = ";"
) -> str:
    email_ls = email_str.split(sep=sep)
    allowed_emails = []

    for em_addr in email_ls:
        domain = em_addr.split("@")[-1]
        if domain in allowed_domains:
            allowed_emails.append(em_addr)

    return sep.join(allowed_emails)


def update_emails_unidades(form_data: dict, email_fields: list[str]):
    ID_UNIDADES: list[int] = form_data["id_unidades"]

    query_unidades: list[Unidade] = (
        database.session.query(Unidade)
        .filter(Unidade.id_unidade.in_(ID_UNIDADES))
        .all()
    )

    for unidade in query_unidades:
        # update email fields in place
        __update_email_fields_from_dict(
            obj=unidade, field_names=email_fields, data=form_data
        )

        database.session.commit()
    return None


def __update_email_fields_from_dict(
    obj: object, field_names: list[str], data: dict[str, str], sep: str = ";"
):
    for field in field_names:
        curr_em: str = getattr(obj, field)
        new_em: str = data.get(field, "")

        if not new_em:
            continue

        if not curr_em:
            setattr(obj, field, new_em)
            continue

        # join new email with current email, remove duplicates and update the column
        new_em = curr_em + sep + new_em
        new_em_ls = new_em.split(sep=sep)
        new_em_ls = list(dict.fromkeys(new_em_ls))
        new_em = sep.join(new_em_ls)

        setattr(obj, field, new_em)

    return None
