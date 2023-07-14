import random

from click.testing import CliRunner

from src.main.central_avisos.commands import gerar_tokens
from src.main.central_avisos.utils import filter_emails_by_domain

from .utils import random_email_list


def test_command_gerar_tokens(runner: CliRunner):
    args_list = ['--id-empresa', 1]

    res = runner.invoke(gerar_tokens, args=args_list)

    assert res.exit_code == 0
    assert res.exception is None


def test_filter_emails_by_domain():
    domain_choices = ["empresa1.com", "empresa2.com"]
    domains = "empresa1.com;empresa2.com"

    rand_emails = random_email_list().replace(',', ';').split(';')

    # add some allowed emails
    num_allowed = random.randint(1, len(rand_emails))
    for i in range(num_allowed):
        rand_emails.append(f'allowed_email@{random.choice(domain_choices)}')

    random.shuffle(rand_emails)

    allowed_emails = filter_emails_by_domain(
        email_str=';'.join(rand_emails),
        allowed_domains=domains
    )

    allowed_emails_ls = allowed_emails.split(';')

    assert num_allowed == len(allowed_emails_ls)

    for em_addr in allowed_emails_ls:
        dom = em_addr.split('@')[-1]
        assert dom in domains
