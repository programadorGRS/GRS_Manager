import mimetypes
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid

from manager import database
from manager.utils import get_json_configs


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
    DEFAULT_SENDER: str = get_json_configs('configs/config_email.json')['MAIL_USERNAME']
    EMAIL_PASSWORD: str = get_json_configs('configs/config_email.json')['MAIL_PASSWORD'] # gmail
    OUTLOOK_PASSWORD: str = get_json_configs('configs/config_email.json')['OUTLOOK_PASSWORD'] # office365
    ASSINATURA_BOT: dict[str, str] = {
        'img_path': 'manager/static/images/ass_bot2.png',
        'cid_placeholder': 'AssEmail'
    }
    EMAIL_TEMPLATES: str = 'manager/email_templates/'

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
        use_outlook: bool = False
    ) -> None:
        """Envia email em plaintext ou html. Aceita imagens inline (HTML) e anexos.

        Args:
            sender_name (str): nome do remetente
            message_body (str): corpo do email
            message_preamble (str | None, optional): preambulo do email . Defaults to None.
            message_attachments (list[str] | None, optional): lista de anexos. Defaults to None.
            
            message_imgs (list[dict[str, str]] | None, optional): imagens para inserir no corpo do Email se for HTML. \
            Deve seguir o modelo lista de dicionarios.

            Exemplo:

            [{'img_path': caminho_imagem, 'cid_placeholder': placeholder_para_cid}, \
            {'img_path': caminho_imagem, 'cid_placeholder': placeholder_para_cid}]
        """
        message = EmailMessage()
        from_addr = self.DEFAULT_SENDER
        email_password = self.EMAIL_PASSWORD


        # HEADERS
        message["From"] = f'{sender_name} <{from_addr}>'
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
                        maintype=maintype, # main e subtypes generalistas
                        subtype=subtype,
                        filename=arqv.name.split(sep='/')[-1]
                    )


        # ENVIAR
        if use_outlook:
            # using Office365
            with smtplib.SMTP(host="smtp.office365.com", port=587) as server:
                server.ehlo()
                server.starttls()
                server.login(user=from_addr, password=self.OUTLOOK_PASSWORD)
                server.send_message(
                    from_addr=from_addr,
                    to_addrs=to_addr,
                    msg=message
                )
        else:
            # using Gmail
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host="smtp.gmail.com", port=465, context=context) as server:
                server.login(user=from_addr, password=email_password)
                server.send_message(
                    from_addr=from_addr,
                    to_addrs=to_addr,
                    msg=message
                )
        return None


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


