import smtplib, ssl
from email.message import EmailMessage
import mimetypes


def enviar_email(
    remetente: str,
    senha_email: str,
    email_dest: list[str],
    corpo_email: str,
    assunto: str,
    dic_imgs: dict[str] = None,
    email_cc: list[str] = None,
    anexos: list[str] = None,
) -> None:
    '''
    Envia um email para o endereço especificado, com ou sem anexo

    Aceita imagens inline se o corpo for html

    Referencias:
    - Imagens: https://stackoverflow.com/a/49098251
    - Anexos: https://stackoverflow.com/a/52410242
    '''
    # criar objeto EmailMessage
    message = EmailMessage()
    # HEADERS
    message["From"] = f'GRS Connect Bot <{remetente}>'
    message["Subject"] = assunto
    message["To"] = ','.join(email_dest)  # lista para string
    # message["Bcc"] = remetente
    if email_cc:
        message['Cc'] = ','.join(email_cc)
        enviar_para = email_dest + email_cc
    else:
        enviar_para = email_dest
    # CORPO DO EMAIL
    message.set_content(corpo_email)  # corpo padrao (plain text)
    message.add_alternative(corpo_email, subtype='html')
    # IMAGENS
    if dic_imgs:
        # corpo alternativo do email em html
        message.add_alternative(corpo_email, subtype='html')
        for nome_imagem, cid_imagem in dic_imgs.items():
            # abrir imagem e anexar ao corpo do email
            with open(nome_imagem, 'rb') as img:
                # know the Content-Type of the image
                maintype, subtype = mimetypes.guess_type(img.name)[0].split('/')
                # attach it
                message.get_payload()[1].add_related(
                    img.read(),
                    maintype=maintype,
                    subtype=subtype,
                    cid=cid_imagem # cid da img com <>
                )
    # ANEXOS
    # se houver anexos: iterar sobre todos e anexar ao email
    if anexos:
        for anexo in anexos:
            # nome do anexo nao permite caracteres especiais
            # deve estar na mesma pasta do script
            with open(anexo, 'rb') as arqv:
                # ler conteudo do arqv
                conteudo = arqv.read()
                # anexar
                message.add_attachment(
                    conteudo,
                    maintype='application', # main e subtypes generalistas
                    subtype='octet-stream',
                    filename=arqv.name.split(sep='/')[-1] # nome do arqv aberto
                )
    # ENVIAR
    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(remetente, senha_email)
        server.sendmail(
            from_addr=remetente,
            to_addrs=enviar_para,
            msg=message.as_string()
        ) # enviar msg como string
    return None


def enviar_report(subj: str, send_to: list[str], body: str=''):
    from datetime import datetime
    from pytz import timezone

    from modules.exporta_dados import get_json_configs
    # enviar report
    remetente = get_json_configs('configs/config_email.json')['MAIL_USERNAME']
    senha_email = get_json_configs('configs/config_email.json')['MAIL_PASSWORD']
    tz = timezone("America/Sao_Paulo")
    enviar_email(
        remetente=remetente,
        senha_email=senha_email,
        assunto=f"{subj} - {datetime.now(tz=tz).strftime('%d-%m-%Y %H:%M:%S')}",
        corpo_email=body,
        email_dest=send_to
    )


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

