import click

DATE_FORMAT = '%d-%m-%Y'

data_inicio = click.Option(
    default=None,
    param_decls=['-dti', '--data-inicio'],
    type=click.DateTime(formats=[DATE_FORMAT]),
    show_default=True,
    help='Data Inicio. Format: "dd-mm-yyyy". Defaults to current date - 2 years'
)

data_fim = click.Option(
    param_decls=['-dtf', '--data-fim'],
    default=None,
    type=click.DateTime(formats=[DATE_FORMAT]),
    show_default=True,
    help='Data Fim. Format: "dd-mm-yyyy". Defaults to current date + 1 month'
)

dias_vencimento = click.Option(
    param_decls=['-dias', '--dias-vencimento'],
    default=90,
    type=int,
    show_default=False,
    help='Dias para calcular alerta de vencimento dos mandatos. Defaults to 90.'
)

id_empresa = click.Option(
    param_decls=['-id', '--id-empresa'],
    default=None,
    type=int,
    show_default=False,
    help='Id da Empresa para carregar os Mandatos. Defaults to all.'
)

cod_unidade = click.Option(
    param_decls=['-cod', '--cod-unidade'],
    default=None,
    type=str,
    show_default=False,
    help='Cod da Unidade. Defaults to all.'
)

ativo_multiple = click.Option(
    param_decls=['-atv', '--ativo'],
    default=(0, 1),
    multiple=True,
    type=int,
    show_default=True,
    help='Status do mandato. Aceita multiplos. Defaults to all.'
)

ativo_single = click.Option(
    param_decls=['-atv', '--ativo'],
    default=1,
    type=int,
    show_default=True,
    help='Status do mandato. Defaults to 1.'
)


modo = click.Option(
    param_decls=['-m', '--modo'],
    default=1,
    type=int,
    show_default=False,
    help='Modo de operação. 1: Empresa, 2: Unidade. Defaults to 1.'
)

