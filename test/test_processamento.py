from click.testing import CliRunner

from src.main.processamento.commands import cancelar_tarefas


def test_cancelar_tarefas(runner: CliRunner):
    res = runner.invoke(cancelar_tarefas)

    assert res.exit_code == 0
    assert res.exception is None
