import mimetypes
import os
import smtplib
import time
from email.message import EmailMessage
from email.utils import make_msgid

import jinja2
from flask_mail import Attachment

from src import app, database


class EmailConnect(database.Model):
    '''
    Tabela para registrar envio dos relatorios criados pelo sistema \
    (ConvExames, Absenteismo, ExamesRealizados etc)
    '''
    __tablename__ = 'EmailConnect'

    id = database.Column(database.Integer, primary_key=True)
    email_to = database.Column(database.String(500), nullable=False)
    email_cc = database.Column(database.String(500))
    email_bcc = database.Column(database.String(500))
    email_subject = database.Column(database.String(500))
    attachments = database.Column(database.String(500)) # attachment names
    status = database.Column(database.Boolean, nullable=False, default=True) # sent or error
    df_len = database.Column(database.Integer) # length of dataframe, if any
    ped_proc = database.Column(database.Integer) # id pedido_proc
    error = database.Column(database.String(255))
    obs = database.Column(database.String(255))
    email_date = database.Column(database.DateTime, nullable=False)

    # CONFIGS EMAIL------------------------------------------------------------------
    ASSINATURA_BOT: dict[str, str] = {
        'img_path': os.path.join(
            app.static_folder,
            'connect',
            'ass_bot.png'
        ),
        'cid_placeholder': 'AssEmail'
    }
    ASSINATURA_PATH: str = os.path.join(app.static_folder, 'connect', 'ass_bot.png')
    EMAIL_TEMPLATES: str = 'src/email_templates/'

    def __repr__(self) -> str:
        return f'<{self.id}> {self.email_subject} - {self.email_date}'


    @classmethod
    def send_email(
        self,
        to_addr: list[str],
        message_subject: str,
        message_body: str,
        sender_name: str = 'GRS+Connect Bot',
        message_preamble: str | None = None,
        message_imgs: list[dict[str, str]] | None = None,
        cc_addr: list[str] | None = None,
        bcc_addr: list[str] | None = None,
        reply_to: list[str] | None = None,
        message_attachments: list[str] | None = None,
        send_attempts: int = 3,
        attempt_delay: int = 30
    ) -> dict[str, any]:
        """Envia email em plaintext ou html. Aceita imagens inline (HTML) e anexos.

        Args:
            sender_name (str): nome do remetente
            message_body (str): corpo do email
            message_preamble (str | None, optional): preambulo do email . Defaults to None.
            message_attachments (list[str] | None, optional): lista de anexos. Defaults to None.
            send_attempts (int, optional): numero de tentativas ao enviar o email. Defaults to 3.
            attempt_delay (int, optional): tempo de espera (segundos) entre cada tentativa. Defaults to 30.
            
            message_imgs (list[dict[str, str]] | None, optional): imagens para inserir no corpo do Email se for HTML. \
            Deve seguir o modelo lista de dicionarios.

            Exemplo:

            [{'img_path': caminho_imagem, 'cid_placeholder': placeholder_para_cid}, \
            {'img_path': caminho_imagem, 'cid_placeholder': placeholder_para_cid}]

        Returns:
            dict[str, any]: {
                sent: int 1 | 0,
                error: str | None
            }
        """
        message = EmailMessage()
        from_addr: str = app.config['MAIL_DEFAULT_SENDER']
        email_password: str = app.config['MAIL_PASSWORD']
        mail_port: int = app.config['MAIL_PORT']
        mail_server: str = app.config['MAIL_SERVER']

        # HEADERS
        message["From"] = f"{sender_name} <{from_addr}>"
        message["To"] = ','.join(to_addr)
        message["Subject"] = message_subject

        if cc_addr:
            message['Cc'] = ','.join(cc_addr)
            to_addr.extend(cc_addr)

        if bcc_addr:
            message["Bcc"] = ','.join(bcc_addr)
            to_addr.extend(bcc_addr)

        if reply_to:
            message["Reply-To"] = ','.join(reply_to)

        if message_preamble: # nao funciona nos email clientes q sao mime aware
            message.preamble = message_preamble


        # CORPO PLAINTEXT
        message.set_content(message_body) # corpo padrao (plain text)


        # CORPO HTML + IMAGENS
        if message_imgs:
            # criar CIDs
            for dic in message_imgs:
                new_cid = make_msgid()
                dic['new_cid'] = new_cid
                message_body = message_body.replace(dic['cid_placeholder'], new_cid[1:-1])

            # incluir corpo email
            message.add_alternative(message_body, subtype='html')

            for dic in message_imgs:
                with open(dic['img_path'], 'rb') as img:
                    # know the Content-Type of the image
                    maintype, subtype = mimetypes.guess_type(img.name)[0].split('/')
                    # attach it
                    message.get_payload()[1].add_related(
                        img.read(),
                        maintype=maintype,
                        subtype=subtype,
                        cid=dic['new_cid'] # cid com <>
                    )
        else:
            # corpo sem imagem
            message.add_alternative(message_body, subtype='html')


        # ANEXOS
        if message_attachments:
            for anexo in message_attachments:
                # nome do anexo nao permite caracteres especiais
                with open(anexo, 'rb') as arqv:
                    maintype, subtype = mimetypes.guess_type(arqv.name)[0].split('/')
                    message.add_attachment(
                        arqv.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=os.path.basename(arqv.name)
                    )


        # ENVIAR
        infos = {
            "sent": None,
            "error": None
        }
        for tentativa in range(send_attempts):
            try:
                # using Office365
                with smtplib.SMTP(host=mail_server, port=mail_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(user=from_addr, password=email_password)
                    server.send_message(
                        from_addr=from_addr,
                        to_addrs=to_addr,
                        msg=message
                    )

                infos["sent"] = 1
                return infos

            except smtplib.SMTPException as err:
                infos["error"] = type(err).__name__
                infos["sent"] = 0
                
                if tentativa + 1 < send_attempts:
                    time.sleep(attempt_delay)
                
                continue
        return infos


    @staticmethod
    def create_email_body(
        email_template_path: str,
        replacements: dict[str, str] | None = None
    ) -> str:
        """
        Args:
            email_template_path (str): caminho para o HTML do corpo do email
            replacements (dict[str, str]): Dicionario no formato {NOME_DO_PLACEHOLDER: substituicao}

        Returns:
            str: corpo do email com placeholders substituidos
        """
        with open(file=email_template_path, mode='r', encoding='utf-8') as f:
            email_body: str = f.read()

        if replacements:
            for key, value in replacements.items():
                email_body = email_body.replace(key, value)

        return email_body

    @staticmethod
    def render_email_body(template_path: str, cid_assinatura: str | None = None, **kwargs):
        '''
            Renderiza corpo de um email com Jinja2 para HTML contendo as variaveis passadas.

            Args:
                cid_assinatura (str, optional): cid da assinatura do Bot (.png).
                Obs: já remove os simbolos <> se houver.
        '''
        template_loader = jinja2.FileSystemLoader('./')
        template_env = jinja2.Environment(loader=template_loader)

        template = template_env.get_template(name=template_path)

        if cid_assinatura:
            for symbol in('<', '>'):
                cid_assinatura = cid_assinatura.replace(symbol, '')

            kwargs['cid_assinatura'] = cid_assinatura

        return template.render(**kwargs)

    @classmethod
    def get_assinatura_attachment(self):
        '''
            Cria objeto FlaskMail.Attachment para a Assinatura de email do Bot.
            Gera CID automaticamente para a assinatura. Atributo: obj.cid
        '''
        CID = make_msgid()
        ass = Attachment(
            filename=self.ASSINATURA_PATH,
            content_type='image/png',
            data=app.open_resource(self.ASSINATURA_PATH).read(),
            disposition='inline',
            headers=[['Content-ID', CID]]
        )
        ass.cid = CID
        return ass

