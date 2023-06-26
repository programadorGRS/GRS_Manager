import os

from src import UPLOAD_FOLDER
from src.utils import zipar_arquivos


def test_zipar_arquivos():
    files = []
    for i in range(3):
        file_name = os.path.join(UPLOAD_FOLDER, f'file_{i}.txt')
        with open(file_name, mode='w') as f:
            f.write(f'Testing wrinting in file number {i}')

        files.append(file_name)

    zipped_name = 'zipped_file.zip'
    zipped = zipar_arquivos(
        caminho_pasta_zip=os.path.join(UPLOAD_FOLDER, 'zipped_file.zip'),
        caminhos_arquivos=files
    )

    assert zipped_name in os.listdir(UPLOAD_FOLDER)

