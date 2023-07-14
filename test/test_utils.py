import os

from src import UPLOAD_FOLDER
from src.utils import tratar_emails, zipar_arquivos

from .utils import random_email_list


def test_zipar_arquivos():
    files = []
    for i in range(3):
        file_name = os.path.join(UPLOAD_FOLDER, f"file_{i}.txt")
        with open(file_name, mode="w") as f:
            f.write(f"Testing wrinting in file number {i}")

        files.append(file_name)

    zipped_name = "zipped_file.zip"
    zipped_path = zipar_arquivos(
        caminho_pasta_zip=os.path.join(UPLOAD_FOLDER, "zipped_file.zip"),
        caminhos_arquivos=files,
    )

    assert zipped_name in os.listdir(UPLOAD_FOLDER)
    assert zipped_path == os.path.join(UPLOAD_FOLDER, zipped_name)


def test_tratar_emails():
    rand_emails = random_email_list()
    proccessed_emails = tratar_emails(email_str=rand_emails)

    assert ' ' not in proccessed_emails
    assert ',' not in proccessed_emails

    for email in proccessed_emails.split(";"):
        assert isinstance(email, str)
        assert email
