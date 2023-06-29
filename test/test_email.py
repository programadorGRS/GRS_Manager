from src.email_connect import EmailConnect


def test_render_email_body():
    vencimentos = ['teste123', 'teste456']
    body = EmailConnect.render_email_body(
        template_path='src/email_templates/erros_mandatos_cipa.html',
        vencimentos=vencimentos
    )

    for i in vencimentos:
        assert i in body

