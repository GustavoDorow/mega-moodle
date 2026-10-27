import sqlite3
import sys
from pathlib import Path

from mega_moodle.controllers.cadastro_controller import CadastroController
from mega_moodle.daos.banco_dados import BancoDados
from mega_moodle.daos.disciplina_dao import DisciplinaDAO
from mega_moodle.daos.disponibilidade_dao import DisponibilidadeDAO
from mega_moodle.daos.estudante_dao import EstudanteDAO


def criar_controller(caminho_banco: str | Path = "megamoodle.db") -> CadastroController:
    """Monta as dependências; as telas recebem os controllers já prontos."""
    banco = BancoDados(caminho_banco)
    banco.inicializar()
    return CadastroController(
        DisciplinaDAO(banco), EstudanteDAO(banco), DisponibilidadeDAO(banco)
    )


def main() -> None:
    from PySide6.QtWidgets import QApplication, QMessageBox

    from mega_moodle.views.gui import MegaMoodleWindow

    app = QApplication(sys.argv)
    try:
        controller = criar_controller()
    except sqlite3.Error:
        QMessageBox.critical(None, "Mega Moodle", "Não foi possível abrir o banco de dados.")
        raise SystemExit(1)

    janela = MegaMoodleWindow(controller)
    janela.show()
    raise SystemExit(app.exec())


def main_cli() -> None:
    from mega_moodle.views.cli import executar

    try:
        controller = criar_controller()
    except sqlite3.Error:
        print("Não foi possível abrir o banco de dados.")
        raise SystemExit(1)
    executar(controller)
