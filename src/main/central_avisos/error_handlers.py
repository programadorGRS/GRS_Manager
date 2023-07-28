from flask import render_template


def error_404_central(error):
    return (
        render_template(
            "error_handlers/erro.html",
            cod_erro=404,
            titulo_erro="Essa página não existe",
        ),
        404,
    )
