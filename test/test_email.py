from src.email_connect import EmailConnect

def test_render_email_body():
    body = EmailConnect.render_email_body(
        template_path='src/email_templates/erros_mandatos_cipa.html',
        df_resumo_erros='teste123'
    )

    assert 'teste123' in body

