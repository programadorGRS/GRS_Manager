# NOTE: this module is to be completely replaced by the new one (EmailConnect).
# Delete after full replacement has been finished


def corpo_email_padrao(
    tabela: str,
    nome_usuario: str,
    email_usuario: str,
    telefone_usuario: str = None,
    celular_usuario: str = None,
    observacoes: str = 'Sinalizar se o funcionário não compareceu.'
) -> str:
    '''Cria corpo do Email'''

    if telefone_usuario:
        telefone_usuario = f'({telefone_usuario[:2]}) {telefone_usuario[2:6]}-{telefone_usuario[6:]}'
    if celular_usuario:
        celular_usuario = f'({celular_usuario[:2]}) {celular_usuario[2:7]}-{celular_usuario[7:]}'
    
    body = f'''
        <html>
            <head>
                <style type="text/css">
                    table {{border: none; border-collapse: collapse; border-spacing: 0; color: black; font-size: 11px; font-family:Arial, Helvetica, sans-serif; table-layout: fixed;}}
                    thead {{border-bottom: 1px solid black; vertical-align: bottom;}}
                    th, td {{padding: 2px; border: 1px solid lightgray;}}
                    tr, th, td {{text-align: right; vertical-align: middle; padding: 0.5em 0.5em; line-height: normal; white-space: normal; max-width: none;border: none;}}
                    th {{font-weight: bold;}}
                    tbody tr:nth-child(odd) {{background: #f5f5f5;}}
                    tbody tr:hover {{background: rgba(66, 165, 245, 0.2);}}
                    p {{font-size: 14px; font-family:Arial, Helvetica, sans-serif; margin: 0;}}
                </style>
            </head>
            <body style="font-size: 14px; font-family:Arial, Helvetica, sans-serif; padding:0;">
                <p>Olá Prestador &#128516;</p>
                <p>Solicitamos o envio dos ASOs abaixo &#128071;</p>
                <br>
                <p><b>Obs: {observacoes}</b></p>
                <br>
                <p>{tabela.to_html(index=False)}</p>
                <br>
                <p><b>&#127973; Liberação GRS - {nome_usuario}</b></p>
                <p><b>&#128231; {email_usuario}</b></p>
                <p><b>&#9742;&#65039; {telefone_usuario}</b></p>
                <p><b>&#128241; {celular_usuario}</b></p>
                <br>
                <img src="cid:AssEmail" alt="GRS Manager Bot" width="536px" height="123px">
            </body>
        </html>'''
    return body


def corpo_email_otp(
    nome_dest: str,
    username_dest: str,
    current_datetime: str,
    otp_usuario: str,
) -> str:
    '''Cria corpo do Email de validacao OTP'''
    body = f'''
        <html>
            <body style="font-size: 14px; font-family:Arial, Helvetica, sans-serif;">
                <p>Olá, {nome_dest}.</p>
                <p>Houve uma tentativa de login no seu Usuário <b>{username_dest}</b> em: <b>{current_datetime}</b></p>
                <p>A sua Chave temporária de acesso é: <b>{otp_usuario}</b></p>
                <p>Se não foi você, avise ao Administrador para resetar o seu acesso.</p>
                <br>
                <img src="cid:AssEmail" alt="GRS Manager Bot" width="536px" height="123px">
            </body>
        </html>'''
    return body

