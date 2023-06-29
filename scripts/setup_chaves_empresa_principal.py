if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')
    import os

    from src import app
    from src.config import set_app_config
    from src.extensions import database
    from src.main.empresa_principal.empresa_principal import EmpresaPrincipal

    name = os.name
    print('Usando configuração: ', end='')
    if name == 'posix':
        print('prod')
        set_app_config(app=app, conf='prod')
    else:
        print('dev')
        set_app_config(app=app, conf='dev')

    keys = (
        (423, 'grs.json'),
        (638911, 'syngenta.json')
    )

    with app.app_context():
        for cod, filename in keys:
            print(f'{cod}: {filename}')
            empresa: EmpresaPrincipal = EmpresaPrincipal.query.get(cod)
            empresa.chaves_exporta_dados = filename
            database.session.commit()

    print('Done!')

