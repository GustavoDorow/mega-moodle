import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTime
from PySide6.QtWidgets import QApplication

from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.main import criar_controller
from mega_moodle.views.gui import MegaMoodleWindow


class TelasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "teste.db"
        self.cadastro = criar_controller(self.caminho)
        self.janela = self.abrir_janela(self.cadastro)

    def abrir_janela(self, cadastro):
        janela = MegaMoodleWindow(cadastro)
        self.addCleanup(janela.close)
        return janela

    def abrir_perfil(self, janela, perfil):
        janela.nome_usuario.setText("Usuário de teste")
        janela.identificacao.setValue(10)
        janela.perfil.setCurrentText(perfil)
        janela._cadastrar_usuario()

    def test_cadastro_disciplina_persiste_e_reaparece_na_tela(self):
        self.abrir_perfil(self.janela, "Administrador")
        self.janela.codigo.setText("INE5608")
        self.janela.nome_disciplina.setText("APS")
        self.janela._cadastrar_disciplina()
        self.assertEqual(self.janela.lista.count(), 1)
        self.assertEqual(self.janela.codigo.text(), "")

        reaberta = self.abrir_janela(criar_controller(self.caminho))
        self.abrir_perfil(reaberta, "Administrador")
        self.assertIn("INE5608", reaberta.lista.item(0).text())

    def test_disponibilidade_persiste_e_falha_preserva_a_tela(self):
        self.abrir_perfil(self.janela, "Estudante")
        self.janela._registrar_disponibilidade()
        self.assertEqual(self.janela.lista.count(), 1)

        self.janela.inicio.setTime(QTime(9, 0))
        with patch.object(
            self.cadastro.disponibilidade_dao, "registrar", return_value=StatusPersistencia.ERRO
        ), patch("mega_moodle.views.gui.QMessageBox.warning") as aviso:
            self.janela._registrar_disponibilidade()
            aviso.assert_called_once()
        self.assertEqual(self.janela.lista.count(), 1)
        self.assertEqual(self.janela.inicio.time(), QTime(9, 0))

        reaberta = self.abrir_janela(criar_controller(self.caminho))
        self.abrir_perfil(reaberta, "Estudante")
        self.assertEqual(reaberta.lista.count(), 1)
        self.assertIn("08:00 às 12:00", reaberta.lista.item(0).text())
