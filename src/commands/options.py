import click

DATE_FORMAT = '%d-%m-%Y'

opt_data_fim = click.Option(
    param_decls=['-di', '--data-inicio'],
    default=None,
    type=click.DateTime(formats=[DATE_FORMAT]),
)

opt_data_inicio = click.Option(
    param_decls=['-df', '--data-fim'],
    default=None,
    type=click.DateTime(formats=[DATE_FORMAT]),
)

opt_id_empresa = click.Option(
    param_decls=['-id', '--id-empresa'],
    default=None,
    type=int
)

