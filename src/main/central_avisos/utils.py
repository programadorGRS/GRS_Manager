from src.extensions import database as db

from ..empresa.empresa import Empresa


def get_allowed_domains(id_empresas: list[int], sep: str = ";") -> str:
    query: list[Empresa] = (
        db.session.query(Empresa).filter(Empresa.id_empresa.in_(id_empresas)).all()  # type: ignore
    )

    domains = [emp.dominios_email for emp in query if emp.dominios_email]
    # remove duplicates from list
    domains = list(dict.fromkeys(domains))
    return sep.join(domains)


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
